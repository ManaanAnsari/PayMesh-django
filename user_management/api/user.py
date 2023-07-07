from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_management.models import User, Web3Address
from user_management.serializers.user import UserSerializer, Web3AddressSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from user_management.validators.user import UpdateUserValidator, UserAddressUpdateValidator, UserAddressValidator
from web3.auto import w3



class UserView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    
    def get(self,request,*args,**kwargs):
        content = {}
        user = User.objects.get(pk = request.user.id)
        serializer = UserSerializer(user)
        content["data"] = serializer.data
        content["message"] = "successfully fetched!"
        return Response(content, status = status.HTTP_200_OK)
    
    
    @swagger_auto_schema(request_body=UpdateUserValidator)
    def put(self,request,*args,**kwargs):
        content = {}
        serializer = UpdateUserValidator(data=request.data)
        me = User.objects.get(id= request.user.id)
        if serializer.is_valid():
            data = request.data
            me.name = data.get("name") if data.get("name", None) else me.name
            if data.get("email", None):
                if User.objects.filter(Q(email=data.get("email")) & ~Q(id=me.id)).exists():
                    content["message"] = "email already exists"
                    return Response(content, status = status.HTTP_400_BAD_REQUEST)
                me.email = data.get("email")
            me.save()
            serializer = UserSerializer(me)
            content["data"] = serializer.data
            return Response(content, status=status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST) 



class UserAddressView(APIView):
    '''
    note: we dont need this for now
    '''
    permission_classes = (IsAuthenticated,)
    serializer_class = Web3AddressSerializer
    
    def get(self,request,*args,**kwargs):
        content = {}
        me = User.objects.get(pk = request.user.id)
        content["data"] = Web3AddressSerializer(Web3Address.objects.filter(user=me),many=True).data
        content["message"] = "successfully fetched!"
        return Response(content, status = status.HTTP_200_OK)
    
    @swagger_auto_schema(request_body=UserAddressValidator)
    def post(self,request,*args,**kwargs):
        content = {}
        serializer = UserAddressValidator(data=request.data)
        me = User.objects.get(id= request.user.id)
        if serializer.is_valid():
            data = request.data
            # dont allow more than 10 address
            if Web3Address.objects.filter(user=me).count() >= 10:
                content["message"] = "max 10 address allowed"
                return Response(content, status = status.HTTP_400_BAD_REQUEST)
            
            if Web3Address.objects.filter(address=data.get("address"),user=me).exists():
                content["message"] = "address already exists"
                return Response(content, status = status.HTTP_400_BAD_REQUEST)
            
            if not w3.is_address(data.get("address")):
                content["message"] = "invalid address"
                return Response(content, status = status.HTTP_400_BAD_REQUEST)
            
            addr_obj = Web3Address(
                user = me,
                address = data.get("address"),
                address_type = data.get("address_type"), 
                human_name = data.get("human_name",None),  
            )
            addr_obj.save()
            
            content["data"] = Web3AddressSerializer(addr_obj).data
            content["message"] = "successfully added!"
            return Response(content, status=status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST) 

    
    @swagger_auto_schema(request_body=UserAddressUpdateValidator)
    def put(self,request,*args,**kwargs):
        content = {}
        serializer = UserAddressUpdateValidator(data=request.data)
        me = User.objects.get(id= request.user.id)
        if serializer.is_valid():
            data = request.data
            if Web3Address.objects.filter(id = data.get("address_id") ,user=me).exists():
                addr_obj = Web3Address.objects.get(id = data.get("address_id"))
                addr_obj.human_name = data.get("human_name") if data.get("human_name", None) else addr_obj.human_name
                addr_obj.address_type = data.get("address_type") if data.get("address_type", None) else addr_obj.address_type
                
                if data.get("address", None):
                    if addr_obj.address != data.get("address"):
                        if addr_obj.address_type.lower() == "evm":
                            if not w3.is_address(data.get("address")):
                                content["message"] = "invalid address"
                                return Response(content, status = status.HTTP_400_BAD_REQUEST)
                            addr_obj.address = data.get("address")
                
                addr_obj.save()
                content["data"] = Web3AddressSerializer(addr_obj).data
                content["message"] = "successfully updated!"
                return Response(content, status=status.HTTP_200_OK)
            content["message"] = "address does not exists"
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST) 

    
    address_id_param = openapi.Parameter('id', openapi.IN_QUERY, description="address id", type=openapi.TYPE_INTEGER)
    @swagger_auto_schema(manual_parameters=[address_id_param])
    def delete(self,request,*args,**kwargs):
        content = {}
        me = User.objects.get(id= request.user.id)
        if Web3Address.objects.filter(id=request.GET.get("id"),user=me).exists():
            Web3Address.objects.filter(id=request.GET.get("id"),user=me).delete()
            content["message"] = "successfully deleted!"
            return Response(content, status=status.HTTP_200_OK)
        content["message"] = "address does not exists"
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    


