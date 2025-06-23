from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from tables.models import Table
from food.models import FoodItem, Order, FoodCategory
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

# Set up logging
logger = logging.getLogger(__name__)

@staff_member_required
def dashboard(request):
    today = timezone.now().date()
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Daily revenue
    daily_revenue = Order.objects.filter(
        created_at__date=today,
        is_paid=True
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Monthly revenue
    monthly_revenue = Order.objects.filter(
        created_at__month=current_month,
        created_at__year=current_year,
        is_paid=True
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related('table', 'user').order_by('-created_at')[:10]
    
    # Pending payments
    pending_payments = Order.objects.filter(is_paid=False).count()
    
    context = {
        'daily_revenue': daily_revenue,
        'monthly_revenue': monthly_revenue,
        'recent_orders': recent_orders,
        'pending_payments': pending_payments,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

@staff_member_required
def change_order_status(request, order_id):
    logger.info(f"=== CHANGE ORDER STATUS REQUEST ===")
    logger.info(f"Order ID: {order_id}")
    logger.info(f"Method: {request.method}")
    logger.info(f"User: {request.user}")
    logger.info(f"Is staff: {request.user.is_staff}")
    logger.info(f"Is authenticated: {request.user.is_authenticated}")
    
    if request.method == 'POST':
        try:
            logger.info(f"Attempting to get order with ID: {order_id}")
            order = Order.objects.get(id=order_id)
            logger.info(f"Order found: {order}")
            
            # Update order status
            order.is_paid = True
            order.payment_method = 'counter'
            order.save()
            logger.info(f"Order {order_id} marked as paid")
            
            # Unlock the table
            table = order.table
            table.is_locked = False
            table.locked_by = None
            table.locked_at = None
            table.save()
            logger.info(f"Table {table.table_number} unlocked")
            
            # Send WebSocket notification to customer
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'order_{order_id}',
                    {
                        'type': 'payment_complete',
                        'message': 'Payment successful',
                        'order_id': order_id
                    }
                )
                logger.info(f"WebSocket notification sent for order {order_id}")
            except Exception as ws_error:
                logger.error(f"WebSocket notification failed: {ws_error}")
                # Don't fail the whole request if WebSocket fails
            
            logger.info(f"Successfully processed order {order_id}")
            return JsonResponse({'success': True})
            
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found")
            return JsonResponse({'success': False, 'error': 'Order not found'})
        except Exception as e:
            logger.error(f"Error processing order {order_id}: {str(e)}")
            logger.exception("Full traceback:")
            return JsonResponse({'success': False, 'error': str(e)})
    
    logger.warning(f"Invalid request method: {request.method}")
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def manage_tables(request):
    tables = Table.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"Action received: {action}")  # Debug print
        
        if action == 'add_table':
            table_number = request.POST.get('table_number')
            capacity = request.POST.get('capacity', 4)
            image = request.FILES.get('table_image')  # Get uploaded image
            
            table = Table.objects.create(
                table_number=table_number, 
                capacity=capacity
            )
            
            if image:
                table.image = image
                table.save()
                print(f"Image saved for table {table_number}")  # Debug print
        
        elif action == 'unlock_table':
            table_id = request.POST.get('table_id')
            table = Table.objects.get(id=table_id)
            table.is_locked = False
            table.locked_by = None
            table.locked_at = None
            table.save()
            print(f"Table {table.table_number} unlocked")  # Debug print
        
        elif action == 'update_table_image':
            table_id = request.POST.get('table_id')
            image = request.FILES.get('table_image')
            print(f"Updating image for table {table_id}")  # Debug print
            print(f"Files received: {request.FILES}")  # Debug print
            
            if table_id and image:
                try:
                    table = Table.objects.get(id=table_id)
                    # Delete old image if exists
                    if table.image:
                        table.image.delete(save=False)
                    # Save new image
                    table.image = image
                    table.save()
                    print(f"Image updated for table {table.table_number}")  # Debug print
                except Table.DoesNotExist:
                    print(f"Table with id {table_id} not found")  # Debug print
            else:
                print("No table_id or image provided")  # Debug print
        
        return redirect('admin_panel:manage_tables')
    
    return render(request, 'admin_panel/manage_tables.html', {'tables': tables})

@staff_member_required
def manage_food(request):
    food_items = FoodItem.objects.all()
    categories = FoodCategory.objects.all()
    
    if request.method == 'POST':
        # Handle food item creation
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        is_spicy = request.POST.get('is_spicy') == 'on'
        is_popular = request.POST.get('is_popular') == 'on'
        
        FoodItem.objects.create(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            image=image,
            is_spicy=is_spicy,
            is_popular=is_popular
        )
        
        return redirect('admin_panel:manage_food')
    
    return render(request, 'admin_panel/manage_food.html', {
        'food_items': food_items,
        'categories': categories
    })