from django.urls import path
from webhook_management.api import webhook as webhook_api


urlpatterns = [
    # signups
    path('webhook/', webhook_api.WebhookView.as_view(), name ='webhook'),
    path('getwebhook/', webhook_api.getWebhookView.as_view(), name ='getwebhook'),
    path('requests/', webhook_api.getWebhookRequestView.as_view(), name ='requests'),
    # only for testing
    path('test_receive/', webhook_api.WebhookTestReceiverView.as_view(), name ='test_receive'),    
]