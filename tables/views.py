from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Table

@login_required
def table_selection(request):
    tables = Table.objects.all()
    return render(request, 'tables/table_selection.html', {'tables': tables})

@login_required
def lock_table(request, table_id):
    if request.method == 'POST':
        table = Table.objects.get(id=table_id)
        if not table.is_locked:
            table.is_locked = True
            table.locked_by = request.user
            table.locked_at = timezone.now()
            table.save()
            request.session['selected_table_id'] = table.id
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Table already locked'})
    return JsonResponse({'success': False})