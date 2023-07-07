
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt import views as jwt_views
from django.conf import settings
from django.views.static import serve
from payment.views import qr_temp_view


# for swagger
schema_view = get_schema_view(
   openapi.Info(
      title="API",
      default_version='v1',
      description="Testing API",
      terms_of_service="https://nobodycares.com/",
      contact=openapi.Contact(email="someone@fromearth.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

# prefix of url like api/v1/endpoint
API_PREFIX = "api/v"+str(settings.API_VERSION)+"/"


urlpatterns = [
    # django admin pannel (not the react one)
    path("admin/", admin.site.urls),
    path('qr_temp/<str:link_hash>', qr_temp_view, name ='qr'),

    
    # swagger docs ui 
    path(API_PREFIX, schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(API_PREFIX+'redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Auth: login and get JWT
    path(API_PREFIX+'token/',
        jwt_views.TokenObtainPairView.as_view(),
        name ='token_obtain_pair'
    ),
    
    path(
        API_PREFIX+'token/refresh/',
        jwt_views.TokenRefreshView.as_view(),
        name ='token_refresh'),
    
    path(API_PREFIX+'token/logout/',
        jwt_views.TokenBlacklistView.as_view(),
        name ='logout'
    ),
    
    # our created apps endpoints
    path(API_PREFIX+'user/', include('user_management.urls')),
    
    path(API_PREFIX+'payment/', include('payment.urls')),
    path(API_PREFIX+'webhook/', include('webhook_management.urls')),
    
    # if media uploaded on local 
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT,})
]