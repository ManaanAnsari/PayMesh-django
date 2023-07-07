from rest_framework import serializers


class AuthRequestValidator(serializers.Serializer):
    signature = serializers.CharField()
    web3_address = serializers.CharField()