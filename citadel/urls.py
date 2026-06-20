from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

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

# Add this for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)