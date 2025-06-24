"""
NUCLEAR SESSION FIX: Absolute session isolation
Replace authentication/middleware.py with this
"""

from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class AdminPanelAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # NUCLEAR OPTION: Complete session isolation for admin panel
        if request.path.startswith('/admin-panel/'):
            print(f"\n💥 NUCLEAR SESSION PROTECTION 💥")
            print(f"Path: {request.path}")
            print(f"Request session key: {request.session.session_key}")
            print(f"Request cookies: {request.COOKIES}")
            
            # STEP 1: Get session key from cookies (most reliable)
            session_key = None
            if 'sessionid' in request.COOKIES:
                session_key = request.COOKIES['sessionid']
                print(f"Session key from cookies: {session_key}")
            else:
                session_key = request.session.session_key
                print(f"Session key from request.session: {session_key}")
            
            # STEP 2: Force fresh session lookup from database
            if session_key:
                try:
                    # Get session directly from database
                    session_obj = Session.objects.get(session_key=session_key)
                    session_data = session_obj.get_decoded()
                    user_id = session_data.get('_auth_user_id')
                    
                    print(f"📊 Session from DB:")
                    print(f"  Session key: {session_key}")
                    print(f"  User ID: {user_id}")
                    print(f"  Session data: {session_data}")
                    
                    if user_id:
                        # Get user directly from database
                        user = User.objects.get(id=user_id)
                        print(f"👤 User from DB:")
                        print(f"  Username: {user.username}")
                        print(f"  ID: {user.id}")
                        print(f"  is_staff: {user.is_staff}")
                        print(f"  is_superuser: {user.is_superuser}")
                        
                        # NUCLEAR: Completely replace request.user
                        request.user = user
                        request.user.backend = 'django.contrib.auth.backends.ModelBackend'
                        
                        # NUCLEAR: Force update request.session
                        request.session._session_key = session_key
                        request.session._session_cache = session_data
                        
                        print(f"💥 NUCLEAR REPLACEMENT COMPLETE")
                        print(f"  Final user: {request.user.username}")
                        print(f"  Final is_staff: {request.user.is_staff}")
                        
                    else:
                        print(f"❌ No user_id in session")
                        request.user = None
                        
                except Session.DoesNotExist:
                    print(f"❌ Session {session_key} not found in DB")
                    request.user = None
                except User.DoesNotExist:
                    print(f"❌ User {user_id} not found in DB")
                    request.user = None
                except Exception as e:
                    print(f"❌ Nuclear session error: {e}")
                    request.user = None
            else:
                print(f"❌ No session key found")
                request.user = None
            
            print(f"💥 END NUCLEAR PROTECTION 💥\n")
        
        # Permission checks with detailed logging
        if request.path.startswith('/admin-panel/'):
            print(f"🔒 PERMISSION CHECK:")
            print(f"  User: {request.user}")
            print(f"  Authenticated: {getattr(request.user, 'is_authenticated', False)}")
            print(f"  Is staff: {getattr(request.user, 'is_staff', False)}")
            
            if not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
                print(f"❌ Authentication failed")
                if self.is_ajax(request):
                    return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
                else:
                    return redirect('authentication:login')
            
            elif not (request.user.is_staff or request.user.is_superuser):
                print(f"❌ Admin privileges required for {request.user.username}")
                if self.is_ajax(request):
                    return JsonResponse({'success': False, 'error': 'Admin privileges required'}, status=403)
                else:
                    return redirect('tables:table_selection')
            else:
                print(f"✅ Admin access granted to {request.user.username}")
        
        response = self.get_response(request)
        
        if request.path.startswith('/admin-panel/'):
            print(f"📤 Response status: {response.status_code}\n")
        
        return response
    
    def is_ajax(self, request):
        """Check if request is AJAX"""
        return (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                request.headers.get('Content-Type') == 'application/json' or 
                request.headers.get('Accept') == 'application/json')