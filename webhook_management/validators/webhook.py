from rest_framework import serializers
from webhook_management.models import WebHookSecret
from backend.helpers import is_valid_url



class CreateWebhookValidator(serializers.Serializer):
    endpoint = serializers.CharField(max_length=200)
    
    def validate(self, data):
        if data.get("endpoint",None):
            if is_valid_url(data["endpoint"]):
                return data
            raise serializers.ValidationError("invalid url")
        

class UpdateWebhookValidator(serializers.Serializer):
    webhook_id = serializers.IntegerField()
    endpoint = serializers.CharField(max_length=200, required=False)
    enabled = serializers.BooleanField(required=False)
   
    def validate(self, data):
        if data.get("webhook_id",None):
            if WebHookSecret.objects.filter(pk=data.get("webhook_id",None)).exists():
                if data.get("endpoint",None):
                    if not is_valid_url(data["endpoint"]):
                        raise serializers.ValidationError("invalid url")
                return data
        raise serializers.ValidationError("webhook not found!")

    
    
