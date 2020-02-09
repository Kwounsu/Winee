from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index),
    path('login/', auth_views.LoginView.as_view()),
    path('logout/', views.logout_view),
    path('register/', views.register),
    path('search/', views.search, name='search'),
    path('wine_info/<int:wine_id>/', views.wine_info),
    path('MyPage/', views.mypage),
    path('upload-csv/', views.wine_upload),
]