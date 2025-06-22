from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from food.models import Order
import qrcode
import io
import base64

@login_required
def payment_options(request):
    if 'current_order_id' not in request.session:
        return redirect('food:food_selection')
    
    order = Order.objects.get(id=request.session['current_order_id'])
    
    context = {
        'order': order,
        'table_number': order.table.table_number,
    }
    
    return render(request, 'payment/payment_options.html', context)

@login_required
def generate_qr(request, order_id):
    order = Order.objects.get(id=order_id)
    
    # Generate QR code data
    payment_data = f"order:{order.id}|amount:{order.total_amount}|table:{order.table.table_number}"
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return JsonResponse({
        'qr_code': f'data:image/png;base64,{img_base64}',
        'order_id': order.id
    })

@login_required
def payment_success(request, order_id):
    order = Order.objects.get(id=order_id)
    order.is_paid = True
    order.payment_method = 'qr'
    order.save()
    
    # Unlock table
    table = order.table
    table.is_locked = False
    table.locked_by = None
    table.locked_at = None
    table.save()
    
    # Clear session
    request.session.pop('current_order_id', None)
    request.session.pop('selected_table_id', None)
    
    return render(request, 'payment/success.html', {'order': order})