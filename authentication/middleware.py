
from django.shortcuts import redirect
from django.urls import reverse

class AdminPanelAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for admin_panel URLs
        if request.path.startswith('/admin-panel/'):
            # If user is not authenticated, redirect to login
            if not request.user.is_authenticated:
                return redirect('authentication:login')
            # If user is not staff/admin, redirect to table selection
            elif not (request.user.is_staff or request.user.is_superuser):
                return redirect('tables:table_selection')
        
        response = self.get_response(request)
        return response