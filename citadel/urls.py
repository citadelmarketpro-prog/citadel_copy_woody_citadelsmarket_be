import sys
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect, render
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Citadels Market Administration"
admin.site.site_title = "Citadels Market Admin Portal"
admin.site.index_title = "Welcome to Citadels Market Admin Portal"

def home(request):
    return redirect("dashboard:dashboard")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home),
    path("api/", include("app.urls")),
    path("dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# ── Custom error handlers ──

def handler404_view(request, exception=None):
    return render(request, '404.html', {
        'path': request.path,
        'exception': str(exception) if exception else 'The page you requested could not be found.',
    }, status=404)

def handler500_view(request):
    exc_type, exc_value, _ = sys.exc_info()
    return render(request, '500.html', {
        'error_type': exc_type.__name__ if exc_type else 'ServerError',
        'error_message': str(exc_value) if exc_value else 'An unexpected server error occurred.',
    }, status=500)

def handler403_view(request, exception=None):
    return render(request, '403.html', {
        'path': request.path,
        'exception': str(exception) if exception else 'You do not have permission to access this page.',
    }, status=403)

def handler400_view(request, exception=None):
    return render(request, '400.html', {
        'path': request.path,
        'exception': str(exception) if exception else 'The server could not understand your request.',
    }, status=400)

handler404 = handler404_view
handler500 = handler500_view
handler403 = handler403_view
handler400 = handler400_view