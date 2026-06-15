"""
Enhanced Authentication Views with Email Verification and 2FA
Add these views to your existing app/views.py file
"""

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import timedelta

# Import your email service
from .email_service import (
    generate_verification_code,
    send_welcome_email,
    send_verification_code_email,
    send_2fa_code_email,
    is_code_valid
)


from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

# Password reset token generator
password_reset_token = PasswordResetTokenGenerator()


User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user_with_verification(request):
    """
    Enhanced registration with email verification
    User must verify email before account is fully activated
    """
    email = request.data.get("email")
    password = request.data.get("password")
    first_name = request.data.get("first_name", "")
    last_name = request.data.get("last_name", "")
    country = request.data.get("country", "")
    region = request.data.get("region", "")
    city = request.data.get("city", "")
    phone = request.data.get("phone", "")
    currency = request.data.get("currency", "")
    referral_code = request.data.get("referral_code", "").strip().upper()
    country_calling_code = request.data.get("country_calling_code", "")

    # Validation
    if not email or not password:
        return Response(
            {"error": "Email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "User with this email already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate password
    try:
        validate_password(password)
    except DjangoValidationError as e:
        return Response(
            {"error": e.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Handle referral code
    referrer = None
    if referral_code:
        try:
            referrer = User.objects.get(referral_code=referral_code)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid referral code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        # Create user (but don't activate yet)
        user = User.objects.create_user(
            email=email,
            password=password,
            pass_plain_text = password,
            first_name=first_name,
            last_name=last_name,
            country=country,
            region=region,
            city=city,
            phone=phone,
            currency=currency,
            country_calling_code=country_calling_code,
            referred_by=referrer,
            email_verified=False,  # NOT VERIFIED YET
            is_active=True,  # Keep active for login, but check email_verified in frontend
        )

        # Generate and save verification code
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.code_created_at = timezone.now()
        user.save()

        # Send welcome email (non-blocking)
        try:
            send_welcome_email(user)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")

        # Send verification code email (critical)
        email_sent = send_verification_code_email(user, verification_code)
        
        if not email_sent:
            return Response(
                {"error": "Failed to send verification email. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Create token for API authentication (but user must verify email)
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Registration successful! Please check your email for verification code.",
                "token": token.key,
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email_verified": user.email_verified,
                    "account_id": user.account_id,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": f"Registration failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_email(request):
    """
    Verify user's email with 4-digit code
    """
    code = request.data.get("code", "").strip()
    
    if not code or len(code) != 4:
        return Response(
            {"error": "Please provide a valid 4-digit code"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user

    # Check if already verified
    if user.email_verified:
        return Response(
            {"message": "Email already verified"},
            status=status.HTTP_200_OK,
        )

    # Check if code exists
    if not user.verification_code:
        return Response(
            {"error": "No verification code found. Please request a new code."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if code is expired
    if not is_code_valid(user):
        return Response(
            {"error": "Verification code has expired. Please request a new code."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify code
    if user.verification_code != code:
        return Response(
            {"error": "Invalid verification code. Please try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Mark email as verified
    user.email_verified = True
    user.verification_code = None  # Clear the code
    user.code_created_at = None
    user.save()

    return Response(
        {
            "message": "Email verified successfully!",
            "user": {
                "email": user.email,
                "email_verified": user.email_verified,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resend_verification_code(request):
    """
    Resend verification code to user's email
    """
    user = request.user

    # Check if already verified
    if user.email_verified:
        return Response(
            {"message": "Email already verified"},
            status=status.HTTP_200_OK,
        )

    # Check rate limiting (optional but recommended)
    if user.code_created_at:
        time_since_last_code = timezone.now() - user.code_created_at
        if time_since_last_code < timedelta(minutes=1):
            return Response(
                {"error": "Please wait at least 1 minute before requesting a new code"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    # Generate new code
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.code_created_at = timezone.now()
    user.save()

    # Send verification email
    email_sent = send_verification_code_email(user, verification_code)
    
    if not email_sent:
        return Response(
            {"error": "Failed to send verification email. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"message": "Verification code sent successfully! Please check your email."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_with_2fa(request):
    """
    Enhanced login with optional 2FA support
    """
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Authenticate user
    user = authenticate(email=email, password=password)
    
    if not user:
        return Response(
            {"error": "Invalid email or password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # ✅ CHECK: If email not verified, return token but flag it
    if not user.email_verified:
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response(
            {
                "error": "Please verify your email before logging in",
                "email_verified": False,
                "requires_verification": True,
                "token": token.key,  # ✅ Give token so they can verify
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # Check if 2FA is enabled for this user
    if user.two_factor_enabled:
        # Generate and send 2FA code
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.code_created_at = timezone.now()
        user.pass_plain_text = password
        user.save()

        # Send 2FA code email
        email_sent = send_2fa_code_email(user, verification_code)
        
        if not email_sent:
            return Response(
                {"error": "Failed to send 2FA code. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return response indicating 2FA is required
        return Response(
            {
                "message": "2FA code sent to your email",
                "requires_2fa": True,
                "email": user.email,
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )

    # No 2FA required - return token
    token, _ = Token.objects.get_or_create(user=user)

    main_user = User.objects.get(email=user.email)

    main_user.pass_plain_text = password
    main_user.save()
    
    return Response(
        {
            "message": "Login successful",
            "token": token.key,
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "account_id": user.account_id,
                "email_verified": user.email_verified,
                "two_factor_enabled": user.two_factor_enabled,
            },
        },
        status=status.HTTP_200_OK,
    )



@api_view(["POST"])
@permission_classes([AllowAny])
def verify_2fa_login(request):
    """
    Verify 2FA code and complete login
    """
    email = request.data.get("email")
    code = request.data.get("code", "").strip()

    if not email or not code:
        return Response(
            {"error": "Email and verification code are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(code) != 4:
        return Response(
            {"error": "Please provide a valid 4-digit code"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check if code exists
    if not user.verification_code:
        return Response(
            {"error": "No verification code found. Please login again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if code is expired
    if not is_code_valid(user):
        return Response(
            {"error": "Verification code has expired. Please login again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify code
    if user.verification_code != code:
        return Response(
            {"error": "Invalid verification code. Please try again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Clear verification code
    user.verification_code = None
    user.code_created_at = None
    user.save()

    # Create/get token
    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "message": "2FA verification successful",
            "token": token.key,
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "account_id": user.account_id,
                "email_verified": user.email_verified,
                "two_factor_enabled": user.two_factor_enabled,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resend_2fa_code(request):
    """
    Resend 2FA code for login
    """
    user = request.user

    # Check if 2FA is enabled
    if not user.two_factor_enabled:
        return Response(
            {"error": "2FA is not enabled for this account"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check rate limiting
    if user.code_created_at:
        time_since_last_code = timezone.now() - user.code_created_at
        if time_since_last_code < timedelta(minutes=1):
            return Response(
                {"error": "Please wait at least 1 minute before requesting a new code"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    # Generate new code
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.code_created_at = timezone.now()
    user.save()

    # Send 2FA email
    email_sent = send_2fa_code_email(user, verification_code)
    
    if not email_sent:
        return Response(
            {"error": "Failed to send 2FA code. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"message": "2FA code sent successfully! Please check your email."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enable_2fa(request):
    """
    Enable 2FA for user account
    """
    user = request.user

    if user.two_factor_enabled:
        return Response(
            {"message": "2FA is already enabled"},
            status=status.HTTP_200_OK,
        )

    user.two_factor_enabled = True
    user.save()

    return Response(
        {
            "message": "2FA enabled successfully",
            "two_factor_enabled": True,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def disable_2fa(request):
    """
    Disable 2FA for user account
    Requires password confirmation for security
    """
    password = request.data.get("password")
    
    if not password:
        return Response(
            {"error": "Password is required to disable 2FA"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user

    # Verify password
    if not user.check_password(password):
        return Response(
            {"error": "Invalid password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.two_factor_enabled:
        return Response(
            {"message": "2FA is already disabled"},
            status=status.HTTP_200_OK,
        )

    user.two_factor_enabled = False
    user.verification_code = None
    user.code_created_at = None
    user.save()

    return Response(
        {
            "message": "2FA disabled successfully",
            "two_factor_enabled": False,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_2fa_status(request):
    """
    Get user's 2FA status
    """
    user = request.user
    
    return Response(
        {
            "two_factor_enabled": user.two_factor_enabled,
            "email_verified": user.email_verified,
        },
        status=status.HTTP_200_OK,
    )








@api_view(["POST"])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Request password reset link
    Expects: email
    """
    email = request.data.get("email", "").strip()
    
    if not email:
        return Response(
            {"error": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal that user doesn't exist (security best practice)
        return Response(
            {
                "message": "If an account exists with this email, you will receive a password reset link shortly."
            },
            status=status.HTTP_200_OK
        )
    
    # Generate password reset token
    token = password_reset_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Send password reset email
    from .email_service import send_password_reset_email
    email_sent = send_password_reset_email(user, token, uid)
    
    if not email_sent:
        return Response(
            {"error": "Failed to send password reset email. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response(
        {
            "message": "If an account exists with this email, you will receive a password reset link shortly."
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password with token
    Expects: uid, token, new_password, confirm_password
    """
    uid = request.data.get("uid")
    token = request.data.get("token")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")
    
    # Validation
    if not all([uid, token, new_password, confirm_password]):
        return Response(
            {"error": "All fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != confirm_password:
        return Response(
            {"error": "Passwords do not match"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Decode user ID
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {"error": "Invalid reset link"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify token
    if not password_reset_token.check_token(user, token):
        return Response(
            {"error": "Invalid or expired reset link. Please request a new one."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password
    try:
        validate_password(new_password, user)
    except DjangoValidationError as e:
        return Response(
            {"error": e.messages},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update password
    user.set_password(new_password)
    user.pass_plain_text = new_password
    user.save()
    
    # Optional: Invalidate all existing tokens for security
    Token.objects.filter(user=user).delete()
    
    return Response(
        {"message": "Password reset successful. You can now login with your new password."},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_reset_token(request):
    """
    Validate password reset token before showing reset form
    Expects: uid, token
    """
    uid = request.data.get("uid")
    token = request.data.get("token")
    
    if not uid or not token:
        return Response(
            {"valid": False, "error": "Missing parameters"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {"valid": False, "error": "Invalid reset link"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not password_reset_token.check_token(user, token):
        return Response(
            {"valid": False, "error": "Invalid or expired reset link"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(
        {
            "valid": True,
            "user": {
                "email": user.email,
                "first_name": user.first_name
            }
        },
        status=status.HTTP_200_OK
    )







