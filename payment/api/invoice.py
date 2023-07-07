from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from backend.helpers import get_random_string, getOrCreateWeb3Acoount, encrypt_message, decrypt_message, intOrZero
from backend.pagination.base import GlobalPagination
from payment.serializers.invoice import InvoiceQRDataSerializer, InvoiceSerializer
from user_management.models import User
from rest_framework.permissions import IsAuthenticated
from payment.validators.invoice import PaymentLinkRequestValidator
from payment.models import Invoice, SupportedToken
from eth_account import Account
from django.db.models import Q
from datetime import datetime, timedelta
from rest_framework.generics import ListAPIView
# if this is not imported here celery will not be able to find the task
from payment.tasks import check_status, test_foo, mark_expired_invoices
from webhook_management.tasks import webhook_request, send_webhook_request


class PaymentLinkView(APIView):
    '''
        create payment link/invoice
    '''    
    
    def getUniqueLinkHash(self):
        link_hash = get_random_string()
        while Invoice.objects.filter(link_hash=link_hash).exists():
            link_hash = get_random_string()
        
        return link_hash
        
    
    
    permission_classes = (IsAuthenticated,)
    
    @swagger_auto_schema(request_body=PaymentLinkRequestValidator)
    def post(self,request,*args,**kwargs):
        content = {}
        serializer = PaymentLinkRequestValidator(data=request.data)
        if serializer.is_valid():
            # serializer is valid
            # get me 
            me = User.objects.get(pk=request.user.id)
            data = request.data
            # create the invoice 
            data["network"] = data["network"].lower()
            data["token"] = data["token"].lower()
            token = SupportedToken.objects.filter(symbol=data["token"],network__network_name=data["network"],enabled=True).first()
            if token:
                w3_acc = getOrCreateWeb3Acoount(me)
                itr = 1
                if Invoice.objects.filter(receiver=me).exists():
                    inv = Invoice.objects.filter(receiver=me).order_by('-pk').first()
                    itr  = inv.pk + 1
                
                Account.enable_unaudited_hdwallet_features()
                acct = Account.from_mnemonic(
                    decrypt_message(w3_acc.mnemonic),
                    account_path=f"m/44'/60'/0'/0/{itr}"
                )
                
                invoice_obj = Invoice(
                    status = "CREATED",
                    token = token,
                    amount = data["amount"],
                    receiver = me,
                    link_hash = self.getUniqueLinkHash(),
                    payment_account_address = acct.address,
                    payment_account_address_private_key = encrypt_message(acct.key.hex()),
                    metadata = data.get("metadata",None),
                )
                invoice_obj.save()
                # send the link 

                content["data"] = {
                    "invoice_id": invoice_obj.pk,
                    "link_hash": invoice_obj.link_hash,
                }
                content["message"] = "invoice successfully created!"
                return Response(content, status = status.HTTP_200_OK)
            content["message"] = "invalid token/network"
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        # invalid data
        content["message"] = "invalid data"
        content["errors"] = serializer.errors
        return Response(content, status = status.HTTP_400_BAD_REQUEST)


class InvoiceQRDataView(APIView):        
    '''
        get link using the hash
    '''
    
    link_hash_param = openapi.Parameter('link_hash', openapi.IN_QUERY, description="link hash", type=openapi.TYPE_STRING)
    @swagger_auto_schema(manual_parameters=[link_hash_param])
    def get(self,request,*args,**kwargs):
        content ={}
        link_hash = request.GET.get('link_hash', None)
        
        if Invoice.objects.filter(link_hash=link_hash).exists():
            invoice = Invoice.objects.get(link_hash=link_hash)
            content["data"] = InvoiceQRDataSerializer(invoice).data
            return Response(content, status = status.HTTP_200_OK)
        
        content["message"] = "invalid link hash"
        return Response(content, status = status.HTTP_400_BAD_REQUEST)



class InvoiceView(ListAPIView):        
    '''
        list invoices with pagination
    '''
    
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceSerializer
    pagination_class = GlobalPagination
    
    search_param = openapi.Parameter('search', openapi.IN_QUERY, description="search", type=openapi.TYPE_STRING)
    from_param = openapi.Parameter('from', openapi.IN_QUERY, description="from date-time", type=openapi.TYPE_STRING,format=openapi.FORMAT_DATETIME)
    to_param = openapi.Parameter('to', openapi.IN_QUERY, description="to date-time", type=openapi.TYPE_STRING,format=openapi.FORMAT_DATETIME)   
    @swagger_auto_schema(manual_parameters=[search_param,from_param,to_param])
    def get(self,request,*args,**kwargs):
        content ={}
        me = User.objects.get(pk=request.user.id)
        _from = request.GET.get('from', None)
        _to = request.GET.get('to', None)
        search = request.GET.get('search', None)
        
        qs = Invoice.objects.filter(receiver=me)
        
        search_int = 0   
        if search:
            search_int = intOrZero(search)
            qs = qs.filter(
                Q(pk=search_int) 
                | Q(status__icontains=search) | Q(token__symbol__icontains=search) 
                | Q(token__token_name__icontains=search) | Q(customer_address__icontains=search)
                | Q(link_hash__icontains=search) | Q(payment_account_address__icontains=search) 
                | Q(status__icontains=search)
            )
            
        if _from:
            qs = qs.filter(created_at__gte = _from)
        
        if _to:
            try:
                date_format = "%Y-%m-%d"
                # Convert string to date
                date_object = datetime.strptime(_to, date_format)
                # Add a day to the date
                new_date_object = date_object + timedelta(days=1)
                # Convert the new date back to a string
                _to = new_date_object.strftime(date_format)
            except Exception as e:
                print(e)
            qs = qs.filter(created_at__lte = _to)
        
        qs = qs.order_by('-pk')
        paginator = GlobalPagination()
        result_page = paginator.paginate_queryset(qs, request)
        serializer = InvoiceSerializer(result_page,many=True)
        content["data"] = serializer.data
        return paginator.get_paginated_response(serializer.data)
    
    
    id_param = openapi.Parameter('id', openapi.IN_QUERY, description="invoice id", type=openapi.TYPE_INTEGER, required=True)   
    @swagger_auto_schema(manual_parameters=[id_param])
    def delete(self,request,*args,**kwargs):
        content ={}
        me = User.objects.get(pk=request.user.id)
        _id = request.GET.get('id', None)
        invoice = Invoice.objects.filter(pk=_id,receiver=me).first()
        if invoice:
            if invoice.status in ["CREATED"]:
                invoice.delete()
                content["message"] = "invoice successfully deleted!"
                return Response(content, status = status.HTTP_200_OK)
            content["message"] = "invoice cannot be deleted!"
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        content["message"] = "invalid invoice id"
        return Response(content, status = status.HTTP_400_BAD_REQUEST)
        
        
        

        

    
    



