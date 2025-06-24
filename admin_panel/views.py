from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from tables.models import Table
from food.models import FoodItem, Order, FoodCategory
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User  # IMPORTANT: Add this import

# Set up logging
logger = logging.getLogger(__name__)

def admin_required(view_func):
    """Custom decorator to check if user is admin/staff"""
    def wrapper(request, *args, **kwargs):
        print(f"\n=== ADMIN_REQUIRED DECORATOR CHECK ===")
        print(f"Request path: {request.path}")
        print(f"Request method: {request.method}")
        print(f"Request user: {request.user}")
        print(f"User authenticated: {request.user.is_authenticated}")
        
        if not request.user.is_authenticated:
            print(f"❌ FAILED: User not authenticated")
            logger.warning(f"Unauthenticated user trying to access admin panel: {request.path}")
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        
        print(f"User is_staff: {request.user.is_staff}")
        print(f"User is_superuser: {request.user.is_superuser}")
        
        if not (request.user.is_staff or request.user.is_superuser):
            print(f"❌ FAILED: User lacks admin privileges")
            print(f"User details - ID: {request.user.id}, Username: {request.user.username}")
            logger.warning(f"Non-staff user trying to access admin panel: {request.user.username}")
            return JsonResponse({'success': False, 'error': 'Admin privileges required'}, status=403)
        
        print(f"✅ PASSED: User has admin privileges")
        print(f"=== END ADMIN_REQUIRED CHECK ===\n")
        
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def dashboard(request):
    print(f"\n=== DASHBOARD ACCESS ===")
    print(f"User: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"Is staff: {request.user.is_staff}")
    print(f"Is superuser: {request.user.is_superuser}")
    
    # IMPORTANT: Check if user has admin privileges
    if not (request.user.is_staff or request.user.is_superuser):
        print(f"❌ Dashboard access denied for user: {request.user}")
        return redirect('authentication:login')
    
    print(f"✅ Dashboard access granted")
    
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

@admin_required
@require_http_methods(["POST"])
def change_order_status(request, order_id):
    print(f"\n=== CHANGE ORDER STATUS FUNCTION START ===")
    print(f"Order ID: {order_id}")
    print(f"Request method: {request.method}")
    print(f"Request user: {request.user}")
    print(f"User ID: {request.user.id}")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"User is_staff: {request.user.is_staff}")
    print(f"User is_superuser: {request.user.is_superuser}")
    print(f"Session key: {request.session.session_key}")
    
    # Log session data
    print(f"Session data: {dict(request.session)}")
    
    # Check headers
    print(f"Request headers:")
    for key, value in request.headers.items():
        if 'csrf' in key.lower() or 'auth' in key.lower() or 'cookie' in key.lower():
            print(f"  {key}: {value}")
    
    logger.info(f"=== CHANGE ORDER STATUS REQUEST ===")
    logger.info(f"Order ID: {order_id}")
    logger.info(f"Method: {request.method}")
    logger.info(f"User: {request.user}")
    logger.info(f"Is staff: {request.user.is_staff}")
    logger.info(f"Is authenticated: {request.user.is_authenticated}")
    
    try:
        logger.info(f"Attempting to get order with ID: {order_id}")
        order = Order.objects.get(id=order_id)
        logger.info(f"Order found: {order}")
        print(f"✅ Order found: {order}")
        
        # Check if order is already paid
        if order.is_paid:
            print(f"❌ Order {order_id} is already paid")
            logger.warning(f"Order {order_id} is already paid")
            return JsonResponse({'success': False, 'error': 'Order already paid'})
        
        # Update order status
        order.is_paid = True
        order.payment_method = 'counter'
        order.save()
        logger.info(f"Order {order_id} marked as paid")
        print(f"✅ Order {order_id} marked as paid")
        
        # Unlock the table
        table = order.table
        table.is_locked = False
        table.locked_by = None
        table.locked_at = None
        table.save()
        logger.info(f"Table {table.table_number} unlocked")
        print(f"✅ Table {table.table_number} unlocked")
        
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
            print(f"✅ WebSocket notification sent for order {order_id}")
        except Exception as ws_error:
            logger.error(f"WebSocket notification failed: {ws_error}")
            print(f"⚠️ WebSocket notification failed: {ws_error}")
            # Don't fail the whole request if WebSocket fails
        
        logger.info(f"Successfully processed order {order_id}")
        print(f"✅ Successfully processed order {order_id}")
        print(f"=== CHANGE ORDER STATUS FUNCTION END ===\n")
        
        return JsonResponse({'success': True, 'message': 'Order marked as paid successfully'})
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        print(f"❌ Order {order_id} not found")
        print(f"=== CHANGE ORDER STATUS FUNCTION END (ERROR) ===\n")
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        logger.error(f"Error processing order {order_id}: {str(e)}")
        logger.exception("Full traceback:")
        print(f"❌ Error processing order {order_id}: {str(e)}")
        print(f"=== CHANGE ORDER STATUS FUNCTION END (ERROR) ===\n")
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)

@login_required
def manage_tables(request):
    # Check if user has admin privileges
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('authentication:login')
        
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

@login_required
def manage_food(request):
    # Check if user has admin privileges
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('authentication:login')
        
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

def test_auth(request):
    """Test endpoint to check authentication status"""
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'is_staff': request.user.is_staff if request.user.is_authenticated else False,
        'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
        'session_key': request.session.session_key,
        'user_id': request.user.id if request.user.is_authenticated else None,
    })

def debug_session_state(request):
    """Debug view to monitor session state and detect interference"""
    
    # Get current session info
    session_key = request.session.session_key
    session_user_id = request.session.get('_auth_user_id')
    
    # Get all active sessions
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    session_info = []
    for session in active_sessions:
        try:
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass
            
            session_info.append({
                'session_key': session.session_key,
                'user_id': user_id,
                'username': user.username if user else None,
                'is_staff': user.is_staff if user else False,
                'is_current': session.session_key == session_key,
                'expire_date': session.expire_date.isoformat(),
            })
        except Exception as e:
            session_info.append({
                'session_key': session.session_key,
                'error': str(e),
                'is_current': session.session_key == session_key,
            })
    
    return JsonResponse({
        'current_session': {
            'session_key': session_key,
            'user_id': session_user_id,
            'request_user': {
                'username': request.user.username if request.user.is_authenticated else None,
                'is_staff': request.user.is_staff if request.user.is_authenticated else False,
                'is_authenticated': request.user.is_authenticated,
                'id': request.user.id if request.user.is_authenticated else None,
            }
        },
        'all_sessions': session_info,
        'session_count': len(session_info),
        'timestamp': timezone.now().isoformat(),
    })

def cleanup_sessions(request):
    """Clean up all sessions and force fresh login"""
    if request.method == 'POST':
        # Delete ALL sessions
        Session.objects.all().delete()
        print("All sessions deleted")
        
        return JsonResponse({
            'success': True,
            'message': 'All sessions cleared. Please login again.',
        })
    
    return JsonResponse({
        'success': False,
        'error': 'POST method required'
    })