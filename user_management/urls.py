from django.urls import path
from user_management.api import auth as auth_api 
from user_management.api import user as user_api


urlpatterns = [
    # signups
    path('auth/', auth_api.AuthView.as_view(), name ='auth'),
    path('user/', user_api.UserView.as_view(), name ='user'),
    # path('address/', user_api.UserAddressView.as_view(), name ='user_address'),
]