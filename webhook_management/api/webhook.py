from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from backend.helpers import generate_fernet_key, bytesToString, stringToBytes
from backend.pagination.base import GlobalPagination
from user_management.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView

from webhook_management.validators.webhook import CreateWebhookValidator, UpdateWebhookValidator
from webhook_management.models import WebHookSecret, WebHookRequest
from webhook_management.serializers.webhook import WebHookRequestSerializer, WebHookSecretSerializer



class WebhookView(APIView):
    # create webhook 
    # max allowed is 3
    
    permission_classes = (IsAuthenticated,)
    
    
    @swagger_auto_schema(request_body=CreateWebhookValidator)
    def post(self,request,*args,**kwargs):
        content = {}
        serializer = CreateWebhookValidator(data=request.data)
        if serializer.is_valid():
            # serializer is valid
            # get me 
            me = User.objects.get(pk=request.user.id)
            data = request.data
            if WebHookSecret.objects.filter(user=me).count() < 3:
                if data.get("endpoint",None):
                    endpoint = data["endpoint"]
                    skey = generate_fernet_key()
                    skey = bytesToString(skey)
                    wh = WebHookSecret(
                        user = me,
                        sec_key = skey,
                        endpoint = endpoint,  
                        enabled = False,
                    )
                    wh.save()
                    content["data"] = WebHookSecretSerializer(wh).data
                    content["message"] = "webhook successfully created!"
                    return Response(content, status = status.HTTP_200_OK)
                content["message"] = "endpoint is required!"
                return Response(content, status = status.HTTP_400_BAD_REQUEST)
            content["message"] = "max allowed webhooks is 3!"
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        # invalid data
        content["message"] = "invalid data"
        content["errors"] = serializer.errors
        return Response(content, status = status.HTTP_400_BAD_REQUEST)
    
    
    @swagger_auto_schema(request_body=UpdateWebhookValidator)
    def put(self,request,*args,**kwargs):
        content = {}
        serializer = UpdateWebhookValidator(data=request.data)
        if serializer.is_valid():
            # serializer is valid
            # get me 
            me = User.objects.get(pk=request.user.id)
            data = request.data
            if WebHookSecret.objects.filter(pk=data.get("webhook_id",None), user=me).exists():
                wh = WebHookSecret.objects.get(pk=data.get("webhook_id",None), user=me)
                wh.endpoint = data.get("endpoint",wh.endpoint)
                wh.enabled = data.get("enabled",wh.enabled)
                wh.save()         
                # create the invoice 
                content["message"] = " successfully updated!"
                content["data"] = WebHookSecretSerializer(wh).data
                return Response(content, status = status.HTTP_200_OK)
            content["message"] = "webhook not found!"
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        # invalid data
        content["message"] = "invalid data"
        content["errors"] = serializer.errors
        return Response(content, status = status.HTTP_400_BAD_REQUEST)
    
    
    # delete webhook    
    id_param = openapi.Parameter('id', openapi.IN_QUERY, description="webhook id", type=openapi.TYPE_INTEGER, required=True)   
    @swagger_auto_schema(manual_parameters=[id_param])
    def delete(self,request,*args,**kwargs):
        content ={}
        me = User.objects.get(pk=request.user.id)
        _id = request.GET.get('id', None)
        
        if WebHookSecret.objects.filter(pk=_id, user=me).exists():
            WebHookSecret.objects.filter(pk=_id, user=me).delete()
            content["message"] = "webhook successfully deleted!"
            return Response(content, status = status.HTTP_200_OK)
        
        content["message"] = "invalid webhook id"
        return Response(content, status = status.HTTP_400_BAD_REQUEST)



# get created webhooks
class getWebhookView(ListAPIView):        
    
    permission_classes = (IsAuthenticated,)
    serializer_class = WebHookSecretSerializer
    pagination_class = GlobalPagination
    
    def get(self,request,*args,**kwargs):
        me = User.objects.get(pk=request.user.id)
        qs = WebHookSecret.objects.filter(user=me)        
        qs = qs.order_by('-pk')
        paginator = GlobalPagination()
        result_page = paginator.paginate_queryset(qs, request)
        serializer = WebHookSecretSerializer(result_page,many=True)
        return paginator.get_paginated_response(serializer.data)        


       
class getWebhookRequestView(ListAPIView):        
    
    permission_classes = (IsAuthenticated,)
    serializer_class = WebHookRequestSerializer
    pagination_class = GlobalPagination
    
    def get(self,request,*args,**kwargs):
        me = User.objects.get(pk=request.user.id)
        qs = WebHookRequest.objects.filter(webhook__user=me)        
        qs = qs.order_by('-pk')
        paginator = GlobalPagination()
        result_page = paginator.paginate_queryset(qs, request)
        serializer = WebHookRequestSerializer(result_page,many=True)
        return paginator.get_paginated_response(serializer.data)        


class WebhookTestReceiverView(APIView):        
    '''
        just to test webhook
    '''
    
    def post(self,request,*args,**kwargs):
        print(request.data)
        return Response({"message":"ok"}, status = status.HTTP_200_OK)
        
                
        


