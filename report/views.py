from django.shortcuts import render, redirect, get_object_or_404
from .models import *
import pandas as pd
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q, F
import math
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re


def index(request):
    # Fetch all data from the database
    all_data = UserData.objects.all()
    
    # Get unique country names and convert to lowercase
    countries = set(data.country for data in all_data)
    states = set(data.state for data in all_data)
    cities = set(data.city for data in all_data)
    
    if request.method == 'POST':
        type_data = request.POST.get('type') or None
        country = request.POST.get('countries') or None
        state = request.POST.get('States') or None
        city = request.POST.get('cities') or None
        has_supported = request.POST.get('has_supported') or None
        services = request.POST.getlist('services')
        weekly_attendees = request.POST.get('weekly_attendees') or None
        reaches = request.POST.get('reaches') or None
        keyword = request.POST.get('keyword') or None
        search_type = request.POST.get('search_type') or None
        
        filtered_data = None
        
        if type_data and country and state:
        
            # Perform filtering based on selected options
            filtered_data = UserData.objects.all()
            
            if type_data and type_data != 'none_of_them':
                if type_data != 'all':
                    if type_data == 'church':
                        filtered_data = filtered_data.filter(is_church=True)
                    elif type_data == 'organization':
                        filtered_data = filtered_data.filter(is_organization=True)
                    elif type_data == 'influencer':
                        filtered_data = filtered_data.filter(is_influencer=True)
                    elif type_data == 'media':
                        filtered_data = filtered_data.filter(is_media=True)
                else:
                    filtered_data = filtered_data.filter(
                        Q(is_church=True) | Q(is_organization=True) | Q(is_influencer=True) | Q(is_media=True)
                    )
            
            if country and country != 'all':
                filtered_data = filtered_data.filter(country__iexact=country)
            else:
                filtered_data = filtered_data.filter(country__in=countries)
            
            if state and state != 'all':
                filtered_data = filtered_data.filter(state__iexact=state)
            else:
                filtered_data = filtered_data.filter(state__in=states)
            
            if city and city != 'all':
                filtered_data = filtered_data.filter(city__iexact=city)
            elif city and city == 'all':
                filtered_data = filtered_data.filter(city__in=cities)
            
            if has_supported and has_supported != 'all':
                filtered_data = filtered_data.filter(has_supported__contains=has_supported)
            elif has_supported and has_supported == 'all':
                filtered_data = filtered_data.filter(
                    Q(has_supported__contains='movieScreenings') | Q(has_supported__contains='meetings') | Q(has_supported__contains='events')
                )
            
            if services and 'all' not in services:
                query = Q()
                for service in services:
                    query |= Q(services__icontains=service)
                filtered_data = filtered_data.filter(query | Q(services__isnull=True))
            elif services and 'all' in services:
                filtered_data = filtered_data.filter(
                    Q(services__icontains='monday') | Q(services__icontains='tuesday') | Q(services__icontains='wednesday') | Q(services__icontains='thursday') | Q(services__icontains='friday') | Q(services__icontains='saturday') | Q(services__icontains='sunday')
                )
            
            if weekly_attendees:
                attendee_ranges = {
                    'less_than_300': (0, 300),
                    '301_to_1000': (301, 1000),
                    '1001_to_5000': (1001, 5000),
                    '5000_to_10000': (5000, 10000),
                    'over_10000': (10000, None)
                }
                attendees_range = attendee_ranges.get(weekly_attendees)
                if attendees_range:
                    filtered_data = filtered_data.filter(weekly_attendees__range=attendees_range)
            
            if reaches:
                reaches_ranges = {
                    'less_than_100k': (1, 100000),
                    '100k_to_500k': (100000, 500000),
                    '500k_to_1mil': (500000, 1000000),
                    'over_1mil': (1000000, None)
                }
                reaches_range = reaches_ranges.get(reaches)
                # Fetch follower counts from social media platforms and update the corresponding fields
                for data in filtered_data:
                    if data.instagram:
                        data.instagram_followers = get_followers_from_instagram(data.instagram)
                    else:
                        data.instagram_followers = 0
                        
                    if data.facebook:
                        data.facebook_followers = get_followers_from_facebook(data.facebook)
                    else:
                        data.facebook_followers = 0
                        
                    if data.ticktock:
                        data.ticktock_followers = get_followers_from_ticktock(data.ticktock)
                    else:
                        data.ticktock_followers = 0
                        
                    if data.twitter:
                        data.twitter_followers = get_followers_from_twitter(data.twitter)
                    else:
                        data.twitter_followers = 0
                        
                    if data.youtube:
                        data.youtube_followers = get_followers_from_youtube(data.youtube)
                    else:
                        data.youtube_followers = 0
                        
                    data.save()
                if reaches_range:
                    filtered_data = filtered_data.filter(
                        Q(instagram_followers__isnull=False) |
                        Q(facebook_followers__isnull=False) |
                        Q(ticktock_followers__isnull=False) |
                        Q(twitter_followers__isnull=False) |
                        Q(youtube_followers__isnull=False)
                    ).annotate(
                        total_followers=F('instagram_followers') + F('facebook_followers') +
                                        F('ticktock_followers') + F('twitter_followers') +
                                        F('youtube_followers')
                    ).filter(total_followers__range=reaches_range)
                
            
            if keyword:
                filtered_data = filtered_data.filter(notes__icontains=keyword)
            
        if not filtered_data:
            messages.info(request, 'No data found after filtering.')
                
        if search_type == "name":
            context = {
                'names': filtered_data,
                'countries': countries,
                'states': states,
                'cities': cities,
            }
            return render(request, 'home.html', context)
        else:
            context = {
                'filtered_data': filtered_data,
                'countries': countries,
                'states': states,
                'cities': cities,
            }
            return render(request, 'home.html', context)
    
    context = {
        'countries': countries,
        'states': states,
        'cities': cities,
    }
    
    return render(request, 'home.html', context)

