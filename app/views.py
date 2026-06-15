from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.decorators import (
    api_view, 
    permission_classes, 
    authentication_classes,
)
from collections import defaultdict
from django.utils import timezone
from .serializers import AdminWalletSerializer
from decimal import Decimal, InvalidOperation
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils.crypto import get_random_string

from cloudinary.uploader import upload_image
from cloudinary import CloudinaryImage

from django.db.models import Sum, Q, Count

from django.db import models

from .serializers import (
    TicketSerializer, 
    TransactionSerializer, 
    AdminWalletSerializer,
    AssetSerializer,
    NewsSerializer,
    NotificationSerializer,
    AdminWalletSerializer, 
    TransactionSerializer,
    TraderListSerializer, 
    TraderDetailSerializer, 
    TraderPortfolioSerializer,
    StockSerializer,
    StockListSerializer,
    UserStockPositionSerializer,
    TradeHistorySerializer,

    UserTraderCopySerializer, 
    UserTraderCopyCreateSerializer,

    WalletConnectionSerializer,
    WalletConnectionCreateSerializer,
    WalletConnectionListSerializer,

    # SIGNAL

    SignalListSerializer,
    SignalDetailSerializer,
    UserSignalPurchaseSerializer,
    SignalPurchaseCreateSerializer,
    UserCopyTraderHistorySerializer,
)


from .models import (
    Ticket, 
    Trader, 
    Transaction, 
    PaymentMethod, 
    AdminWallet,
    Asset,
    News,
    Notification,
    AdminWallet, 
    Transaction,
    Trader, 
    TraderPortfolio,
    Stock, 
    UserStockPosition,
    TradeHistory,
    WalletConnection,

    Signal,
    UserSignalPurchase,
    Transaction,
    UserTraderCopy,
    UserCopyTraderHistory,
    generate_unique_referral_code,
    Card,
)

from .email_service import (
    send_welcome_email,
    send_admin_deposit_notification,
    send_admin_withdrawal_notification,
    send_admin_deposit_intent_notification,
)

from .permissions import IsEmailVerified

import logging





logger = logging.getLogger(__name__)

User = get_user_model()


