from django.shortcuts import render,redirect
from payment.models import Invoice
from payment.serializers.invoice import InvoiceQRDataSerializer
import qrcode
from io import BytesIO


def qr_temp_view(request,link_hash):
    '''
        this is a temporary view to show the qr code
        we will remove this view once we have the frontend 
    '''
   
    context = {}
    
    if Invoice.objects.filter(link_hash=link_hash).exists():
        invoice = Invoice.objects.get(link_hash=link_hash)
        if invoice.status == "CREATED":
            # context["invoice"] = InvoiceQRDataSerializer(invoice).data
            # Generate the QR code image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(invoice.payment_account_address)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert the QR code image to BytesIO object
            qr_bytes = BytesIO()
            qr_img.save(qr_bytes)
            context["qr_code"] = qr_bytes.getvalue()
        context["invoice"] = invoice
    return render(request, 'qr.html', context)