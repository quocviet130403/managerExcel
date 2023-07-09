from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('all_data/', views.allData, name='allData'),
    path('input_manually/', views.input_manually, name='input_manually'),
    path('upload_excel_sheet/', views.upload_excel_sheet, name='upload_excel_sheet'),
    path('edit/<int:data_id>/', views.edit_data, name='edit_data'),
    path('delete/<int:data_id>/', views.delete_data, name='delete_data'),
]