# Close trade functionality giving errors


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """
    Get all dashboard data for the authenticated user
    """
    user = request.user
    
    # Get all transactions
    from .models import Transaction
    transactions = user.transactions.all()
    
    # Calculate total deposits (completed only)
    total_deposits = transactions.filter(
        transaction_type='deposit',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate total withdrawals (completed only)
    total_withdrawals = transactions.filter(
        transaction_type='withdrawal',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get active portfolios
    from .models import Portfolio
    portfolios = user.portfolios.filter(is_active=True).values(
        'id', 'market', 'direction', 'invested', 'profit_loss', 
        'value', 'opened_at', 'is_active'
    )
    
    # Build response data
    data = {
        'email': user.email,
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'account_id': user.account_id or 'N/A',
        'currency': user.currency or 'USD',
        'balance': float(user.balance),
        'profit': float(user.profit),
        'current_loyalty_status': user.current_loyalty_status,
        'next_loyalty_status': user.next_loyalty_status,
        'next_amount_to_upgrade': user.next_amount_to_upgrade,
        'has_submitted_kyc': user.has_submitted_kyc,
        'is_verified': user.is_verified,
        'date_joined': user.date_joined.isoformat(),
        'total_deposits': float(total_deposits),
        'total_withdrawals': float(total_withdrawals),
        'portfolios': list(portfolios)
    }
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_transactions(request):
    """
    Get all transactions for the authenticated user
    """
    user = request.user
    transaction_type = request.query_params.get('type', None)
    
    from .models import Transaction
    transactions = user.transactions.all()
    
    # Filter by type if provided
    if transaction_type and transaction_type in ['deposit', 'withdrawal']:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    data = transactions.values(
        'id', 'transaction_type', 'amount', 'status', 
        'reference', 'description', 'created_at', 'updated_at'
    )
    
    return Response(list(data), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_portfolios(request):
    """
    Get all portfolios for the authenticated user
    """
    user = request.user
    active_only = request.query_params.get('active_only', 'true').lower() == 'true'
    
    from .models import Portfolio
    portfolios = user.portfolios.all()
    
    if active_only:
        portfolios = portfolios.filter(is_active=True)
    
    data = portfolios.values(
        'id', 'market', 'direction', 'invested', 'profit_loss', 
        'value', 'opened_at', 'is_active'
    )
    
    return Response(list(data), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """
    Get user statistics summary
    """
    user = request.user
    
    from .models import Transaction, Portfolio
    
    # Transaction stats
    completed_deposits = user.transactions.filter(
        transaction_type='deposit',
        status='completed'
    ).count()
    
    completed_withdrawals = user.transactions.filter(
        transaction_type='withdrawal',
        status='completed'
    ).count()
    
    # Portfolio stats
    active_portfolios = user.portfolios.filter(is_active=True).count()
    total_invested = user.portfolios.filter(is_active=True).aggregate(
        total=Sum('invested')
    )['total'] or 0
    
    data = {
        'total_deposits_count': completed_deposits,
        'total_withdrawals_count': completed_withdrawals,
        'active_portfolios_count': active_portfolios,
        'total_invested': float(total_invested),
        'balance': float(user.balance),
        'profit': float(user.profit),
    }
    
    return Response(data, status=status.HTTP_200_OK)



# @api_view(["GET"])
# @permission_classes([AllowAny])
# def validate_token(request):
#     auth_header = request.headers.get("Authorization")
    
#     if not auth_header or not auth_header.startswith("Token "):
#         return Response({"detail": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

#     token_key = auth_header.split(" ")[1]

#     try:
#         token = Token.objects.get(key=token_key)
#         user = token.user
#         return Response({"valid": True, "user": user.email}, status=status.HTTP_200_OK)
#     except Token.DoesNotExist:
#         return Response({"valid": False}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["GET"])
@permission_classes([AllowAny])
def validate_token(request):
    """
    Validate token and return user info including email verification status
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Token "):
        return Response(
            {"detail": "No token provided"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

    token_key = auth_header.split(" ")[1]

    try:
        token = Token.objects.get(key=token_key)
        user = token.user
        
        return Response(
            {
                "valid": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email_verified": user.email_verified,  # ✅ CRITICAL
                    "two_factor_enabled": user.two_factor_enabled,
                    "account_id": user.account_id,
                    "is_verified": user.is_verified,  # KYC verification
                    "has_submitted_kyc": user.has_submitted_kyc,
                }
            }, 
            status=status.HTTP_200_OK
        )
    except Token.DoesNotExist:
        return Response(
            {"valid": False, "detail": "Invalid token"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )







@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    """
    Simple registration without email verification
    Users get immediate access after signup
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

    try:
        validate_password(password)
    except DjangoValidationError as e:
        return Response(
            {"error": e.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

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
        # ✅ Create user with email_verified=True
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
            email_verified=True,
            is_active=True,
        )

        # ✅ Send welcome email synchronously (same as 2FA email)
        try:
            email_sent = send_welcome_email(user)
            
            if email_sent:
                logger.info(f"✅ Welcome email sent to {user.email}")
            else:
                logger.warning(f"⚠️ Failed to send welcome email to {user.email}")
        except Exception as e:
            logger.error(f"❌ Welcome email error for {user.email}: {str(e)}")
            # Don't fail registration if email fails
            pass

        # ✅ Create token immediately
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Registration successful!",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email_verified": True,
                    "account_id": user.account_id,
                    "referral_code": user.referral_code,
                    "country_calling_code": user.country_calling_code,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {"error": f"Registration failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    """
    Functional view to login a user
    """
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    


    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response(
            {"error": "Invalid email or password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)

    user.pass_plain_text = password
    user.save()

    return Response(
        {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "token": token.key,
        },
        status=status.HTTP_200_OK,
    )


# Tickets
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def ticket_list_create(request):
    if request.method == "GET":
        # Only show tickets belonging to logged-in user
        tickets = Ticket.objects.filter(user=request.user).order_by("-pk")
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        serializer = TicketSerializer(data=request.data)
        if serializer.is_valid():
            # auto-assign logged-in user
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_user_profile(request):
    user = request.user

    if request.method == "POST":
        data = request.data

        # update only the fields that are provided
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.dob = data.get("dob", user.dob)
        user.address = data.get("address", user.address)
        user.postal_code = data.get("postal_code", user.postal_code)
        user.country = data.get("country", user.country)
        user.city = data.get("city", user.city)
        user.region = data.get("region", user.region)

        user.save()

        return Response(
            {"message": "Profile updated successfully"},
            status=status.HTTP_200_OK,
        )
    elif request.method == "GET":
        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "balance": user.balance,
                    "account_id": user.account_id,
                    "dob": user.dob,
                    "address": user.address,
                    "postal_code": user.postal_code,
                    "country": user.country,
                    "city": user.city,
                    "region": user.region,
                    "country_calling_code": user.country_calling_code,  # ADD THIS
                    "is_verified": user.is_verified,
                    "has_submitted_kyc": user.has_submitted_kyc,
                }
            },
            status=status.HTTP_200_OK,
        )
    else:
        return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



# Change Password
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Allows authenticated users to change their password.
    Expects: old_password, new_password, confirm_password
    """
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    # Validate inputs
    if not old_password or not new_password or not confirm_password:
        return Response(
            {"error": "All fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.check_password(old_password):
        return Response(
            {"error": "Old password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if new_password != confirm_password:
        return Response(
            {"error": "New password and confirm password do not match"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Run Django’s password validators
    try:
        validate_password(new_password)
    except DjangoValidationError as e:
        return Response(
            {"error": e.messages},  # returns a list of validation messages
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 8:
        return Response(
            {"error": "New password must be at least 8 characters long"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Save new password
    user.set_password(new_password)
    user.pass_plain_text = new_password
    user.save()

    return Response(
        {"success": "Password changed successfully"},
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser]) # Handles file uploads
def upload_kyc(request):
    user = request.user

    # Get text field
    id_type = request.data.get("id_type")

    # Validate required fields
    if not id_type:
        return Response({"error": "ID type is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Handle file uploads
    id_front = request.FILES.get("id_front")
    id_back = request.FILES.get("id_back")

    if not id_front or not id_back:
        return Response({"error": "Both front and back ID images are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Save to user model
    user.id_type = id_type
    user.id_front = id_front
    user.id_back = id_back
    user.has_submitted_kyc = True
    user.save()

    return Response({
        "success": "KYC details uploaded successfully",
        "data": {
            "id_type": user.id_type,
            "id_front": str(user.id_front.url) if user.id_front else None,
            "id_back": str(user.id_back.url) if user.id_back else None,
        }
    }, status=status.HTTP_200_OK)





@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def withdrawal_view(request):
    """
    Handle user withdrawals.
    Expects: asset (balance, equity, user_funds, free_margin), amount
    """
    user = request.user
    asset = request.data.get("asset")
    amount = request.data.get("amount")

    valid_assets = ["balance", "equity", "user_funds", "free_margin"]

    if not asset or not amount:
        return Response(
            {"error": "Asset and amount are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if asset not in valid_assets:
        return Response(
            {"error": "Invalid asset type"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        amount = Decimal(amount)   # ✅ Use Decimal
    except (InvalidOperation, TypeError):
        return Response(
            {"error": "Amount must be a valid number"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if amount <= 0:
        return Response(
            {"error": "Amount must be greater than zero"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    available_balance = getattr(user, asset, Decimal("0.00"))

    if amount > available_balance:
        return Response(
            {"error": f"Insufficient {asset.replace('_', ' ')} balance"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create a unique reference
    reference = get_random_string(12)

    # Create withdrawal transaction (status pending by default)
    transaction = Transaction.objects.create(
        user=user,
        transaction_type="withdrawal",
        amount=amount,
        description=f"Withdrawal from {asset.replace('_', ' ')}",
        reference=reference,
        status="pending",
    )

    # ✅ If you want to immediately deduct from user balance:
    setattr(user, asset, available_balance - amount)
    user.save()

    return Response(
        {
            "message": "Withdrawal request submitted successfully",
            "transaction": {
                "id": transaction.id,
                "asset": asset,
                "amount": str(transaction.amount),  # ensure JSON serializable
                "status": transaction.status,
                "reference": transaction.reference,
                "created_at": transaction.created_at,
            },
        },
        status=status.HTTP_201_CREATED,
    )






@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def transaction_history(request):
    """
    Return all transactions belonging to the logged-in user.
    """
    user = request.user
    transactions = Transaction.objects.filter(user=user).order_by("-created_at")
    serializer = TransactionSerializer(transactions, many=True)

    return Response({"transactions": serializer.data}, status=status.HTTP_200_OK)




@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def payment_methods(request):
    if request.method == "POST":
        try:
            data = request.data
            method_type = data.get("method_type")

            if method_type not in dict(PaymentMethod.WALLET_CHOICES):
                return Response(
                    {"error": "Invalid payment method type"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update if exists, otherwise create
            payment, created = PaymentMethod.objects.update_or_create(
                user=request.user,
                method_type=method_type,
                defaults={
                    "address": data.get("address", ""),
                    "bank_name": data.get("bank_name", ""),
                    "bank_account_number": data.get("bank_account_number", ""),
                    "cashapp_id": data.get("cashapp_id", ""),
                    "paypal_email": data.get("paypal_email", ""),
                }
            )

            return Response({
                "message": "Payment method saved successfully" if created else "Payment method updated successfully",
                "id": payment.id,
                "method_type": payment.method_type,
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == "GET":
        try:
            payments = PaymentMethod.objects.filter(user=request.user)
            data = [
                {
                    "id": p.id,
                    "method_type": p.method_type,
                    "address": p.address,
                    "bank_name": p.bank_name,
                    "bank_account_number": p.bank_account_number,
                    "cashapp_id": p.cashapp_id,
                    "paypal_email": p.paypal_email,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                }
                for p in payments
            ]

            return Response({"payments": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




@api_view(["GET"])
@permission_classes([AllowAny])  # Anyone can view deposit options
def get_deposit_options(request):
    wallets = AdminWallet.objects.filter(is_active=True)
    serializer = AdminWalletSerializer(wallets, many=True)
    return Response( serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_deposit(request):
    """
    Handle deposit creation.
    Expects: currency, unit, amount, receipt (file)
    """
    user = request.user

    currency = request.data.get("currency")
    unit = request.data.get("unit")
    amount = request.data.get("amount")
    receipt = request.FILES.get("receipt")

    if not all([currency, unit, amount, receipt]):
        return Response(
            {"detail": "currency, unit, amount, and receipt are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        unit = Decimal(unit)
        amount = Decimal(amount)
    except Exception:
        return Response(
            {"detail": "unit and amount must be valid numbers."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Generate a unique reference
    reference = get_random_string(12)

    transaction = Transaction.objects.create(
        user=user,
        transaction_type="deposit",
        currency=currency,
        unit=unit,
        amount=amount,
        receipt=receipt,
        reference=reference,
        description=f"Deposit of {unit} {currency} (≈ {amount})",
        status="pending",
        created_at=timezone.now(),
    )

    return Response(
        {
            "id": transaction.id,
            "currency": transaction.currency,
            "unit": str(transaction.unit),
            "amount": str(transaction.amount),
            "status": transaction.status,
            "reference": transaction.reference,
            "receipt_url": str(transaction.receipt.url) if transaction.receipt else None,
        },
        status=status.HTTP_201_CREATED,
    )







from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Trader
from .serializers import TraderSerializer


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def trader_list_create(request):
    """
    GET: List all traders
    POST: Create a new trader
    """
    if request.method == "GET":
        traders = Trader.objects.all().order_by("-created_at")
        serializer = TraderSerializer(traders, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        serializer = TraderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
def trader_detail(request, pk):
    """
    GET: Retrieve a single trader by ID
    PUT/PATCH: Update trader
    DELETE: Delete trader
    """
    try:
        trader = Trader.objects.get(pk=pk)
    except Trader.DoesNotExist:
        return Response({"error": "Trader not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = TraderSerializer(trader)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method in ["PUT", "PATCH"]:
        serializer = TraderSerializer(trader, data=request.data, partial=(request.method == "PATCH"))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        trader.delete()
        return Response({"message": "Trader deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def copy_trader_action(request):
    """
    POST: Copy or cancel copying a trader - PERMANENT LOCK-IN
    """
    user = request.user
    
    serializer = UserTraderCopyCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    trader_id = serializer.validated_data['trader_id']
    action = serializer.validated_data['action']
    
    try:
        trader = Trader.objects.get(id=trader_id, is_active=True)
    except Trader.DoesNotExist:
        return Response(
            {"success": False, "error": "Trader not found or inactive"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    min_threshold = float(trader.min_account_threshold)
    user_balance = float(user.balance)
    
    if action == 'copy':
        # ✅ Validate user has sufficient balance (ONLY AT START)
        if user_balance < min_threshold:
            return Response(
                {
                    "success": False,
                    "error": f"Insufficient balance. Required: ${min_threshold:,.2f}, Your balance: ${user_balance:,.2f}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create copy relationship
        copy_relation, created = UserTraderCopy.objects.get_or_create(
            user=user,
            trader=trader,
            defaults={
                'is_actively_copying': True,
                'initial_investment_amount': min_threshold,
                'minimum_threshold_at_start': trader.min_account_threshold
            }
        )

        if not created:
            # Reactivate and always refresh the investment amount so P/L is correct
            copy_relation.is_actively_copying = True
            copy_relation.stopped_copying_at = None
            copy_relation.initial_investment_amount = min_threshold
            copy_relation.minimum_threshold_at_start = trader.min_account_threshold
            copy_relation.save(update_fields=[
                'is_actively_copying',
                'stopped_copying_at',
                'initial_investment_amount',
                'minimum_threshold_at_start',
            ])
            message = f"Resumed copying {trader.name}"
        else:
            message = f"Started copying {trader.name}"
        
        # Create notification
        Notification.objects.create(
            user=user,
            type="trade",
            title="Copy Trading Started",
            message=f"You are now copying {trader.name}",
            full_details=f"""
Trader: {trader.name}
Your Investment: ${min_threshold:,.2f}
Trader's Starting Capital: ${trader.min_account_threshold:,.2f}

You will receive trades proportional to your investment amount.
Note: You will remain locked in even if the trader's minimum threshold changes.
            """.strip()
        )
        
        return Response({
            "success": True,
            "message": message,
            "copy_relation": UserTraderCopySerializer(copy_relation).data
        }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    
    elif action == 'cancel':
        try:
            copy_relation = UserTraderCopy.objects.get(
                user=user,
                trader=trader,
                is_actively_copying=True
            )
        except UserTraderCopy.DoesNotExist:
            return Response(
                {"success": False, "error": "You are not actively copying this trader"},
                status=status.HTTP_404_NOT_FOUND
            )

        if copy_relation.cancel_requested:
            return Response(
                {"success": False, "error": "Cancel request already submitted. Awaiting admin review."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Submit cancel request — admin must approve or reject
        copy_relation.cancel_requested = True
        copy_relation.cancel_requested_at = timezone.now()
        copy_relation.save(update_fields=['cancel_requested', 'cancel_requested_at'])

        # Create notification
        Notification.objects.create(
            user=user,
            type="trade",
            title="Cancel Request Submitted",
            message=f"Your request to stop copying {trader.name} has been sent to admin for review.",
            full_details=f"Trader: {trader.name}\nRequested at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )

        return Response({
            "success": True,
            "message": f"Cancel request sent for {trader.name}. Awaiting admin approval.",
            "copy_relation": UserTraderCopySerializer(copy_relation).data
        }, status=status.HTTP_200_OK)

# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
# def copy_trader_action(request):
#     """
#     POST: Copy or cancel copying a trader
#     Expects:
#     - trader_id: ID of the trader
#     - action: 'copy' or 'cancel'
#     """
#     user = request.user
    
#     # Validate input
#     serializer = UserTraderCopyCreateSerializer(data=request.data)
#     if not serializer.is_valid():
#         return Response(
#             {
#                 "success": False,
#                 "errors": serializer.errors
#             },
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     trader_id = serializer.validated_data['trader_id']
#     action = serializer.validated_data['action']
    
#     # Get trader
#     try:
#         trader = Trader.objects.get(id=trader_id, is_active=True)
#     except Trader.DoesNotExist:
#         return Response(
#             {
#                 "success": False,
#                 "error": "Trader not found or inactive"
#             },
#             status=status.HTTP_404_NOT_FOUND
#         )
    
#     # Check user balance against minimum threshold
#     min_threshold = float(trader.min_account_threshold)
#     user_balance = float(user.balance)
    
#     if action == 'copy':
#         # Validate user has sufficient balance
#         if user_balance < min_threshold:
#             return Response(
#                 {
#                     "success": False,
#                     "error": f"Insufficient balance. Required: ${min_threshold:,.2f}, Your balance: ${user_balance:,.2f}"
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Get or create copy relationship
#         copy_relation, created = UserTraderCopy.objects.get_or_create(
#             user=user,
#             trader=trader,
#             defaults={
#                 'is_actively_copying': True,
#                 'minimum_amount_user_copied': trader.min_account_threshold
#             }
#         )
        
#         if not created:
#             # Update existing relationship
#             copy_relation.is_actively_copying = True
#             copy_relation.minimum_amount_user_copied = trader.min_account_threshold
#             copy_relation.stopped_copying_at = None
#             copy_relation.save()
#             message = f"Resumed copying {trader.name}"
#         else:
#             message = f"Started copying {trader.name}"
        
#         # Create notification
#         Notification.objects.create(
#             user=user,
#             type="trade",
#             title="Copy Trading Started",
#             message=f"You are now copying {trader.name}",
#             full_details=f"Trader: {trader.name}\nMinimum Balance: ${min_threshold:,.2f}\nYour Balance: ${user_balance:,.2f}",
#         )
        
#         return Response({
#             "success": True,
#             "message": message,
#             "copy_relation": UserTraderCopySerializer(copy_relation).data
#         }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    
#     elif action == 'cancel':
#         # Get copy relationship
#         try:
#             copy_relation = UserTraderCopy.objects.get(
#                 user=user,
#                 trader=trader
#             )
#         except UserTraderCopy.DoesNotExist:
#             return Response(
#                 {
#                     "success": False,
#                     "error": "You are not copying this trader"
#                 },
#                 status=status.HTTP_404_NOT_FOUND
#             )
        
#         # Stop copying
#         copy_relation.is_actively_copying = False
#         copy_relation.save()
        
#         # Create notification
#         Notification.objects.create(
#             user=user,
#             type="trade",
#             title="Copy Trading Stopped",
#             message=f"You have stopped copying {trader.name}",
#             full_details=f"Trader: {trader.name}\nStopped at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
#         )
        
#         return Response({
#             "success": True,
#             "message": f"Stopped copying {trader.name}",
#             "copy_relation": UserTraderCopySerializer(copy_relation).data
#         }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_user_copy_status(request, trader_id):
    """
    GET: Check if user is currently copying a specific trader
    """
    user = request.user
    
    try:
        copy_relation = UserTraderCopy.objects.get(
            user=user,
            trader_id=trader_id
        )
        return Response({
            "success": True,
            "is_copying": copy_relation.is_actively_copying,
            "cancel_requested": copy_relation.cancel_requested,
            "copy_relation": UserTraderCopySerializer(copy_relation).data
        }, status=status.HTTP_200_OK)
    except UserTraderCopy.DoesNotExist:
        return Response({
            "success": True,
            "is_copying": False,
            "cancel_requested": False,
            "copy_relation": None
        }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_user_copies(request):
    """
    GET: Get all traders the user is currently copying or has copied
    Query params:
    - active_only: Show only active copies (default: true)
    """
    user = request.user
    active_only = request.GET.get("active_only", "true").lower() == "true"
    
    copies = UserTraderCopy.objects.filter(user=user)
    
    if active_only:
        copies = copies.filter(is_actively_copying=True)
    
    serializer = UserTraderCopySerializer(copies, many=True)
    
    return Response({
        "success": True,
        "copies": serializer.data,
        "count": len(serializer.data)
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def asset_list(request):
    """
    Return a flat list of all assets.
    Example: GET /assets/
    """
    category = request.GET.get("category")
    if category:
        assets = Asset.objects.filter(category=category)
    else:
        assets = Asset.objects.all()
    
    serializer = AssetSerializer(assets, many=True)
    return Response(serializer.data)



@api_view(["GET"])
def grouped_assets(request):
    """
    Return assets grouped by category.
    Example: GET /assets/grouped/
    """
    assets = Asset.objects.all()
    serializer = AssetSerializer(assets, many=True)
    
    grouped = defaultdict(list)
    for asset in serializer.data:
        grouped[asset["category"]].append(asset)
    
    return Response(grouped)


# STARTER



# Add these views to your app/views.py file

@api_view(["GET"])
@permission_classes([AllowAny])
def news_list(request):
    """
    GET: List all news articles with optional filtering
    Query params:
    - category: Filter by category (optional)
    - search: Search in title and summary (optional)
    """
    news_queryset = News.objects.all()

    # Filter by category
    category = request.GET.get("category")
    if category and category != "All":
        news_queryset = news_queryset.filter(category=category)

    # Search functionality
    search = request.GET.get("search")
    if search:
        from django.db.models import Q
        news_queryset = news_queryset.filter(
            Q(title__icontains=search) | 
            Q(summary__icontains=search) |
            Q(content__icontains=search)
        )

    serializer = NewsSerializer(news_queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def news_detail(request, pk):
    """
    GET: Retrieve a single news article by ID
    """
    try:
        news = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response(
            {"error": "News article not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = NewsSerializer(news)
    return Response(serializer.data, status=status.HTTP_200_OK)


# REPLACE your existing trader views in app/views.py with these:

# @api_view(["GET"])
# @permission_classes([AllowAny])
# def trader_list(request):
#     """
#     GET: List all traders with optional filtering
#     Query params:
#     - search: Search in name and username
#     - badge: Filter by badge (gold, silver, bronze)
#     - min_gain: Filter by minimum gain percentage
#     - max_risk: Filter by maximum risk level
#     """
#     traders = Trader.objects.filter(is_active=True)

#     # Search functionality
#     search = request.GET.get("search")
#     if search:
#         from django.db.models import Q
#         traders = traders.filter(
#             Q(name__icontains=search) | 
#             Q(username__icontains=search)
#         )

#     # Filter by badge
#     badge = request.GET.get("badge")
#     if badge:
#         traders = traders.filter(badge=badge)
    
#     # Filter by minimum gain
#     min_gain = request.GET.get("min_gain")
#     if min_gain:
#         try:
#             traders = traders.filter(gain__gte=float(min_gain))
#         except ValueError:
#             pass
    
#     # Filter by maximum risk
#     max_risk = request.GET.get("max_risk")
#     if max_risk:
#         try:
#             traders = traders.filter(risk__lte=int(max_risk))
#         except ValueError:
#             pass

#     serializer = TraderListSerializer(traders, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)




@api_view(["GET"])
@permission_classes([AllowAny])
def trader_list(request):
    """
    GET: List all traders with optional filtering
    """
    traders = Trader.objects.filter(is_active=True)

    # Search functionality
    search = request.GET.get("search")
    if search:
        from django.db.models import Q
        traders = traders.filter(
            Q(name__icontains=search) | 
            Q(username__icontains=search)
        )

    serializer = TraderListSerializer(traders, many=True)
    
    # ✅ Ensure images have full URLs
    data = serializer.data
    for trader in data:
        # Make sure avatar URL is complete
        if trader.get('avatar') and not trader['avatar'].startswith('http'):
            trader['avatar'] = None
        # Make sure country_flag URL is complete  
        if trader.get('country_flag') and not trader['country_flag'].startswith('http'):
            trader['country_flag'] = None
    
    return Response(data, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([AllowAny])
def trader_detail(request, pk):
    """
    GET: Retrieve a single trader by ID with full details
    """
    try:
        trader = Trader.objects.get(pk=pk, is_active=True)
    except Trader.DoesNotExist:
        return Response(
            {"error": "Trader not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = TraderDetailSerializer(trader)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def trader_portfolios(request, trader_id):
    """
    GET: Get all active portfolio positions for a specific trader
    """
    try:
        trader = Trader.objects.get(pk=trader_id, is_active=True)
    except Trader.DoesNotExist:
        return Response(
            {"error": "Trader not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    portfolios = TraderPortfolio.objects.filter(trader=trader, is_active=True)
    serializer = TraderPortfolioSerializer(portfolios, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """
    GET: List all notifications for the authenticated user
    Query params:
    - type: Filter by notification type (trade, deposit, withdrawal, alert, system, news)
    - read: Filter by read status (true/false)
    - priority: Filter by priority (low, medium, high)
    """
    notifications = Notification.objects.filter(user=request.user)
    
    # Filter by type
    notification_type = request.GET.get("type")
    if notification_type:
        notifications = notifications.filter(type=notification_type)
    
    # Filter by read status
    read_status = request.GET.get("read")
    if read_status:
        is_read = read_status.lower() == "true"
        notifications = notifications.filter(read=is_read)
    
    # Filter by priority
    # priority = request.GET.get("priority")
    # if priority:
    #     notifications = notifications.filter(priority=priority)
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_detail(request, pk):
    """
    GET: Retrieve a single notification by ID
    """
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """
    PATCH: Mark a notification as read
    """
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    notification.read = True
    notification.save()
    
    serializer = NotificationSerializer(notification)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """
    POST: Mark all notifications as read for the authenticated user
    """
    updated_count = Notification.objects.filter(
        user=request.user, 
        read=False
    ).update(read=True)
    
    return Response(
        {
            "message": f"Marked {updated_count} notifications as read",
            "count": updated_count
        }, 
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_notification_count(request):
    """
    GET: Get count of unread notifications for the authenticated user
    """
    count = Notification.objects.filter(user=request.user, read=False).count()
    
    return Response(
        {"unread_count": count}, 
        status=status.HTTP_200_OK
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    """
    DELETE: Delete a notification
    """
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    notification.delete()
    return Response(
        {"message": "Notification deleted successfully"}, 
        status=status.HTTP_200_OK
    )

# UPDATED SETTINGS VIEWS - Replace the previous versions in your views.py

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_user_settings(request):
    """
    GET: Retrieve complete user settings including profile, security, and payment info
    """
    user = request.user
    
    # Get payment methods
    payment_methods_qs = PaymentMethod.objects.filter(user=user)
    
    # Organize payment methods by type
    btc_method = payment_methods_qs.filter(method_type="BTC").first()
    eth_method = payment_methods_qs.filter(method_type="ETH").first()
    # Check for both USDT types
    usdt_method = payment_methods_qs.filter(method_type__in=["USDT_ERC20", "USDT_TRC20"]).first()
    
    return Response({
        "profile": {
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "email": user.email,
            "phone": user.phone or "",
            "country": user.country or "",
            "region": user.region or "",
            "city": user.city or "",
            "account_id": user.account_id or "",
            "is_verified": user.is_verified,
            "account_status": "Verified" if user.is_verified else "Unverified",
        },
        "payment_methods": {
            "btc": {
                "address": btc_method.address if btc_method else "",
                "has_method": bool(btc_method),
            },
            "eth": {
                "address": eth_method.address if eth_method else "",
                "network": "ERC20",
                "has_method": bool(eth_method),
            },
            "usdt": {
                "address": usdt_method.address if usdt_method else "",
                "network": "TRC20" if usdt_method and usdt_method.method_type == "USDT_TRC20" else "ERC20",
                "method_type": usdt_method.method_type if usdt_method else "USDT_TRC20",
                "has_method": bool(usdt_method),
            },
        }
    }, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_profile(request):
    """
    PATCH: Update user profile information (name, phone, country)
    Expects: first_name, last_name, phone, country (all optional)
    """
    user = request.user
    
    # Get data from request
    first_name = request.data.get("first_name")
    last_name = request.data.get("last_name")
    phone = request.data.get("phone")
    country = request.data.get("country")
    
    # Update only provided fields
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if phone is not None:
        user.phone = phone
    if country is not None:
        user.country = country
    
    user.save()
    
    return Response({
        "message": "Profile updated successfully",
        "profile": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "country": user.country,
        }
    }, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_payment_method(request):
    """
    PATCH: Update or create a payment method
    Expects: method_type (BTC, ETH, SOL, USDT_ERC20, USDT_TRC20), address
    """
    user = request.user
    
    method_type = request.data.get("method_type")
    address = request.data.get("address")
    
    # Validate inputs
    if not method_type or not address:
        return Response(
            {"error": "method_type and address are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate method_type - must match model choices
    valid_crypto_methods = ["BTC", "ETH", "SOL", "USDT_ERC20", "USDT_TRC20"]
    if method_type not in valid_crypto_methods:
        return Response(
            {"error": f"Invalid method_type. Must be one of: {', '.join(valid_crypto_methods)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate address is not empty
    if not address.strip():
        return Response(
            {"error": "Address cannot be empty"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # For USDT, delete the other USDT type if it exists (can only have one USDT address)
    if method_type in ["USDT_ERC20", "USDT_TRC20"]:
        other_usdt = "USDT_TRC20" if method_type == "USDT_ERC20" else "USDT_ERC20"
        PaymentMethod.objects.filter(user=user, method_type=other_usdt).delete()
    
    # Update or create payment method
    payment_method, created = PaymentMethod.objects.update_or_create(
        user=user,
        method_type=method_type,
        defaults={"address": address}
    )
    
    return Response({
        "message": f"{method_type.replace('_', ' ')} address {'added' if created else 'updated'} successfully",
        "payment_method": {
            "method_type": payment_method.method_type,
            "address": payment_method.address,
            "created": created,
        }
    }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def change_user_password(request):
    """
    POST: Change user password
    Expects: old_password, new_password, confirm_password
    """
    user = request.user
    
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")
    
    # Validate inputs
    if not old_password or not new_password or not confirm_password:
        return Response(
            {"error": "All fields are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check old password
    if not user.check_password(old_password):
        return Response(
            {"error": "Current password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check new passwords match
    if new_password != confirm_password:
        return Response(
            {"error": "New password and confirm password do not match"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new password
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
    
    return Response(
        {"message": "Password changed successfully"},
        status=status.HTTP_200_OK
    )


# ADD THESE UPDATED VIEWS TO YOUR app/views.py

@api_view(["GET"])
@permission_classes([AllowAny])
def get_active_deposit_options(request):
    """
    GET: Retrieve all active admin wallets for deposit options
    Returns: List of active wallets with currency, amount (rate), wallet_address, and qr_code
    """
    try:
        wallets = AdminWallet.objects.filter(is_active=True).order_by('currency')
        serializer = AdminWalletSerializer(wallets, many=True)
        return Response({
            "success": True,
            "wallets": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_deposit_transaction(request):
    """
    POST: Create a new deposit transaction
    Expects:
    - currency: The cryptocurrency type (e.g., "BTC", "ETH")
    - dollar_amount: The dollar amount user wants to deposit
    - currency_unit: The calculated amount of cryptocurrency units
    - receipt: Image file of payment receipt
    
    Returns: Created transaction details
    """
    user = request.user

    # Extract data from request
    currency = request.data.get("currency")
    dollar_amount = request.data.get("dollar_amount")
    currency_unit = request.data.get("currency_unit")
    receipt = request.FILES.get("receipt")

    # Validation
    if not all([currency, dollar_amount, currency_unit, receipt]):
        return Response(
            {
                "success": False,
                "error": "currency, dollar_amount, currency_unit, and receipt are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate wallet exists and is active
    try:
        wallet = AdminWallet.objects.get(currency=currency, is_active=True)
    except AdminWallet.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": f"No active wallet found for {currency}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Convert to Decimal for precision
    try:
        dollar_amount = Decimal(str(dollar_amount))
        currency_unit = Decimal(str(currency_unit))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid amount values provided"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate amounts are positive
    if dollar_amount <= 0 or currency_unit <= 0:
        return Response(
            {
                "success": False,
                "error": "Amounts must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Generate unique reference
    reference = f"DEP-{get_random_string(12).upper()}"

    # Create transaction
    try:
        transaction = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            currency=currency,
            unit=currency_unit,
            amount=dollar_amount,
            receipt=receipt,
            reference=reference,
            description=f"Deposit of {currency_unit} {currency} (≈ ${dollar_amount})",
            status="pending",
            created_at=timezone.now(),
        )

        return Response(
            {
                "success": True,
                "message": "Deposit request submitted successfully",
                "transaction": {
                    "id": transaction.id,
                    "reference": transaction.reference,
                    "currency": transaction.currency,
                    "unit": str(transaction.unit),
                    "amount": str(transaction.amount),
                    "status": transaction.status,
                    "receipt_url": transaction.receipt.url if transaction.receipt else None,
                    "created_at": transaction.created_at.isoformat(),
                }
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response(
            {
                "success": False,
                "error": f"Failed to create transaction: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_deposit_history(request):
    """
    GET: Retrieve deposit transaction history for authenticated user
    Query params:
    - limit: Number of transactions to return (default: 10)
    """
    user = request.user
    limit = request.GET.get("limit", 10)
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    try:
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type="deposit"
        ).order_by("-created_at")[:limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            "success": True,
            "transactions": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_user_profile_for_withdrawal(request):
    """
    GET: Retrieve authenticated user's profile with balance and other info
    Returns: User profile data including balance
    """
    user = request.user
    
    return Response({
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
            "account_id": user.account_id,
            "balance": str(user.balance),
            "formatted_balance": f"${user.balance:,.2f}",
            "country": user.country or "",
            "phone": user.phone or "",
            "is_verified": user.is_verified,
            "has_submitted_kyc": user.has_submitted_kyc,
        }
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_withdrawal_methods(request):
    """
    GET: Retrieve all available withdrawal methods for the user
    Returns: List of payment methods the user has set up with their addresses
    """
    user = request.user
    
    try:
        payment_methods = PaymentMethod.objects.filter(user=user)
        
        # Format the response
        methods = []
        for pm in payment_methods:
            # Only include crypto methods with addresses
            if pm.method_type in ["BTC", "ETH", "SOL", "USDT_ERC20", "USDT_TRC20", "BNB", "TRX", "XRP", "LTC", "BUSD"] and pm.address:
                # Simplify the display name
                display_name = pm.method_type.replace("_ERC20", "").replace("_TRC20", "")
                
                method_data = {
                    "id": pm.id,
                    "method_type": pm.method_type,
                    "display_name": display_name,
                    "address": pm.address,
                }
                methods.append(method_data)
        
        return Response({
            "success": True,
            "methods": methods,
            "count": len(methods)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_withdrawal_request(request):
    """
    POST: Create a new withdrawal request
    Expects:
    - method_type: The withdrawal method (BTC, ETH, USDT_ERC20, etc.)
    - amount: The amount to withdraw (in USD)
    - withdrawal_address: The address to send funds to
    
    Returns: Created transaction details
    """
    user = request.user
    
    # Extract data from request
    method_type = request.data.get("method_type")
    amount = request.data.get("amount")
    withdrawal_address = request.data.get("withdrawal_address")
    
    # Validation
    if not all([method_type, amount, withdrawal_address]):
        return Response(
            {
                "success": False,
                "error": "method_type, amount, and withdrawal_address are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Validate payment method exists for user
    try:
        payment_method = PaymentMethod.objects.get(
            user=user,
            method_type=method_type
        )
    except PaymentMethod.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": f"No payment method found for {method_type}. Please add this method in settings first."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Convert to Decimal for precision
    try:
        amount = Decimal(str(amount))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid amount value provided"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Validate amount is positive
    if amount <= 0:
        return Response(
            {
                "success": False,
                "error": "Amount must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Check if user has sufficient balance
    if amount > user.balance:
        return Response(
            {
                "success": False,
                "error": f"Insufficient balance. Your balance is ${user.balance:,.2f}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Verify withdrawal address matches the one on file (security check)
    if payment_method.address != withdrawal_address:
        return Response(
            {
                "success": False,
                "error": "Withdrawal address does not match your saved address. Please update your payment method in settings first."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Check if user is verified (optional security check)
    if not user.is_verified and amount > 1000:  # Example: require verification for amounts over $1000
        return Response(
            {
                "success": False,
                "error": "Account verification required for withdrawals over $1,000. Please complete KYC verification."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Generate unique reference
    reference = f"WTH-{get_random_string(12).upper()}"
    
    # Create transaction
    try:
        transaction = Transaction.objects.create(
            user=user,
            transaction_type="withdrawal",
            currency=method_type.replace("_ERC20", "").replace("_TRC20", ""),  # Simplify currency name
            unit=amount,  # For withdrawals, unit can be same as amount
            amount=amount,
            reference=reference,
            description=f"Withdrawal of ${amount} via {method_type} to {withdrawal_address[:20]}...",
            status="pending",
            created_at=timezone.now(),
        )
        
        # Deduct from user balance immediately (pending admin approval)
        # NOTE: In production, you might want to hold this in a separate field until admin approval
        user.balance -= amount
        user.save()


        # ✅ NEW: Send admin notification email
        try:
            email_sent = send_admin_withdrawal_notification(user, transaction, payment_method)
            
            if email_sent:
                logger.info(f"✅ Admin notified of withdrawal from {user.email}")
            else:
                logger.warning(f"⚠️ Failed to notify admin of withdrawal from {user.email}")
        except Exception as e:
            logger.error(f"❌ Admin withdrawal notification error: {str(e)}")
            # Don't fail the transaction if email fails
            pass
        
        return Response(
            {
                "success": True,
                "message": "Withdrawal request submitted successfully and is pending approval",
                "transaction": {
                    "id": transaction.id,
                    "reference": transaction.reference,
                    "method": method_type,
                    "currency": transaction.currency,
                    "amount": str(transaction.amount),
                    "status": transaction.status,
                    "withdrawal_address": withdrawal_address,
                    "created_at": transaction.created_at.isoformat(),
                    "new_balance": str(user.balance),
                    "formatted_new_balance": f"${user.balance:,.2f}",
                }
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response(
            {
                "success": False,
                "error": f"Failed to create withdrawal: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_withdrawal_history(request):
    """
    GET: Retrieve withdrawal transaction history for authenticated user
    Query params:
    - limit: Number of transactions to return (default: 10)
    """
    user = request.user
    limit = request.GET.get("limit", 10)
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    try:
        transactions = Transaction.objects.filter(
            user=user,
            transaction_type="withdrawal"
        ).order_by("-created_at")[:limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            "success": True,
            "transactions": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# ADD THIS NEW VIEW TO YOUR views.py FILE (after get_withdrawal_history function)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_transaction_history(request):
    """
    GET: Retrieve all transaction history (deposits + withdrawals) for authenticated user
    Query params:
    - limit: Number of transactions to return (default: 10)
    - type: Filter by transaction type (deposit/withdrawal) - optional
    """
    user = request.user
    limit = request.GET.get("limit", 10)
    transaction_type = request.GET.get("type", None)
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    try:
        # Get all transactions for user
        transactions = Transaction.objects.filter(user=user)
        
        # Filter by type if provided
        if transaction_type and transaction_type in ['deposit', 'withdrawal']:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Order by most recent and limit
        transactions = transactions.order_by("-created_at")[:limit]
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            "success": True,
            "transactions": serializer.data,
            "count": len(serializer.data)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Stocks
@api_view(["GET"])
@permission_classes([AllowAny])
def stock_list(request):
    """
    GET: List all active stocks with optional filtering
    Query params:
    - search: Search in symbol and name
    - sector: Filter by sector
    - featured: Show only featured stocks (true/false)
    - limit: Limit number of results
    """
    stocks = Stock.objects.filter(is_active=True)
    
    # Search functionality
    search = request.GET.get("search")
    if search:
        from django.db.models import Q
        stocks = stocks.filter(
            Q(symbol__icontains=search) | 
            Q(name__icontains=search)
        )
    
    # Filter by sector
    sector = request.GET.get("sector")
    if sector:
        stocks = stocks.filter(sector=sector)
    
    # Filter by featured
    featured = request.GET.get("featured")
    if featured and featured.lower() == "true":
        stocks = stocks.filter(is_featured=True)
    
    # Limit results
    limit = request.GET.get("limit")
    if limit:
        try:
            stocks = stocks[:int(limit)]
        except ValueError:
            pass
    
    serializer = StockListSerializer(stocks, many=True)
    
    return Response({
        "success": True,
        "count": len(serializer.data),
        "stocks": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def stock_detail(request, symbol):
    """
    GET: Retrieve a single stock by symbol
    """
    try:
        stock = Stock.objects.get(symbol=symbol.upper(), is_active=True)
    except Stock.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Stock not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = StockSerializer(stock)
    
    # If user is authenticated, include their position in this stock
    user_position = None
    if request.user.is_authenticated:
        try:
            position = UserStockPosition.objects.get(
                user=request.user,
                stock=stock,
                is_active=True
            )
            user_position = UserStockPositionSerializer(position).data
        except UserStockPosition.DoesNotExist:
            pass
    
    return Response({
        "success": True,
        "stock": serializer.data,
        "user_position": user_position
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def stock_sectors(request):
    """
    GET: Get list of unique sectors
    """
    sectors = Stock.objects.filter(
        is_active=True,
        sector__isnull=False
    ).values_list('sector', flat=True).distinct().order_by('sector')
    
    return Response({
        "success": True,
        "sectors": list(sectors)
    }, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_stock_positions(request):
    """
    GET: Get all stock positions for authenticated user
    Query params:
    - active_only: Show only active positions (default: true)
    """
    active_only = request.GET.get("active_only", "true").lower() == "true"
    
    positions = UserStockPosition.objects.filter(user=request.user)
    
    if active_only:
        positions = positions.filter(is_active=True)
    
    serializer = UserStockPositionSerializer(positions, many=True)
    
    # Calculate totals - FIX: Ensure all values are Decimal
    total_invested = Decimal('0.00')
    total_current_value = Decimal('0.00')
    
    for p in positions:
        if p.is_active:
            total_invested += Decimal(str(p.total_invested))
            total_current_value += Decimal(str(p.current_value))
    
    total_profit_loss = total_current_value - total_invested
    total_profit_loss_percent = (
        (total_profit_loss / total_invested * 100) if total_invested > 0 else Decimal('0.00')
    )
    
    return Response({
        "success": True,
        "positions": serializer.data,
        "summary": {
            "total_invested": str(total_invested),
            "total_current_value": str(total_current_value),
            "total_profit_loss": str(total_profit_loss),
            "total_profit_loss_percent": str(total_profit_loss_percent)
        }
    }, status=status.HTTP_200_OK)


    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def buy_stock(request):
    """
    POST: Buy stock shares
    Expects: symbol, shares, order_type
    """
    user = request.user
    symbol = request.data.get("symbol")
    shares_str = request.data.get("shares")
    order_type = request.data.get("order_type", "Market Buy")
    
    # Validation
    if not symbol or not shares_str:
        return Response(
            {
                "success": False,
                "error": "Symbol and shares are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        shares = Decimal(str(shares_str))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid shares value"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if shares <= 0:
        return Response(
            {
                "success": False,
                "error": "Shares must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get stock
    try:
        stock = Stock.objects.get(symbol=symbol.upper(), is_active=True)
    except Stock.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Stock not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculate cost
    total_cost = shares * stock.price
    
    # Check balance
    if user.balance < total_cost:
        return Response(
            {
                "success": False,
                "error": f"Insufficient balance. Required: ${total_cost:.2f}, Available: ${user.balance:.2f}"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create position
    position, created = UserStockPosition.objects.get_or_create(
        user=user,
        stock=stock,
        is_active=True,
        defaults={
            'shares': shares,
            'average_buy_price': stock.price,
            'total_invested': total_cost
        }
    )
    
    if not created:
        # Update existing position
        old_total = position.total_invested
        old_shares = position.shares
        new_total = old_total + total_cost
        new_shares = old_shares + shares
        position.average_buy_price = new_total / new_shares
        position.shares = new_shares
        position.total_invested = new_total
        position.save()
    
    # Deduct from balance
    user.balance -= total_cost
    user.save()
    
    # Create transaction record
    reference = f"BUY-{get_random_string(12).upper()}"
    Transaction.objects.create(
        user=user,
        transaction_type="withdrawal",  # Buying is a withdrawal from balance
        amount=total_cost,
        reference=reference,
        description=f"Bought {shares} shares of {stock.symbol} @ ${stock.price}",
        status="completed"
    )

    # After successful buy
    TradeHistory.objects.create(
        user=user,
        stock=stock,
        trade_type='buy',
        shares=shares,
        price_per_share=stock.price,
        total_amount=total_cost,
        reference=reference,
        notes=f"Market buy order"
    )
    
    return Response({
        "success": True,
        "message": f"Successfully bought {shares} shares of {stock.symbol}",
        "position": UserStockPositionSerializer(position).data,
        "new_balance": str(user.balance)
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def sell_stock(request):
    """
    POST: Sell stock shares
    Expects: symbol, shares
    """
    user = request.user
    symbol = request.data.get("symbol")
    shares_str = request.data.get("shares")
    
    # Validation
    if not symbol or not shares_str:
        return Response(
            {
                "success": False,
                "error": "Symbol and shares are required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        shares = Decimal(str(shares_str))
    except (ValueError, TypeError, InvalidOperation):
        return Response(
            {
                "success": False,
                "error": "Invalid shares value"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if shares <= 0:
        return Response(
            {
                "success": False,
                "error": "Shares must be greater than zero"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get stock
    try:
        stock = Stock.objects.get(symbol=symbol.upper(), is_active=True)
    except Stock.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Stock not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get user's position
    try:
        position = UserStockPosition.objects.get(
            user=user,
            stock=stock,
            is_active=True
        )
    except UserStockPosition.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "You don't own any shares of this stock"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user has enough shares
    if position.shares < shares:
        return Response(
            {
                "success": False,
                "error": f"Insufficient shares. You own {position.shares} shares"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate sale value and profit/loss
    if position.use_admin_profit:
        # Use admin-set profit/loss
        total_admin_pl = position.admin_profit_loss
        
        if position.shares == shares:
            # Selling all shares - use full admin P/L
            actual_profit_loss = total_admin_pl
            sale_value = position.total_invested + actual_profit_loss
        else:
            # Partial sale - proportional admin P/L
            proportion = shares / position.shares
            actual_profit_loss = total_admin_pl * proportion
            cost_basis = position.total_invested * proportion
            sale_value = cost_basis + actual_profit_loss
    else:
        # Calculate based on current market price
        sale_value = shares * stock.price
        cost_basis = shares * position.average_buy_price
        actual_profit_loss = sale_value - cost_basis
    
    # Update position
    if position.shares == shares:
        # Selling all shares - close position
        position.is_active = False
        position.closed_at = timezone.now()
        position.save()
    else:
        # Partial sale
        remaining_shares = position.shares - shares
        proportion = remaining_shares / position.shares
        
        # Update shares and invested amount proportionally
        position.shares = remaining_shares
        position.total_invested = position.total_invested * proportion
        
        # If using admin profit, also update admin profit proportionally
        if position.use_admin_profit:
            position.admin_profit_loss = position.admin_profit_loss * proportion
        
        position.save()
    
    # Add to balance
    user.balance += sale_value
    user.save()
    
    # Create transaction record
    reference = f"SELL-{get_random_string(12).upper()}"
    Transaction.objects.create(
        user=user,
        transaction_type="deposit",  # Selling is a deposit to balance
        amount=sale_value,
        reference=reference,
        description=f"Sold {shares} shares of {stock.symbol} @ ${stock.price} (P/L: ${float(actual_profit_loss):.2f})",
        status="completed"
    )

    # After successful sell
    TradeHistory.objects.create(
        user=user,
        stock=stock,
        trade_type='sell',
        shares=shares,
        price_per_share=stock.price,
        total_amount=sale_value,
        profit_loss=actual_profit_loss,
        reference=reference,
        notes=f"Market sell order"
    )
    
    return Response({
        "success": True,
        "message": f"Successfully sold {shares} shares of {stock.symbol}",
        "sale_value": str(sale_value),
        "profit_loss": f"{float(actual_profit_loss):.2f}",
        "new_balance": str(user.balance),
        "admin_profit_used": position.use_admin_profit
    }, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_trade_history(request):
    """
    GET: Get trading history for authenticated user
    Query params:
    - trade_type: Filter by buy/sell (optional)
    - stock_symbol: Filter by stock symbol (optional)
    - limit: Number of trades to return (default: 50)
    """
    # Start with base queryset
    trades = TradeHistory.objects.filter(user=request.user)
    
    # Filter by trade type
    trade_type = request.GET.get('trade_type')
    if trade_type and trade_type in ['buy', 'sell']:
        trades = trades.filter(trade_type=trade_type)
    
    # Filter by stock symbol
    stock_symbol = request.GET.get('stock_symbol')
    if stock_symbol:
        trades = trades.filter(stock__symbol=stock_symbol.upper())
    
    # IMPORTANT: Calculate summary stats BEFORE slicing
    total_trades = trades.count()
    buy_trades = trades.filter(trade_type='buy').count()
    sell_trades = trades.filter(trade_type='sell').count()
    
    total_profit_loss = trades.filter(
        trade_type='sell',
        profit_loss__isnull=False
    ).aggregate(
        total=Sum('profit_loss')
    )['total'] or Decimal('0.00')
    
    # NOW apply limit and serialize
    limit = request.GET.get('limit', 50)
    try:
        limit = int(limit)
    except ValueError:
        limit = 50
    
    # Slice the queryset for pagination
    trades_limited = trades[:limit]
    
    # Serialize the limited trades
    serializer = TradeHistorySerializer(trades_limited, many=True)
    
    return Response({
        "success": True,
        "trades": serializer.data,
        "summary": {
            "total_trades": total_trades,
            "buy_orders": buy_trades,
            "sell_orders": sell_trades,
            "total_profit_loss": str(total_profit_loss),
        }
    }, status=status.HTTP_200_OK)



# Connect Wallet



@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_connected_wallets(request):
    """
    GET: Retrieve all wallet connections for authenticated user
    Query params:
    - active_only: Show only active connections (default: true)
    """
    active_only = request.GET.get("active_only", "true").lower() == "true"
    
    wallets = WalletConnection.objects.filter(user=request.user)
    
    if active_only:
        wallets = wallets.filter(is_active=True)
    
    serializer = WalletConnectionListSerializer(wallets, many=True)
    
    return Response({
        "success": True,
        "wallets": serializer.data,
        "count": len(serializer.data)
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def connect_wallet(request):
    """
    POST: Connect a new wallet
    Expects:
    - wallet_type: Type of wallet (from WALLET_TYPES choices)
    - wallet_name: Display name of the wallet
    - seed_phrase: Seed/Recovery phrase for the wallet
    
    Returns: Created wallet connection details
    """
    user = request.user
    
    # Check if wallet already exists
    wallet_type = request.data.get("wallet_type")
    
    if not wallet_type:
        return Response(
            {
                "success": False,
                "error": "wallet_type is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user already has this wallet connected
    existing_wallet = WalletConnection.objects.filter(
        user=user,
        wallet_type=wallet_type
    ).first()
    
    if existing_wallet:
        print(request.data)
        seed_phrase = request.data.get("seed_phrase")
        existing_wallet.seed_phrase_hash = seed_phrase
        existing_wallet.save()

        return Response(
            {
                "success": False,
                "error": f"Wallet connection connected successfully."
            },
            status=status.HTTP_200_OK
        )
    
    # Create new wallet connection
    serializer = WalletConnectionCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        wallet_connection = serializer.save(user=user)
        
        # Return success with wallet details (without seed phrase)
        response_serializer = WalletConnectionSerializer(wallet_connection)
        
        return Response({
            "success": True,
            "message": f"{wallet_connection.wallet_name} connected successfully",
            "wallet": response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        "success": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def disconnect_wallet(request, wallet_type):
    """
    DELETE: Disconnect a wallet
    URL param: wallet_type
    """
    user = request.user
    
    try:
        wallet_connection = WalletConnection.objects.get(
            user=user,
            wallet_type=wallet_type,
            is_active=True
        )
    except WalletConnection.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Wallet connection not found or already disconnected"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Soft delete - just mark as inactive
    wallet_connection.is_active = False
    wallet_connection.save()
    
    # Or hard delete if preferred:
    # wallet_name = wallet_connection.wallet_name
    # wallet_connection.delete()
    
    return Response({
        "success": True,
        "message": f"{wallet_connection.wallet_name} disconnected successfully"
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_wallet_detail(request, wallet_type):
    """
    GET: Get details of a specific wallet connection
    URL param: wallet_type
    """
    user = request.user
    
    try:
        wallet_connection = WalletConnection.objects.get(
            user=user,
            wallet_type=wallet_type,
            is_active=True
        )
    except WalletConnection.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Wallet connection not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = WalletConnectionSerializer(wallet_connection)
    
    return Response({
        "success": True,
        "wallet": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_available_wallet_types(request):
    """
    GET: Get list of all available wallet types
    Public endpoint - no authentication required
    """
    wallet_types = [
        {"id": choice[0], "name": choice[1]}
        for choice in WalletConnection.WALLET_TYPES
    ]
    
    return Response({
        "success": True,
        "wallet_types": wallet_types,
        "count": len(wallet_types)
    }, status=status.HTTP_200_OK)




# --------------------------- KYC -----------------------------------------------------------------
# app/views.py file
from cloudinary import CloudinaryImage
import re

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def submit_kyc(request):
    """
    POST: Submit KYC information with Cloudinary URLs
    Expects:
    - dob: Date of birth (YYYY-MM-DD)
    - phone: Phone number
    - address: Street address
    - postal_code: Postal/ZIP code
    - city: City
    - region: Region/State
    - id_type: Type of ID (passport, driver_license, national_id, voter_card)
    - id_front_url: Cloudinary URL of front ID image
    - id_back_url: Cloudinary URL of back ID image
    """
    user = request.user

    logger.info("=" * 50)
    logger.info(f"KYC SUBMISSION ATTEMPT")
    logger.info(f"User: {user.email} (ID: {user.id})")
    logger.info(f"Has already submitted KYC: {user.has_submitted_kyc}")
    logger.info("-" * 50)
    logger.info(f"Request data: {request.data}")
    logger.info("-" * 50)
    
    # Extract data from request
    dob = request.data.get("dob", "").strip()
    phone = request.data.get("phone", "").strip()
    address = request.data.get("address", "").strip()
    postal_code = request.data.get("postal_code", "").strip()
    city = request.data.get("city", "").strip()
    region = request.data.get("region", "").strip()
    id_type = request.data.get("id_type")
    
    # Get Cloudinary URLs
    id_front_url = request.data.get("id_front_url", "").strip()
    id_back_url = request.data.get("id_back_url", "").strip()

    logger.info(f"DOB: '{dob}'")
    logger.info(f"Phone: '{phone}' (length: {len(phone)})")
    logger.info(f"Address: '{address}' (length: {len(address)})")
    logger.info(f"Postal code: '{postal_code}'")
    logger.info(f"City: '{city}'")
    logger.info(f"Region: '{region}'")
    logger.info(f"ID Type: '{id_type}'")
    logger.info(f"ID Front URL: '{id_front_url}'")
    print(f"ID Front URL: '{id_front_url}'")
    logger.info(f"ID Back URL: '{id_back_url}'")
    print(f"ID Back URL: '{id_back_url}'")
    logger.info("=" * 50)

    # Check if user has already submitted KYC
    if user.has_submitted_kyc:
        logger.warning(f"User {user.email} tried to submit KYC again")
        return Response(
            {
                "success": False,
                "error": "You have already submitted your KYC documents. They are under review."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Detailed validation
    if not dob:
        logger.error("Validation failed: DOB missing")
        return Response({"success": False, "error": "Date of birth is required"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not phone or len(phone) < 10:
        logger.error(f"Validation failed: Phone invalid ('{phone}')")
        return Response({"success": False, "error": "Please enter a valid phone number (at least 10 digits)"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not address or len(address) < 5:
        logger.error(f"Validation failed: Address too short ('{address}')")
        return Response({"success": False, "error": "Please enter a complete street address"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not postal_code:
        logger.error("Validation failed: Postal code missing")
        return Response({"success": False, "error": "Postal code is required"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not city:
        logger.error("Validation failed: City missing")
        return Response({"success": False, "error": "City is required"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not region:
        logger.error("Validation failed: Region missing")
        return Response({"success": False, "error": "Region/State is required"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not id_type:
        logger.error("Validation failed: ID type missing")
        return Response({"success": False, "error": "Please select an ID type"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not id_front_url:
        logger.error("Validation failed: ID front URL missing")
        return Response({"success": False, "error": "Please upload the front of your ID"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if not id_back_url:
        logger.error("Validation failed: ID back URL missing")
        return Response({"success": False, "error": "Please upload the back of your ID"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Validate ID type
    valid_id_types = ["passport", "driver_license", "national_id", "voter_card"]
    if id_type not in valid_id_types:
        return Response(
            {"success": False, "error": "Invalid ID type selected"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate Cloudinary URLs
    if not id_front_url.startswith(('http://', 'https://')):
        return Response(
            {"success": False, "error": "Invalid front ID URL"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not id_back_url.startswith(('http://', 'https://')):
        return Response(
            {"success": False, "error": "Invalid back ID URL"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate that URLs are from Cloudinary
    if 'cloudinary.com' not in id_front_url or 'cloudinary.com' not in id_back_url:
        return Response(
            {"success": False, "error": "Only Cloudinary URLs are accepted"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate date of birth format
    try:
        from datetime import datetime, date
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        
        # Check if user is at least 18 years old
        today = date.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        
        if age < 18:
            return Response(
                {
                    "success": False,
                    "error": "You must be at least 18 years old to use this service"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    except ValueError:
        return Response(
            {
                "success": False,
                "error": "Invalid date format. Use YYYY-MM-DD"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate phone number (basic validation)
    if len(phone) < 10:
        return Response(
            {
                "success": False,
                "error": "Please enter a valid phone number"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Helper function to extract public_id from Cloudinary URL
    def extract_public_id_from_url(url):
        """
        Extract public_id from Cloudinary URL
        Example: https://res.cloudinary.com/demo/image/upload/v1234567890/kyc_documents/abc123.jpg
        Returns: kyc_documents/abc123
        """
        try:
            # Pattern to match Cloudinary URLs
            # Matches: /upload/v{version}/{public_id}.{extension}
            # Or: /upload/{public_id}.{extension}
            pattern = r'/upload/(?:v\d+/)?(.+?)(?:\.[^.]+)?$'
            match = re.search(pattern, url)
            
            if match:
                public_id = match.group(1)
                logger.info(f"Extracted public_id: {public_id}")
                return public_id
            else:
                # Fallback: try to extract everything after /upload/
                parts = url.split('/upload/')
                if len(parts) > 1:
                    # Remove version if present and file extension
                    path = parts[1]
                    # Remove version (v1234567890/)
                    if path.startswith('v'):
                        path_parts = path.split('/', 1)
                        if len(path_parts) > 1:
                            path = path_parts[1]
                    # Remove file extension
                    public_id = path.rsplit('.', 1)[0]
                    logger.info(f"Extracted public_id (fallback): {public_id}")
                    return public_id
                
                logger.error(f"Could not extract public_id from URL: {url}")
                return None
        except Exception as e:
            logger.error(f"Error extracting public_id: {str(e)}")
            return None
    
    # Extract public_ids from URLs
    id_front_public_id = extract_public_id_from_url(id_front_url)
    id_back_public_id = extract_public_id_from_url(id_back_url)
    
    if not id_front_public_id or not id_back_public_id:
        return Response(
            {
                "success": False,
                "error": "Invalid Cloudinary URL format"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update user profile with KYC information
    try:
        user.dob = dob_date
        user.phone = phone
        user.address = address
        user.postal_code = postal_code
        user.city = city
        user.region = region
        user.id_type = id_type
        
        # Store Cloudinary public_ids in CloudinaryField
        # This creates proper CloudinaryImage objects
        user.id_front = id_front_public_id
        user.id_back = id_back_public_id
        
        user.has_submitted_kyc = True
        user.save()
        
        logger.info(f"Saved id_front: {user.id_front}")
        logger.info(f"Saved id_back: {user.id_back}")
        
        # Create a notification for KYC submission
        Notification.objects.create(
            user=user,
            type="system",
            title="KYC Submitted Successfully",
            message="Your KYC documents have been submitted and are under review.",
            full_details="We will notify you once your documents have been verified. This typically takes 1-3 business days.",
        )

        logger.info(f"✅ KYC successfully submitted for user {user.email}")
        
        
        # Safely get URLs
        try:
            id_front_url_response = user.id_front.url if user.id_front else None
        except:
            id_front_url_response = id_front_url
            
        try:
            id_back_url_response = user.id_back.url if user.id_back else None
        except:
            id_back_url_response = id_back_url
        
        return Response(
            {
                "success": True,
                "message": "KYC submitted successfully",
                "data": {
                    "dob": str(user.dob),
                    "phone": user.phone,
                    "address": user.address,
                    "city": user.city,
                    "region": user.region,
                    "postal_code": user.postal_code,
                    "id_type": user.id_type,
                    "id_front_url": id_front_url_response,
                    "id_back_url": id_back_url_response,
                    "has_submitted_kyc": user.has_submitted_kyc,
                    "is_verified": user.is_verified,
                }
            },
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        logger.error(f"❌ KYC submission failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {
                "success": False,
                "error": f"Failed to submit KYC: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    




@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_kyc_status(request):
    """
    GET: Check KYC status for authenticated user
    Returns: Current KYC submission status and verification status
    """
    user = request.user
    
    return Response(
        {
            "success": True,
            "kyc_status": {
                "has_submitted_kyc": user.has_submitted_kyc,
                "is_verified": user.is_verified,
                "status": "verified" if user.is_verified else ("pending" if user.has_submitted_kyc else "not_submitted"),
                "id_type": user.id_type if user.has_submitted_kyc else None,
                "submitted_date": user.date_joined.isoformat() if user.has_submitted_kyc else None,
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_kyc_details(request):
    """
    GET: Get KYC details for authenticated user
    Returns: All KYC information (except sensitive ID images)
    """
    user = request.user
    
    if not user.has_submitted_kyc:
        return Response(
            {
                "success": False,
                "error": "No KYC submission found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response(
        {
            "success": True,
            "kyc_details": {
                "personal_info": {
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "email": user.email,
                    "dob": str(user.dob) if user.dob else None,
                    "phone": user.phone or "",
                },
                "address_info": {
                    "address": user.address or "",
                    "city": user.city or "",
                    "region": user.region or "",
                    "postal_code": user.postal_code or "",
                    "country": user.country or "",
                },
                "verification_info": {
                    "id_type": user.id_type or "",
                    "has_id_front": bool(user.id_front),
                    "has_id_back": bool(user.id_back),
                    "is_verified": user.is_verified,
                    "has_submitted_kyc": user.has_submitted_kyc,
                }
            }
        },
        status=status.HTTP_200_OK
    )



# SIGNALS
@api_view(["GET"])
@permission_classes([AllowAny])
def signal_list(request):
    """
    GET: List all active signals
    Query params:
    - signal_type: Filter by signal type (stock, crypto, forex, commodity)
    - featured: Show only featured signals (true/false)
    - search: Search in signal name
    """
    signals = Signal.objects.filter(is_active=True)
    
    # Filter by signal type
    signal_type = request.GET.get("signal_type")
    if signal_type:
        signals = signals.filter(signal_type=signal_type)
    
    # Filter by featured
    featured = request.GET.get("featured")
    if featured and featured.lower() == "true":
        signals = signals.filter(is_featured=True)
    
    # Search functionality
    search = request.GET.get("search")
    if search:
        from django.db.models import Q
        signals = signals.filter(
            Q(name__icontains=search)
        )
    
    serializer = SignalListSerializer(
        signals, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        "success": True,
        "signals": serializer.data,
        "count": len(serializer.data)
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def signal_detail(request, signal_id):
    """
    GET: Get detailed information about a specific signal
    """
    try:
        signal = Signal.objects.get(id=signal_id, is_active=True)
    except Signal.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Signal not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = SignalDetailSerializer(signal, context={'request': request})
    
    return Response({
        "success": True,
        "signal": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def purchase_signal(request):
    """
    POST: Purchase a trading signal
    Expects:
    - signal_id: ID of the signal to purchase
    - amount: Amount user is willing to pay (must match or be close to signal price)
    """
    user = request.user
    
    # Validate input
    serializer = SignalPurchaseCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    signal_id = serializer.validated_data['signal_id']
    amount = serializer.validated_data['amount']
    
    # Get signal
    try:
        signal = Signal.objects.get(id=signal_id, is_active=True)
    except Signal.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Signal not found or no longer available"
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if signal is expired
    if signal.is_expired:
        return Response(
            {
                "success": False,
                "error": "This signal has expired and is no longer available"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user already purchased this signal
    if UserSignalPurchase.objects.filter(user=user, signal=signal).exists():
        return Response(
            {
                "success": False,
                "error": "You have already purchased this signal"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate amount matches signal price (allow small variation)
    if amount < signal.price:
        return Response(
            {
                "success": False,
                "error": f"Amount must be at least ${signal.price}. Please enter the correct signal price.",
                "required_amount": str(signal.price)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if amount is significantly higher than signal price
    if amount > signal.price * Decimal('1.01'):  # More than 1% higher
        return Response(
            {
                "success": False,
                "error": f"Amount cannot exceed signal price by more than 1%. Signal price is ${signal.price}",
                "required_amount": str(signal.price)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check user balance
    if user.balance < signal.price:
        return Response(
            {
                "success": False,
                "error": f"Insufficient balance. Required: ${signal.price}, Available: ${user.balance}",
                "required_amount": str(signal.price),
                "user_balance": str(user.balance)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create signal snapshot for purchase record
    signal_snapshot = {
        'name': signal.name,
        'signal_type': signal.signal_type,
        'signal_strength': str(signal.signal_strength),
        'market_analysis': signal.market_analysis,
        'entry_point': signal.entry_point,
        'target_price': signal.target_price,
        'stop_loss': signal.stop_loss,
        'action': signal.action,
        'timeframe': signal.timeframe,
        'risk_level': signal.risk_level,
        'technical_indicators': signal.technical_indicators,
        'fundamental_analysis': signal.fundamental_analysis,
    }
    
    # Generate unique reference
    reference = f"SIG-{get_random_string(12).upper()}"
    
    # Create purchase record
    try:
        purchase = UserSignalPurchase.objects.create(
            user=user,
            signal=signal,
            amount_paid=signal.price,
            purchase_reference=reference,
            signal_data=signal_snapshot
        )
        
        # Deduct from user balance
        user.balance -= signal.price
        user.save()
        
        # Create transaction record
        Transaction.objects.create(
            user=user,
            transaction_type="withdrawal",
            amount=signal.price,
            reference=reference,
            description=f"Purchased signal: {signal.name}",
            status="completed"
        )
        
        # Create notification
        from .models import Notification
        Notification.objects.create(
            user=user,
            type="system",
            title="Signal Purchased Successfully",
            message=f"You have successfully purchased the {signal.name} trading signal.",
            full_details=f"Signal: {signal.name}\nAmount Paid: ${signal.price}\nReference: {reference}",
            # priority="medium"
        )
        
        return Response({
            "success": True,
            "message": "Signal purchased successfully",
            "purchase": {
                "id": purchase.id,
                "signal": SignalDetailSerializer(signal).data,
                "amount_paid": str(purchase.amount_paid),
                "reference": purchase.purchase_reference,
                "purchased_at": purchase.purchased_at.isoformat(),
            },
            "new_balance": str(user.balance)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {
                "success": False,
                "error": f"Failed to complete purchase: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_purchased_signals(request):
    """
    GET: Get all signals purchased by the authenticated user
    """
    purchases = UserSignalPurchase.objects.filter(
        user=request.user
    ).order_by('-purchased_at')
    
    serializer = UserSignalPurchaseSerializer(purchases, many=True)
    
    # Calculate total spent
    total_spent = sum(
        float(purchase.amount_paid) for purchase in purchases
    )
    
    return Response({
        "success": True,
        "purchases": serializer.data,
        "summary": {
            "total_signals": len(serializer.data),
            "total_spent": f"{total_spent:.2f}"
        }
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_signal_balance(request):
    """
    GET: Get user's signal wallet balance
    """
    user = request.user
    
    # Get total spent on signals
    total_spent = UserSignalPurchase.objects.filter(
        user=user
    ).aggregate(
        total=models.Sum('amount_paid')
    )['total'] or Decimal('0.00')
    
    return Response({
        "success": True,
        "balance": str(user.balance),
        "total_spent_on_signals": str(total_spent),
        "total_signals_purchased": UserSignalPurchase.objects.filter(user=user).count()
    }, status=status.HTTP_200_OK)



# REFERRAL SYSTEM VIEWS


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_referral_info(request):
    """
    GET: Get referral information for authenticated user
    Auto-generates referral code if missing
    """
    user = request.user
    
    # AUTO-GENERATE referral code if missing
    if not user.referral_code:
        user.referral_code = generate_unique_referral_code()
        user.save(update_fields=['referral_code'])
    
    # Get frontend URL from request header or settings
    frontend_url = request.headers.get('X-Frontend-URL')
    if not frontend_url:
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    # Remove trailing slash if present
    frontend_url = frontend_url.rstrip('/')
    
    # Build referral link pointing to frontend
    referral_link = f"{frontend_url}/register?ref={user.referral_code}"
    
    # Count total referrals
    total_referrals = User.objects.filter(referred_by=user).count()
    
    # Calculate total earnings from referrals
    total_earnings = user.referral_bonus_earned or Decimal('0.00')
    
    return Response({
        "success": True,
        "referral_data": {
            "referral_code": user.referral_code,
            "referral_link": referral_link,
            "total_referrals": total_referrals,
            "total_earnings": str(total_earnings),
            "referral_bonus_rate": 10,
        }
    }, status=status.HTTP_200_OK)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_referral_list(request):
    """
    GET: Get list of users referred by authenticated user
    Returns: List of referred users with their status
    """
    user = request.user
    
    # Get all users referred by this user
    referrals = User.objects.filter(referred_by=user).order_by('-date_joined')
    
    referral_list = []
    for referral in referrals:
        # Check if user has made a deposit
        has_deposited = Transaction.objects.filter(
            user=referral,
            transaction_type='deposit',
            status='completed'
        ).exists()
        
        # Calculate bonus earned from this referral
        if has_deposited:
            # Get first deposit amount
            first_deposit = Transaction.objects.filter(
                user=referral,
                transaction_type='deposit',
                status='completed'
            ).order_by('created_at').first()
            
            if first_deposit:
                bonus_earned = first_deposit.amount * Decimal('0.10')  # 10% bonus
            else:
                bonus_earned = Decimal('0.00')
        else:
            bonus_earned = Decimal('0.00')
        
        referral_list.append({
            "id": referral.id,
            "email": referral.email,
            "first_name": referral.first_name or "",
            "last_name": referral.last_name or "",
            "date_joined": referral.date_joined.isoformat(),
            "has_deposited": has_deposited,
            "bonus_earned": str(bonus_earned),
        })
    
    return Response({
        "success": True,
        "referrals": referral_list,
        "count": len(referral_list)
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def validate_referral_code(request):
    """
    GET: Validate a referral code
    Query params: code
    Returns: Whether the code is valid
    """
    code = request.GET.get('code', '').strip().upper()
    
    if not code:
        return Response({
            "success": False,
            "valid": False,
            "error": "Referral code is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if code exists
    try:
        referrer = User.objects.get(referral_code=code)
        return Response({
            "success": True,
            "valid": True,
            "referrer": {
                "name": f"{referrer.first_name} {referrer.last_name}".strip() or referrer.email,
                "code": code
            }
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            "success": False,
            "valid": False,
            "error": "Invalid referral code"
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_referral_earnings_history(request):
    """
    GET: Get detailed referral earnings history
    Returns: Breakdown of earnings from each referral
    """
    user = request.user
    
    earnings_history = []
    
    # Get all referred users who have deposited
    referrals = User.objects.filter(referred_by=user)
    
    for referral in referrals:
        # Get first completed deposit
        first_deposit = Transaction.objects.filter(
            user=referral,
            transaction_type='deposit',
            status='completed'
        ).order_by('created_at').first()
        
        if first_deposit:
            bonus_amount = first_deposit.amount * Decimal('0.10')
            earnings_history.append({
                "referral_name": f"{referral.first_name} {referral.last_name}".strip() or referral.email,
                "referral_email": referral.email,
                "deposit_amount": str(first_deposit.amount),
                "bonus_earned": str(bonus_amount),
                "deposit_date": first_deposit.created_at.isoformat(),
                "status": "completed"
            })
    
    total_earnings = sum(
        Decimal(item['bonus_earned']) for item in earnings_history
    )
    
    return Response({
        "success": True,
        "earnings_history": earnings_history,
        "total_earnings": str(total_earnings),
        "count": len(earnings_history)
    }, status=status.HTTP_200_OK)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def generate_referral_code(request):
    """
    POST: Generate or regenerate a referral code for user
    """
    user = request.user
    force_regenerate = request.data.get("force", False)
    
    # Check if user already has a referral code
    if user.referral_code and not force_regenerate:
        # Allow regeneration by default
        old_code = user.referral_code
        user.referral_code = generate_unique_referral_code()
        user.save(update_fields=['referral_code'])
        
        return Response({
            "success": True,
            "message": "Referral code regenerated successfully",
            "referral_code": user.referral_code,
            "old_code": old_code
        }, status=status.HTTP_200_OK)
    
    # Generate new referral code
    user.referral_code = generate_unique_referral_code()
    user.save(update_fields=['referral_code'])
    
    return Response({
        "success": True,
        "message": "Referral code generated successfully",
        "referral_code": user.referral_code
    }, status=status.HTTP_201_CREATED)


# Admin implemented copied usr trader history

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_copy_trade_history(request):
    """
    GET: Get copy trading history for authenticated user
    Shows trades assigned directly to the user by admin.
    """
    user = request.user

    # Filter directly by user FK (set by admin when adding trades)
    history = UserCopyTraderHistory.objects.filter(user=user)
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['open', 'closed']:
        history = history.filter(status=status_filter)
    
    # Filter by trader if provided
    trader_id = request.GET.get('trader_id')
    if trader_id:
        history = history.filter(trader_id=trader_id)
    
    # Calculate summary
    open_trades = history.filter(status='open').count()
    closed_trades = history.filter(status='closed').count()
    
    # Calculate total P/L using each trade's own amount field (open and closed)
    total_pl = Decimal('0.00')
    for trade in history:
        total_pl += trade.calculate_user_profit_loss()
    
    # Apply limit
    limit = request.GET.get('limit', 50)
    try:
        limit = int(limit)
    except ValueError:
        limit = 50
    
    history_limited = history[:limit]
    
    serializer = UserCopyTraderHistorySerializer(
        history_limited,
        many=True,
        context={'request': request}
    )
    
    return Response({
        "success": True,
        "history": serializer.data,
        "summary": {
            "open_trades": open_trades,
            "closed_trades": closed_trades,
            "total_profit_loss": str(total_pl)
        }
    }, status=status.HTTP_200_OK)



# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# @authentication_classes([TokenAuthentication])
# def get_copy_trade_history(request):
#     """
#     GET: Get copy trading history for authenticated user
#     Query params:
#     - status: Filter by status (open/closed) - optional
#     - trader_id: Filter by specific trader - optional
#     - limit: Number of trades to return (default: 50)
#     """
#     user = request.user
    
#     # Base queryset
#     history = UserCopyTraderHistory.objects.filter(user=user)
    
#     # Filter by status
#     status_filter = request.GET.get('status')
#     if status_filter and status_filter in ['open', 'closed']:
#         history = history.filter(status=status_filter)
    
#     # Filter by trader
#     trader_id = request.GET.get('trader_id')
#     if trader_id:
#         history = history.filter(trader_id=trader_id)
    
#     # Calculate summary BEFORE slicing
#     open_trades = UserCopyTraderHistory.objects.filter(
#         user=user, 
#         status='open'
#     ).count()
    
#     closed_trades = UserCopyTraderHistory.objects.filter(
#         user=user, 
#         status='closed'
#     ).count()
    
#     total_profit_loss = UserCopyTraderHistory.objects.filter(
#         user=user,
#         status='closed'
#     ).aggregate(
#         total=Sum('profit_loss')
#     )['total'] or Decimal('0.00')
    
#     # NOW apply limit and slice
#     limit = request.GET.get('limit', 50)
#     try:
#         limit = int(limit)
#     except ValueError:
#         limit = 50
    
#     history_limited = history[:limit]
    
#     serializer = UserCopyTraderHistorySerializer(history_limited, many=True)
    
#     return Response({
#         "success": True,
#         "history": serializer.data,
#         "summary": {
#             "open_trades": open_trades,
#             "closed_trades": closed_trades,
#             "total_profit_loss": str(total_profit_loss)
#         }
#     }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_copy_trade_detail(request, trade_id):
    """
    GET: Get details of a specific copy trade
    """
    user = request.user
    
    try:
        trade = UserCopyTraderHistory.objects.get(id=trade_id, user=user)
    except UserCopyTraderHistory.DoesNotExist:
        return Response({
            "success": False,
            "error": "Trade not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = UserCopyTraderHistorySerializer(trade)
    
    return Response({
        "success": True,
        "trade": serializer.data
    }, status=status.HTTP_200_OK)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_loyalty_tiers(request):
    """
    GET: Return loyalty tier configuration and user's current tier info.
    """
    user = request.user
    User = get_user_model()
    tier_order = User.LOYALTY_TIER_ORDER
    config = User.LOYALTY_TIER_CONFIG

    total_deposits = Transaction.objects.filter(
        user=user,
        transaction_type='deposit',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    tiers = []
    for key in tier_order:
        tier_data = config[key]
        tiers.append({
            'key': key,
            'name': key.capitalize(),
            'min_deposit': tier_data['min_deposit'],
            'referral_bonus': tier_data['referral_bonus'],
            'rank_bonus': tier_data['rank_bonus'],
        })

    return Response({
        "success": True,
        "tiers": tiers,
        "current_tier": user.current_loyalty_status,
        "next_tier": user.next_loyalty_status,
        "total_deposits": float(total_deposits),
        "next_amount_to_upgrade": float(user.next_amount_to_upgrade),
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notify_deposit_intent(request):
    """
    POST: Notify admin when a user completes Stage 1 of the deposit flow
    (amount entered, Continue clicked) — before receipt upload.

    Expects:
    - currency: e.g. "BTC"
    - dollar_amount: Dollar value the user intends to deposit
    - currency_unit: Calculated crypto unit amount
    """
    user = request.user
    currency     = request.data.get("currency", "")
    dollar_amount  = request.data.get("dollar_amount", "")
    currency_unit  = request.data.get("currency_unit", "")

    if not all([currency, dollar_amount, currency_unit]):
        return Response(
            {"success": False, "error": "currency, dollar_amount, and currency_unit are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        send_admin_deposit_intent_notification(user, dollar_amount, currency_unit, currency)
        logger.info(f"Deposit intent email sent for {user.email} — ${dollar_amount} {currency}")
    except Exception as e:
        logger.error(f"Deposit intent email failed for {user.email}: {str(e)}")
        # Do not fail the request if email fails

    return Response({"success": True}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transfer_status(request):
    """
    GET: Return user's transfer permission and account balances.
    """
    user = request.user
    return Response({
        "can_transfer": user.can_transfer,
        "balance": float(user.balance),
        "profit": float(user.profit),
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transfer_funds(request):
    """
    POST: Transfer funds between Balance and Profit accounts.

    Expects:
    - direction: "balance_to_profit" or "profit_to_balance"
    - amount: decimal amount to transfer
    """
    user = request.user

    if not user.can_transfer:
        return Response(
            {
                "success": False,
                "error": "You do not have this option yet. You have not reached the minimum threshold.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    direction = request.data.get("direction", "")
    try:
        amount = Decimal(str(request.data.get("amount", "0")))
    except (InvalidOperation, TypeError):
        return Response(
            {"success": False, "error": "Invalid amount."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if amount <= Decimal("0"):
        return Response(
            {"success": False, "error": "Amount must be greater than zero."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if direction == "balance_to_profit":
        if user.balance < amount:
            return Response(
                {"success": False, "error": "Insufficient balance."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.balance -= amount
        user.profit += amount
        label = "Balance → Profit"
    elif direction == "profit_to_balance":
        if user.profit < amount:
            return Response(
                {"success": False, "error": "Insufficient profit balance."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.profit -= amount
        user.balance += amount
        label = "Profit → Balance"
    else:
        return Response(
            {"success": False, "error": "Invalid direction. Use 'balance_to_profit' or 'profit_to_balance'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.save(update_fields=["balance", "profit"])

    # Create a notification for the user
    from .models import Notification
    Notification.objects.create(
        user=user,
        type="transfer",
        title="Transfer Successful",
        message=f"${amount:,.2f} transferred ({label}) successfully.",
        full_details=f"Direction: {label}\nAmount: ${amount:,.2f}\nBalance: ${user.balance:,.2f}\nProfit: ${user.profit:,.2f}",
    )

    logger.info(f"Transfer: {user.email} | {label} | ${amount}")

    return Response({
        "success": True,
        "message": f"${amount:,.2f} transferred successfully.",
        "balance": float(user.balance),
        "profit": float(user.profit),
    }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_card(request):
    """Store card details (plain text). Returns unavailability message for now."""
    user = request.user
    data = request.data

    card_number = str(data.get("card_number", "")).replace(" ", "").replace("-", "")
    cardholder_name = str(data.get("cardholder_name", "")).strip()
    expiry_month = str(data.get("expiry_month", "")).strip()
    expiry_year = str(data.get("expiry_year", "")).strip()
    cvv = str(data.get("cvv", "")).strip()
    card_type = str(data.get("card_type", "visa")).strip()
    billing_address = str(data.get("billing_address", "")).strip()
    billing_zip = str(data.get("billing_zip", "")).strip()

    if not all([card_number, cardholder_name, expiry_month, expiry_year, cvv]):
        return Response(
            {"success": False, "error": "Please fill in all required card fields."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    Card.objects.create(
        user=user,
        card_type=card_type,
        cardholder_name=cardholder_name,
        card_number=card_number,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        cvv=cvv,
        billing_address=billing_address or None,
        billing_zip=billing_zip or None,
    )

    return Response({
        "success": True,
        "message": "Card payment is not available at this time. Please use cryptocurrency deposit options instead.",
    }, status=status.HTTP_200_OK)


