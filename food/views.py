from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import FoodItem, Order, OrderItem
from tables.models import Table
import json

@login_required
def food_selection(request):
    if 'selected_table_id' not in request.session:
        return redirect('tables:table_selection')
    
    table = Table.objects.get(id=request.session['selected_table_id'])
    
    # Get filter parameters
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    spicy_filter = request.GET.get('spicy', '')
    price_min = request.GET.get('price_min', 0)
    price_max = request.GET.get('price_max', 10000)
    
    # Build query
    foods = FoodItem.objects.all()
    
    if search_query:
        foods = foods.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        foods = foods.filter(category__name=category_filter)
    
    if spicy_filter:
        foods = foods.filter(is_spicy=True)
    
    foods = foods.filter(price__gte=price_min, price__lte=price_max)
    
    # Get popular items
    popular_items = FoodItem.objects.filter(is_popular=True)[:4]
    
    context = {
        'foods': foods,
        'popular_items': popular_items,
        'table': table,
    }
    
    return render(request, 'food/food_selection.html', context)

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        food_id = data.get('food_id')
        quantity = data.get('quantity', 1)
        
        # Store in session cart
        cart = request.session.get('cart', {})
        if str(food_id) in cart:
            cart[str(food_id)] += quantity
        else:
            cart[str(food_id)] = quantity
        
        request.session['cart'] = cart
        
        return JsonResponse({'success': True, 'cart_count': sum(cart.values())})
    
    return JsonResponse({'success': False})

@login_required
def checkout(request):
    if 'selected_table_id' not in request.session:
        return redirect('tables:table_selection')
    
    table = Table.objects.get(id=request.session['selected_table_id'])
    cart = request.session.get('cart', {})
    
    if not cart:
        return redirect('food:food_selection')
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        table=table
    )
    
    total = 0
    for food_id, quantity in cart.items():
        food_item = FoodItem.objects.get(id=int(food_id))
        OrderItem.objects.create(
            order=order,
            food_item=food_item,
            quantity=quantity,
            price=food_item.price
        )
        total += food_item.price * quantity
    
    order.total_amount = total
    order.save()
    
    # Clear cart
    request.session['cart'] = {}
    request.session['current_order_id'] = order.id
    
    return redirect('payment:payment_options')