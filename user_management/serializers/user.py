from rest_framework import serializers
from user_management.models import User, Web3Address, UserGateWeb3Account


class UserGateWeb3AccountSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserGateWeb3Account
        fields = ("address","address_type",)

class UserSerializer(serializers.ModelSerializer): 
    gate_addresses = serializers.SerializerMethodField('get_gate_address')
    
    def get_gate_address(self, obj):
        return UserGateWeb3AccountSerializer(UserGateWeb3Account.objects.filter(user=obj), many=True).data
    
    class Meta:
        model = User
        # fields = '__all__'
        exclude = ('password', 'groups','user_permissions','is_superuser','is_active') 

        
class Web3AddressSerializer(serializers.ModelSerializer): 

    class Meta:
        model = Web3Address
        fields = '__all__'