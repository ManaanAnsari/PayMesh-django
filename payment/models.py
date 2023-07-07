from django.db import models
from user_management.models import User

# Create your models here.

class SupportedChain(models.Model):
    chain_name = models.CharField(max_length=250)
    enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return self.chain_name + " " + "(enabled)" if self.enabled else "(disabled)" 
    
    class Meta:
        db_table = "supported_chain"
        

class SupportedNetwork(models.Model):
    chain = models.ForeignKey(SupportedChain, on_delete=models.CASCADE)
    network_name = models.CharField(max_length=250)
    url = models.TextField(default=None, null=True, blank=True)
    is_testnet = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    
    def __str__(self):
        dname = self.network_name + " " + "(testnet)" if self.is_testnet else "(mainnet)"
        return dname + " " + "(enabled)" if self.enabled else "(disabled)"
    class Meta:
        db_table = "supported_network"
        

class SupportedToken(models.Model):
    network = models.ForeignKey(SupportedNetwork, on_delete=models.CASCADE)
    contract_address = models.CharField(max_length=250)
    symbol = models.CharField(max_length=250)
    token_name = models.CharField(max_length=250)
    enabled = models.BooleanField(default=True)
    
    def __str__(self) -> str:
        dname =  self.symbol + " " + "(" + self.network.network_name + ")"
        dname += " " + "(enabled)" if self.enabled else "(disabled)"
        dname += " " + "(testnet)" if self.network.is_testnet else "(mainnet)"
        return dname
    

class Invoice(models.Model):
    STATUS = (
        ('CREATED', 'CREATED'),
        ('PROCESSING', 'PROCESSING'),
        ('SUCCESSFUL', 'SUCCESSFUL'),
        ('FAILED', 'FAILED'),
        ('UNDER_REVIEW', 'UNDER_REVIEW'),
        ('EXPIRED', 'EXPIRED'),
    )

    STATUS_LIST = [v[0] for v in STATUS]
   
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="CREATED",
    )
    
    token = models.ForeignKey(SupportedToken, on_delete=models.CASCADE)
    amount = models.FloatField()
    amount_paid = models.FloatField(default=None, null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver")
    customer_address = models.CharField(max_length=250, default=None, null=True, blank=True)
    link_hash = models.CharField(max_length=250, unique=True)
    payment_account_address = models.CharField(max_length=250, unique=True)
    payment_account_address_private_key = models.CharField(max_length=250, unique=True)
    expiry_mins = models.IntegerField(default=90)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(default=None, null=True, blank=True)
    closed_at = models.DateTimeField(default=None, null=True, blank=True)
    transacrion_details = models.TextField(default=None, null=True, blank=True)
    message = models.TextField(default=None, null=True, blank=True)
    metadata = models.JSONField(default=None, null=True, blank=True)
    
    
    def __str__(self) -> str:
        d_name = "#"+str(self.id)
        d_name += " #"+str(self.receiver.id)
        d_name += " "+ self.link_hash
        d_name += " " + "(" + self.token.symbol + ")"
        d_name += " " + "(" + self.status + ")"
        return d_name
    
    
    class Meta:
        db_table = "invoice"




class PayoutTransaction(models.Model):
    STATUS = (
        ('CREATED', 'CREATED'),
        ('PROCESSING', 'PROCESSING'),
        ('SUCCESSFUL', 'SUCCESSFUL'),
        ('FAILED', 'FAILED')
    )

    STATUS_LIST = [v[0] for v in STATUS]
   
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="CREATED",
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount_to_pay = models.FloatField(default=None, null=True, blank=True)
    amount_paid = models.FloatField(default=None, null=True, blank=True)
    fee_amount = models.FloatField(default=None, null=True, blank=True)
    fee_perc = models.FloatField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transacrion_details = models.TextField(default=None, null=True, blank=True)
    message = models.TextField(default=None, null=True, blank=True)
    
    
    def __str__(self) -> str:
        d_name = "#"+str(self.invoice.id)
        d_name += "#"+str(self.invoice.receiver.id)
        d_name += " "+ self.invoice.link_hash
        d_name += " " + "(" + self.status + ")"
        return d_name
    
    
    class Meta:
        db_table = "payout_transaction"
        


# creating a different 
class RefundTransaction(models.Model):
    '''
        This model is used to store the refund transaction details
        its a different model because in future me might want to add a few specific things only for refund 
    '''
    STATUS = (
        ('CREATED', 'CREATED'),
        ('PROCESSING', 'PROCESSING'),
        ('SUCCESSFUL', 'SUCCESSFUL'),
        ('FAILED', 'FAILED'),
        ('IGNORED', 'IGNORED')
    )

    STATUS_LIST = [v[0] for v in STATUS]
   
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="CREATED",
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount_to_pay = models.FloatField(default=None, null=True, blank=True)
    amount_paid = models.FloatField(default=None, null=True, blank=True)
    fee_amount = models.FloatField(default=None, null=True, blank=True)
    fee_perc = models.FloatField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transacrion_details = models.TextField(default=None, null=True, blank=True)
    message = models.TextField(default=None, null=True, blank=True)
    
    
    def __str__(self) -> str:
        d_name = "#"+str(self.id)
        d_name += " #"+str(self.invoice.id)
        d_name += "#"+str(self.invoice.receiver.id)
        d_name += " "+ self.invoice.link_hash
        d_name += " " + "(" + self.status + ")"
        return d_name
    
    
    class Meta:
        db_table = "refund_transaction"
        

class BlockchainTransaction(models.Model):

    STATUS = (
        ('SUCCESSFUL', 'SUCCESSFUL'),
        ('FAILED', 'FAILED')
    )

    STATUS_LIST = [v[0] for v in STATUS]
   
    status = models.CharField(
        max_length=20,
        choices=STATUS
    )
    
    TYPE = (
        ('GAS', 'GAS'),
        ('ERC20', 'ERC20'),
        ('CLOSE_WALLET', 'CLOSE_WALLET'),
    )
    
    TYPE_LIST = [v[0] for v in STATUS]
   
    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE
    )
    
    refund_transaction = models.ForeignKey(RefundTransaction, on_delete=models.CASCADE, default=None, null=True, blank=True)
    payout_transaction = models.ForeignKey(PayoutTransaction, on_delete=models.CASCADE, default=None, null=True, blank=True)
    message = models.TextField(default=None, null=True, blank=True)
    
    
    network = models.ForeignKey(SupportedNetwork, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_hash = models.CharField(max_length=250, unique=True, default=None, null=True, blank=True)
    transacrion_details = models.TextField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self) -> str:
        d_name = str(self.id)
        if self.refund_transaction is not None:
            d_name += " #" + str(self.refund_transaction.invoice.id) + "( refund )"
        
        if self.payout_transaction is not None:
            d_name += " #" + str(self.payout_transaction.invoice.id) + "( payout )"
        d_name += " " + self.transaction_type
        d_name += " " + self.network.network_name
        d_name += " " + "(" + self.status + ")"
        return d_name
    
    
    class Meta:
        db_table = "blockchain_transaction"


