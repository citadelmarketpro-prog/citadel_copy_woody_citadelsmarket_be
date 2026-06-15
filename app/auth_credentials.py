# auth.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token

class CookieTokenAuthentication(BaseAuthentication):
    """
    Custom authentication that reads token from HttpOnly cookie 'authToken'
    """
    def authenticate(self, request):
        token_key = request.COOKIES.get("authToken")
        if not token_key:
            return None  # No token provided → DRF will move to next auth class

        try:
            token = Token.objects.get(key=token_key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid or expired token")

        return (token.user, token)
