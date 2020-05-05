from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index),
    path('login/', auth_views.LoginView.as_view()),
    path('login-dev/', auth_views.LoginView.as_view()),
    path('logout/', views.logout_view),
    path('register/', views.register),
    path('search/', views.search, name='search'),
    path('wine_info/<int:wine_id>/', views.wine_info),
    path('MyPage/', views.mypage),
    path('ratingWine/<int:wine_id>/<int:rate>/', views.ratingWine),
    path('AddWishList/<int:wine_id>/', views.AddWishList),
    path('DelWishList/<int:wine_id>/', views.DelWishList),
]