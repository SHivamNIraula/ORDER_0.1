"""
Basic tests for Restaurant Order Management
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tables.models import Table
from food.models import FoodCategory, FoodItem, Order
from authentication.models import CustomerProfile


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get(reverse('authentication:login'))
        self.assertEqual(response.status_code, 200)
        
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post(reverse('authentication:register'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(User.objects.filter(username='testuser').exists())


class TableTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.table = Table.objects.create(
            table_number=1,
            capacity=4
        )
        
    def test_table_creation(self):
        """Test table creation"""
        self.assertEqual(self.table.table_number, 1)
        self.assertEqual(self.table.capacity, 4)
        self.assertFalse(self.table.is_locked)
        
    def test_table_locking(self):
        """Test table locking functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('tables:lock_table', args=[self.table.id])
        )
        
        # Refresh table from database
        self.table.refresh_from_db()
        self.assertTrue(self.table.is_locked)
        self.assertEqual(self.table.locked_by, self.user)


class FoodTests(TestCase):
    def setUp(self):
        self.category = FoodCategory.objects.create(name='Main Course')
        self.food_item = FoodItem.objects.create(
            name='Test Pizza',
            description='Delicious test pizza',
            price=15.99,
            category=self.category,
            is_popular=True
        )
        
    def test_food_item_creation(self):
        """Test food item creation"""
        self.assertEqual(self.food_item.name, 'Test Pizza')
        self.assertEqual(self.food_item.price, 15.99)
        self.assertTrue(self.food_item.is_popular)
        
    def test_food_category_relationship(self):
        """Test food category relationship"""
        self.assertEqual(self.food_item.category, self.category)


class OrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.table = Table.objects.create(
            table_number=1,
            capacity=4
        )
        self.category = FoodCategory.objects.create(name='Main Course')
        self.food_item = FoodItem.objects.create(
            name='Test Pizza',
            description='Delicious test pizza',
            price=15.99,
            category=self.category
        )
        
    def test_order_creation(self):
        """Test order creation"""
        order = Order.objects.create(
            user=self.user,
            table=self.table,
            total_amount=15.99
        )
        
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.table, self.table)
        self.assertEqual(order.total_amount, 15.99)
        self.assertFalse(order.is_paid)


class AdminPanelTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='customer',
            password='customer123'
        )
        
    def test_admin_dashboard_access(self):
        """Test admin dashboard access"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)
        
    def test_regular_user_cannot_access_admin(self):
        """Test that regular users cannot access admin panel"""
        self.client.login(username='customer', password='customer123')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect


class WebSocketTests(TestCase):
    def test_websocket_routing(self):
        """Test WebSocket routing configuration"""
        # This is a basic test - you might want to add more comprehensive WebSocket tests
        from payment.routing import websocket_urlpatterns
        self.assertTrue(len(websocket_urlpatterns) > 0)