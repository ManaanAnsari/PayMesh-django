from django.db import models

# Create your models here.


class WebHookSecret(models.Model):
    user = models.ForeignKey("user_management.User", on_delete=models.CASCADE)
    sec_key = models.TextField()
    endpoint = models.TextField()  
    enabled = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return "#"+ str(self.user.id) + " || " + str(self.id) 
    
    class Meta:
        db_table = "webhook_secret"
        

class WebHookRequest(models.Model):
    '''
    webhook
    event type
    request type
    request data
    response status code
    request sent at 
    '''
    webhook = models.ForeignKey("WebHookSecret", on_delete=models.CASCADE)
    EVENT_TYPES = (
        ('INVOICE_SUCCESSFUL', 'INVOICE_SUCCESSFUL'),
        ('INVOICE_FAILED', 'INVOICE_FAILED'),
        ('INVOICE_UNDER_REVIEW', 'INVOICE_UNDER_REVIEW'),
        ('INVOICE_EXPIRED', 'INVOICE_EXPIRED'),
        ('PAYOUT_SUCCESSFUL', 'PAYOUT_SUCCESSFUL'),
        ('PAYOUT_FAILED', 'PAYOUT_FAILED'),
        ('REFUND_SUCCESSFUL', 'REFUND_SUCCESSFUL'),
        ('REFUND_FAILED', 'REFUND_FAILED'),
    )

    EVENT_TYPES_LIST = [v[0] for v in EVENT_TYPES]
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES,
    )
    
    REQUEST_TYPES = (
        ('POST', 'POST'),
    )

    REQUEST_TYPES_LIST = [v[0] for v in REQUEST_TYPES]
    request_type = models.CharField(
        max_length=30,
        choices=REQUEST_TYPES,
        default="POST"
    )
    
    request_data = models.JSONField(default=dict)
    response_status_code = models.IntegerField(default=None, null=True, blank=True)
    request_sent_at = models.DateTimeField(default=None, null=True,blank=True)
    
    REQUEST_STATUS = (
        ('CREATED', 'CREATED'),
        ('PROCESSING', 'PROCESSING'),
        ('SUCCESSFUL', 'SUCCESSFUL'),
        ('FAILED', 'FAILED'),
    )

    REQUEST_STATUS_LIST = [v[0] for v in REQUEST_STATUS]
    request_status = models.CharField(
        max_length=30,
        choices=REQUEST_TYPES,
        default="CREATED"
    )
    
    def __str__(self) -> str:
        return "#"+ str(self.id) 
    
    class Meta:
        db_table = "webhook_request"
        

