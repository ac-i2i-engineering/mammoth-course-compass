from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create_course/', views.create_course, name='create_course'),
    path('upload_csv/', views.upload_csv, name='upload_csv'),
]