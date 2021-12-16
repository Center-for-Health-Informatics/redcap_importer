from django.urls import path, include

from . import views


urlpatterns = [ 
    
   path('projects/<str:data_source>/<int:project_id>/events', views.project_details_events, name='project_details_events'),
   path('projects/<str:data_source>/<int:project_id>/instruments', views.project_details_instruments, name='project_details_instruments'),
   path('projects/<str:data_source>/<int:project_id>/records', views.project_details_records, name='project_details_records'),
   path('projects/<str:data_source>/<int:project_id>/instruments/<int:instrument_id>', views.instrument_details, name='instrument_details'),
   path('projects/<str:data_source>/<int:project_id>/fields/<int:field_id>', views.field_details, name='field_details'),
   
   path('projects/<str:data_source>/<int:project_id>/record/<str:record_id>', views.redcap_record, name='redcap_record'), 
    

   path('projects/<int:project_id>/events', views.project_details_events, name='project_details_events'),
   path('projects/<int:project_id>/instruments', views.project_details_instruments, name='project_details_instruments'),
   path('projects/<int:project_id>/records', views.project_details_records, name='project_details_records'),
   path('projects/<int:project_id>/instruments/<int:instrument_id>', views.instrument_details, name='instrument_details'),
   path('projects/<int:project_id>/fields/<int:field_id>', views.field_details, name='field_details'),
   
   path('projects/<int:project_id>/record/<str:record_id>', views.redcap_record, name='redcap_record'),

   path('ajax/recent-upload-list', views.ajax_recent_upload_list, name='ajax_recent_upload_list'),
   
   path('', views.home, name='home'),
]