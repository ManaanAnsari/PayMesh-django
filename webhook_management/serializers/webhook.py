
from rest_framework import serializers
from webhook_management.models import WebHookSecret, WebHookRequest


class WebHookSecretSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = WebHookSecret
        fields = "__all__"


class WebHookRequestSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = WebHookRequest
        fields = "__all__"


