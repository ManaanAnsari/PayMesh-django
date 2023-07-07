
from rest_framework import serializers
from payment.models import Invoice, PayoutTransaction, RefundTransaction

class InvoiceQRDataSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Invoice
        fields = (
            "status", 
            "token", 
            "amount", 
            "receiver",
            "customer_address",
            "link_hash", 
            "payment_account_address", 
            "created_at",
        )


class PayoutTransactionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PayoutTransaction
        fields = "__all__"
        

class RefundTransactionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = RefundTransaction
        fields = "__all__"
        

class InvoiceSerializer(serializers.ModelSerializer):
    payout_transaction = serializers.SerializerMethodField('get_payout_transaction')
    refund_transaction = serializers.SerializerMethodField('get_refund_transaction')
    
    def get_payout_transaction(self, obj):
        return PayoutTransactionSerializer(PayoutTransaction.objects.filter(invoice=obj), many=True).data

    def get_refund_transaction(self, obj):
        return RefundTransactionSerializer(RefundTransaction.objects.filter(invoice=obj), many=True).data
    
    class Meta:
        model = Invoice
        exclude = (
            "payment_account_address_private_key",
        )


