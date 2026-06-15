from rest_framework.permissions import BasePermission

class IsEmailVerified(BasePermission):
    """
    Custom permission to only allow access to users with verified emails
    """
    message = "Please verify your email before accessing this resource."
    
    def has_permission(self, request, view):
        # Allow access only if user's email is verified
        return request.user and request.user.is_authenticated and request.user.email_verified
    

    