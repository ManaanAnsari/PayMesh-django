from rest_framework import serializers
from payment.models import SupportedNetwork, SupportedToken


class PaymentLinkRequestValidator(serializers.Serializer):
    amount = serializers.FloatField()
    network = serializers.CharField(max_length=100)
    token = serializers.CharField(max_length=100)
    metadata = serializers.JSONField(required=False)
       
    def validate(self, data):
        if data.get("network",None) and data.get("token",None):
            data["network"] = data["network"].lower()
            data["token"] = data["token"].lower()
            print(data)
            network_name = data["network"]
            token_symbol = data["token"]
            if SupportedNetwork.objects.filter(network_name=network_name, enabled=True).exists():
                network = SupportedNetwork.objects.get(network_name=network_name, enabled=True)
                print(network)
                if SupportedToken.objects.filter(network = network, symbol=token_symbol, enabled=True).exists():
                    print("token exists")
                    if data["amount"] > 0:
                        return data
                    else:
                        raise serializers.ValidationError("amount must be greater than 0")
                
        raise serializers.ValidationError("invalid token/network")
    
    
    
