from rest_framework import serializers
from user_management.models import Web3Address

class UpdateUserValidator(serializers.Serializer):
    name = serializers.CharField(max_length=100,required=False)
    email = serializers.EmailField(required=False)


class UserAddressValidator(serializers.Serializer):
    address = serializers.CharField(max_length=100,required=True)
    address_type = serializers.ChoiceField(choices=Web3Address.ADDRESS_TYPES_LIST,required=True)
    human_name = serializers.CharField(max_length=100,required=False)

class UserAddressUpdateValidator(serializers.Serializer):
    address_id = serializers.IntegerField(required=True)
    address = serializers.CharField(max_length=100,required=False)
    address_type = serializers.ChoiceField(choices=Web3Address.ADDRESS_TYPES_LIST,required=False)
    human_name = serializers.CharField(max_length=100,required=False)