def input_manually(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        street_address = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        organization_name = request.POST.get('organization_name')
        title = request.POST.get('title')
        website = request.POST.get('website')
        instagram = request.POST.get('instagram')
        facebook = request.POST.get('facebook')
        ticktock = request.POST.get('ticktock')
        twitter = request.POST.get('twitter')
        youtube = request.POST.get('youtube')
        description = request.POST.get('description')
        notes = request.POST.get('notes')
        type_d = request.POST.get('type')
        services = request.POST.getlist('services')
        weekly_attendees = request.POST.get('weekly_attendees')
        if not weekly_attendees:
            weekly_attendees = 0
        has_supported = request.POST.getlist('has_supported')
        if type_d == "church":
            obj = UserData.objects.create(first_name=first_name, last_name=last_name, email=email, phone=phone, street_address=street_address, city=city, state=state, country=country, organization_name=organization_name, title=title, website=website, instagram=instagram, facebook=facebook, ticktock=ticktock, twitter=twitter, youtube=youtube, description=description, notes=notes, is_church=True, services=', '.join(services), weekly_attendees=weekly_attendees, has_supported=', '.join(has_supported))
            obj.save()
        elif type_d == "organization":
            obj = UserData.objects.create(first_name=first_name, last_name=last_name, email=email, phone=phone, street_address=street_address, city=city, state=state, country=country, organization_name=organization_name, title=title, website=website, instagram=instagram, facebook=facebook, ticktock=ticktock, twitter=twitter, youtube=youtube, description=description, notes=notes, is_organization=True, services=', '.join(services), weekly_attendees=weekly_attendees, has_supported=', '.join(has_supported))
            obj.save()
        elif type_d == "influencer":
            obj = UserData.objects.create(first_name=first_name, last_name=last_name, email=email, phone=phone, street_address=street_address, city=city, state=state, country=country, organization_name=organization_name, title=title, website=website, instagram=instagram, facebook=facebook, ticktock=ticktock, twitter=twitter, youtube=youtube, description=description, notes=notes, is_influencer=True, services=', '.join(services), weekly_attendees=weekly_attendees, has_supported=', '.join(has_supported))
            obj.save()
        elif type_d == "media":
            obj = UserData.objects.create(first_name=first_name, last_name=last_name, email=email, phone=phone, street_address=street_address, city=city, state=state, country=country, organization_name=organization_name, title=title, website=website, instagram=instagram, facebook=facebook, ticktock=ticktock, twitter=twitter, youtube=youtube, description=description, notes=notes, is_media=True, services=', '.join(services), weekly_attendees=weekly_attendees, has_supported=', '.join(has_supported))
            obj.save()
        else:
            obj = UserData.objects.create(first_name=first_name, last_name=last_name, email=email, phone=phone, street_address=street_address, city=city, state=state, country=country, organization_name=organization_name, title=title, website=website, instagram=instagram, facebook=facebook, ticktock=ticktock, twitter=twitter, youtube=youtube, description=description, notes=notes, services=', '.join(services), weekly_attendees=weekly_attendees, has_supported=', '.join(has_supported))
            obj.save()
        messages.success(request, 'Data saved successfully!')
        return redirect('home')
        
    return render(request, 'input_manually.html')

def upload_excel_sheet(request):
    if request.method == 'POST' and request.FILES.get('csv_or_excel_file'):
        file = request.FILES['csv_or_excel_file']
        # Check the file extension
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            return HttpResponse('Invalid file format')
        
        # Convert column names to lowercase
        df.columns = df.columns.str.lower()

        # Define column name variations
        name_column_variations = ['first name', 'name']
        organization_name_variations = ['organization name', 'church name']

        # Iterate over rows and create Data objects
        for _, row in df.iterrows():
            is_church = row.get('church', '').lower() == 'yes'
            is_organization = row.get('organization', '').lower() == 'yes'
            is_influencer = row.get('influencer', '').lower() == 'yes'
            is_media = row.get('media', '').lower() == 'yes'
            
            # Check if 'weekly_attendees' value is NaN
            weekly_attendees = row.get('members')
            if isinstance(weekly_attendees, float) and math.isnan(weekly_attendees):
                weekly_attendees = 0
                
            # Replace all NaN values with ""
            row = row.fillna("")
            
            data = UserData(
                first_name=get_value_from_columns(row, name_column_variations),
                last_name=row.get('last name', ''),
                email=row.get('email', ''),
                phone=row.get('telephone', ''),
                street_address=row.get('street address', ''),
                city=row.get('city', ''),
                state=row.get('state', ''),
                country=row.get('country', ''),
                organization_name=get_value_from_columns(row, organization_name_variations),
                title=row.get('title', ''),
                website=row.get('website', ''),
                instagram=row.get('instagram', ''),
                facebook=row.get('facebook', ''),
                ticktock=row.get('ticktock', ''),
                twitter=row.get('twitter', ''),
                youtube=row.get('youtube', ''),
                description=row.get('description', ''),
                notes=row.get('notes', ''),
                is_church=is_church,
                is_organization=is_organization,
                is_influencer=is_influencer,
                is_media=is_media,
                services=row.get('services', ''),
                weekly_attendees=weekly_attendees,
                has_supported=row.get('has supported', ''),
            )
            data.save()

        messages.success(request, 'Data saved successfully!')
        return redirect('home')

    return render(request, 'upload_excel_sheet.html')

def get_value_from_columns(row, column_variations):
    """
    Get the value from the row using column variations.
    """
    for column in column_variations:
        if column in row:
            return row[column]
    return ''


def allData(request):
    datas = UserData.objects.all()
    return render(request, 'all_data.html', {"datas":datas})

def edit_data(request, data_id):
    data = get_object_or_404(UserData, id=data_id)
    
    if request.method == 'POST':
        # Update the data with the form inputs
        data.first_name = request.POST.get('first_name')
        data.last_name = request.POST.get('last_name')
        data.email = request.POST.get('email')
        data.phone = request.POST.get('phone')
        data.street_address = request.POST.get('street_address')
        data.city = request.POST.get('city')
        data.state = request.POST.get('state')
        data.country = request.POST.get('country')
        data.organization_name = request.POST.get('organization_name')
        data.title = request.POST.get('title')
        data.website = request.POST.get('website')
        data.instagram = request.POST.get('instagram')
        data.facebook = request.POST.get('facebook')
        data.ticktock = request.POST.get('ticktock')
        data.twitter = request.POST.get('twitter')
        data.youtube = request.POST.get('youtube')
        data.description = request.POST.get('description')
        data.notes = request.POST.get('notes')
        data.is_church = 'type' in request.POST and request.POST['type'] == 'church'
        data.is_organization = 'type' in request.POST and request.POST['type'] == 'organization'
        data.is_influencer = 'type' in request.POST and request.POST['type'] == 'influencer'
        data.is_media = 'type' in request.POST and request.POST['type'] == 'media'
        data.services = request.POST.getlist('services')
        data.weekly_attendees = request.POST.get('weekly_attendees')
        data.has_supported = request.POST.getlist('has_supported')
        
        # Save the updated data
        data.save()
        messages.success(request, 'Data Updated successfully!')
        return redirect("allData")
    else:
        return render(request, "edit_data.html", {"data": data})
def delete_data(request, data_id):
    data = get_object_or_404(UserData, id=data_id)
    data.delete()
    messages.success(request, 'Deleted successfully!') 
    return redirect("allData")

def convert_to_number(count):
    if count.endswith('k') or count.endswith('K'):
        return float(float(count[:-1]) * 1000)
    elif count.endswith('m') or count.endswith('M'):
        return float(float(count[:-1]) * 1000000)
    elif count.endswith('b') or count.endswith('B'):
        return float(float(count[:-1]) * 1000000000)
    else:
        return float(count.replace(',', ''))

def get_followers_from_instagram(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    meta_description = soup.find('meta', property='og:description')
    if meta_description:
        content = meta_description['content']
        followers_text = content.split(' ')[0]  # Extract the followers count
        followers_count = followers_text.replace(',', '')
        return int(convert_to_number(followers_count))
    else:
        return 0
    
def get_followers_from_twitter(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    follower_count_element = soup.find('a', {'data-nav': 'followers'})
    if follower_count_element:
        follower_count = follower_count_element['data-count']
        return int(convert_to_number(follower_count))
    else:
        return 0
    
def get_followers_from_facebook(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    follower_count_element = soup.find('a', class_='x1i10hfl')
    if follower_count_element:
        follower_count = follower_count_element.text.strip()
        return int(convert_to_number(follower_count))
    else:
        return 0
    
def get_followers_from_youtube(url):
    api_key = 'AIzaSyCI2uku8sTZh2Pw4PJaovG0UW-6cJqB-WM'
    # Extract the channel ID from the URL
    channel_id = url.strip('/').split('/')[-1]
    if channel_id:
        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            channel_response = youtube.channels().list(
                part='statistics',
                id=channel_id
            ).execute()

            if 'items' in channel_response and len(channel_response['items']) > 0:
                statistics = channel_response['items'][0]['statistics']
                subscriber_count = statistics['subscriberCount']
                return int(convert_to_number(subscriber_count))
            else:
                return 0

        except HttpError as e:
            print(f'An HTTP error occurred: {e}')
            return 0

        except Exception as e:
            print(f'An error occurred: {e}')
            return 0
    else:
        return 0
    
def get_followers_from_ticktock(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    followers_element = soup.find("strong", {"title": "Followers"})
    if followers_element:
        followers_count = followers_element.text.strip()
        return int(convert_to_number(followers_count))
    else:
        return 0