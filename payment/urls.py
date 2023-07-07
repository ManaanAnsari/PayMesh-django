from django.urls import path
from payment.api import invoice as invoice_api 


urlpatterns = [
    path('invoice/', invoice_api.InvoiceView.as_view(), name ='invoice'),
    path('link/', invoice_api.PaymentLinkView.as_view(), name ='link'),
    path('qr_data/', invoice_api.InvoiceQRDataView.as_view(), name ='qr_data')    
]