from django.urls import path
from . import views

'''

Give all your html forms views here.

'''

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
]