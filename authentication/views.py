from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from .models import CustomerProfile

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Check if user is admin/staff
                if user.is_staff or user.is_superuser:
                    return redirect('admin_panel:dashboard')
                else:
                    return redirect('tables:table_selection')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            CustomerProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number', '')
            )
            login(request, user)
            
            # Regular users go to table selection
            # (New users created through registration are not admin)
            return redirect('tables:table_selection')
    else:
        form = CustomUserCreationForm()
    return render(request, 'authentication/register.html', {'form': form})
