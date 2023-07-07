from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from backend.helpers import get_random_string, getOrCreateWeb3Acoount
from user_management.models import User, UserCaptcha, UserGateWeb3Account
from user_management.validators.auth import AuthRequestValidator
from rest_framework_simplejwt.tokens import RefreshToken
from eth_account.messages import encode_defunct
from web3.auto import w3
from django.contrib.auth.hashers import make_password 


class AuthView(APIView):
    '''
        login using connect wallet button
    '''
    
    address_param = openapi.Parameter('web3_address', openapi.IN_QUERY, description="web3 address", type=openapi.TYPE_STRING, required=True)
    @swagger_auto_schema(manual_parameters=[address_param])
    def get(self,request,*args,**kwargs):
        content = {}
        address = request.GET.get('web3_address')
        
        
        if not User.objects.filter(web3_address=address).exists():
            if not w3.is_address(address):
                content["message"] = "invalid address"
                return Response(content, status = status.HTTP_400_BAD_REQUEST)
            # create one
            user_obj = User(
                web3_address = address,
                password = make_password(get_random_string())
            )
            user_obj.save()
        
            getOrCreateWeb3Acoount(user_obj)
        
            
        user_obj = User.objects.get(web3_address=address)
        UserCaptcha.objects.filter(user=user_obj).delete()
        captcha = get_random_string()
        user_captcha_obj = UserCaptcha(
            captcha = captcha,
            user=user_obj
        )
        user_captcha_obj.save()
        
        content["data"] = {"captcha": user_captcha_obj.captcha}
        content["message"] = "successfully fetched!"
        return Response(content, status = status.HTTP_200_OK)
    
    
    @swagger_auto_schema(request_body=AuthRequestValidator)
    def post(self,request,*args,**kwargs):
        content = {}
        serializer = AuthRequestValidator(data=request.data)
        if serializer.is_valid():
            data = request.data
            print(data["signature"],data["web3_address"])
            if User.objects.filter(web3_address=data["web3_address"]).exists():
                user = User.objects.get(web3_address=data["web3_address"])
                # get the message
                if UserCaptcha.objects.filter(user=user).exists():
                    captcha = UserCaptcha.objects.get(user=user)
                    message = encode_defunct(text=captcha.captcha)
                    try:
                        pub2 = w3.eth.account.recover_message(message, signature=data["signature"])
                    except Exception as e:
                        content["message"] = "signature not valid"
                        return Response(content, status = status.HTTP_400_BAD_REQUEST)
                    if user.web3_address == pub2:
                        refresh = RefreshToken.for_user(user)
                        content["token"] = {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token)
                        }
                        return Response(content, status = status.HTTP_200_OK)
                    content["message"] = "signature not valid"
                    return Response(content, status = status.HTTP_400_BAD_REQUEST)
                content["message"] = "captcha not found" 
                return Response(content, status = status.HTTP_400_BAD_REQUEST) 
            content["message"] = "user not yet created"
            return Response(content, status = status.HTTP_400_BAD_REQUEST) 
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST) 