# dashboard/decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
        if not request.user.is_superuser:
            return redirect('dashboard:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view










