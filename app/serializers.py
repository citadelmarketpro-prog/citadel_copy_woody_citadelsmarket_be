from rest_framework import serializers
from .models import (
    Ticket, 
    Transaction, 
    AdminWallet, 
    Trader,
    Asset, 
    Notification, 
    UserStockPosition, 
    Stock,
    WalletConnection,
    Signal, UserSignalPurchase,
    TradeHistory,
    UserTraderCopy,
    UserCopyTraderHistory,
)


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "user", "subject", "category", "description", "created_at"]
        read_only_fields = ["id", "user"]


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    receipt_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'user_email',
            'transaction_type',
            'transaction_type_display',
            'amount',
            'status',
            'status_display',
            'reference',
            'description',
            'currency',
            'unit',
            'receipt',
            'receipt_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'reference', 'created_at', 'updated_at']
    
    def get_receipt_url(self, obj):
        """Return the receipt URL if it exists"""
        if obj.receipt:
            return obj.receipt.url
        return None


class AdminWalletSerializer(serializers.ModelSerializer):
    """Serializer for AdminWallet model"""
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminWallet
        fields = [
            'id',
            'currency',
            'currency_display',
            'amount',
            'wallet_address',
            'qr_code',
            'qr_code_url',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_qr_code_url(self, obj):
        """Return the QR code URL if it exists"""
        if obj.qr_code:
            return obj.qr_code.url
        return None



class TraderSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(use_url=True)
    country_flag = serializers.ImageField(use_url=True)
    class Meta:
        model = Trader
        fields = [
            "id", "name", "country", "country_flag", "avatar", "gain", "risk",
            "capital", "copiers", "avg_trade_time", "trades",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url  # Full Cloudinary URL
        return None
    
    def get_country_flag(self, obj):
        if obj.country_flag:
            return obj.country_flag.url  # Full Cloudinary URL
        return None


# Admin will update it himself
# app/serializers.py


class UserCopyTraderHistorySerializer(serializers.ModelSerializer):
    """Serializer for user-specific view of trader history"""
    trader_name = serializers.CharField(source='trader.name', read_only=True)
    trader_username = serializers.CharField(source='trader.username', read_only=True)
    market_name = serializers.SerializerMethodField()
    market_logo_url = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    is_profit = serializers.SerializerMethodField()
    
    # ✅ User-specific profit/loss calculation
    user_profit_loss = serializers.SerializerMethodField()
    user_amount_invested = serializers.SerializerMethodField()
    
    class Meta:
        model = UserCopyTraderHistory
        fields = [
            'id', 'trader_name', 'trader_username',
            'market', 'market_name', 'market_logo_url',
            'direction', 'duration', 'amount',
            'entry_price', 'exit_price',
            'profit_loss_percent',  # ✅ Changed from profit_loss
            'user_profit_loss',     # ✅ NEW
            'user_amount_invested', # ✅ NEW
            'status', 'opened_at', 'closed_at',
            'reference', 'time_ago', 'is_profit'
        ]
    
    def get_market_name(self, obj):
        return obj.market_name
    
    def get_market_logo_url(self, obj):
        return obj.market_logo_url
    
    def get_time_ago(self, obj):
        return obj.time_ago
    
    def get_is_profit(self, obj):
        return obj.is_profit
    
    def get_user_profit_loss(self, obj):
        """P/L is always trade.amount * profit_loss_percent / 100."""
        return str(obj.calculate_user_profit_loss())

    def get_user_amount_invested(self, obj):
        """The admin-entered trade amount IS the user's investment."""
        return str(obj.amount)
        
        

# class UserCopyTraderHistorySerializer(serializers.ModelSerializer):
#     """Serializer for copy trade history"""
#     time_ago = serializers.ReadOnlyField()
#     is_profit = serializers.ReadOnlyField()
#     market_logo_url = serializers.ReadOnlyField()
#     market_name = serializers.ReadOnlyField()
#     trader_name = serializers.CharField(source='trader.name', read_only=True)
#     trader_username = serializers.CharField(source='trader.username', read_only=True)
    
#     class Meta:
#         model = UserCopyTraderHistory
#         fields = [
#             'id',
#             'trader_name',
#             'trader_username',
#             'market',
#             'market_name',
#             'market_logo_url',
#             'direction',
#             # 'leverage',
#             'duration',
#             'amount',
#             'entry_price',
#             'exit_price',
#             'profit_loss',
#             'status',
#             'opened_at',
#             'closed_at',
#             'reference',
#             'time_ago',
#             'is_profit'
#         ]
#         read_only_fields = ['id', 'opened_at', 'reference']



class AssetSerializer(serializers.ModelSerializer):
    flag = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ["id", "category", "symbol", "flag", "change", "bid", "ask", "low", "high", "time"]

    def get_flag(self, obj):
        # return Cloudinary image URL
        return obj.flag.url if obj.flag else None
    



# Add this to your app/serializers.py file

from .models import News

class NewsSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            "id", "title", "summary", "content", "category", 
            "source", "author", "published_at", "image_url", 
            "tags", "is_featured", "created_at", "updated_at"
        ]

    def get_image_url(self, obj):
        # Return Cloudinary image URL
        return obj.image.url if obj.image else None
    





# Update your TraderSerializer in app/serializers.py

from .models import Trader, TraderPortfolio

class TraderPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraderPortfolio
        fields = [
            'id', 'market', 'direction', 'invested', 
            'profit_loss', 'value', 'opened_at', 'is_active'
        ]


# class TraderListSerializer(serializers.ModelSerializer):
#     """Serializer for list view - lighter fields"""
#     avatar_url = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Trader
#         fields = [
#             'id', 'name', 'username', 'avatar_url', 'badge',
#             'country', 'gain', 'risk', 'trades', 'capital',
#             'copiers', 'is_active'
#         ]
    
#     def get_avatar_url(self, obj):
#         return obj.avatar.url if obj.avatar else None


class TraderListSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    country_flag = serializers.SerializerMethodField()
    
    class Meta:
        model = Trader
        fields = [
            'id', 'name', 'username', 'avatar', 'country_flag',
            'badge', 'country', 'gain', 'risk', 'trades', 
            'capital', 'copiers', 'is_active'
        ]
    
    def get_avatar(self, obj):
        """Return full Cloudinary URL for avatar"""
        if obj.avatar:
            try:
                return obj.avatar.url
            except:
                return None
        return None
    
    def get_country_flag(self, obj):
        """Return full Cloudinary URL for country flag"""
        if obj.country_flag:
            try:
                return obj.country_flag.url
            except:
                return None
        return None


class TraderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view - all fields"""
    avatar_url = serializers.SerializerMethodField()
    portfolios = TraderPortfolioSerializer(many=True, read_only=True)
    
    class Meta:
        model = Trader
        fields = [
            'id', 'name', 'username', 'avatar_url', 'badge', 'country',
            'gain', 'risk', 'trades', 'capital', 'copiers', 'avg_trade_time',
            # Stats
            'subscribers', 'current_positions', 'min_account_threshold',
            'expert_rating', 'return_ytd', 'return_2y', 'avg_score_7d',
            'profitable_weeks', 'total_trades_12m', 'avg_profit_percent',
            'avg_loss_percent',
            # Wins and Losses
            'total_wins', 'total_losses',
            # Complex data
            'performance_data', 'monthly_performance', 'frequently_traded',
            # Related
            'portfolios',
            # Metadata
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_avatar_url(self, obj):
        return obj.avatar.url if obj.avatar else None
    
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'full_details',
            # 'priority', 
            'metadata', 'read', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class UserTraderCopySerializer(serializers.ModelSerializer):
    """Serializer for UserTraderCopy model"""
    trader_name = serializers.CharField(source='trader.name', read_only=True)
    trader_username = serializers.CharField(source='trader.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserTraderCopy
        fields = [
            'id',
            'user',
            'user_email',
            'trader',
            'trader_name',
            'trader_username',
            'is_actively_copying',
            'initial_investment_amount',
            'minimum_threshold_at_start',
            'started_copying_at',
            'last_updated',
            'stopped_copying_at',
            'cancel_requested',
            'cancel_requested_at',
        ]
        read_only_fields = ['started_copying_at', 'last_updated', 'stopped_copying_at', 'cancel_requested_at']




class UserTraderCopyCreateSerializer(serializers.Serializer):
    """Serializer for copy/cancel trader actions"""
    trader_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['copy', 'cancel'])
    
    def validate_trader_id(self, value):
        """Validate that trader exists and is active"""
        try:
            Trader.objects.get(id=value, is_active=True)
        except Trader.DoesNotExist:
            raise serializers.ValidationError("Trader not found or inactive")
        return value
    
    def validate_action(self, value):
        """Validate action"""
        if value not in ['copy', 'cancel']:
            raise serializers.ValidationError("Action must be 'copy' or 'cancel'")
        return value



class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model"""
    is_positive_change = serializers.BooleanField(read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    formatted_market_cap = serializers.CharField(read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id',
            'symbol',
            'name',
            'logo_url',
            'price',
            'change',
            'change_percent',
            'volume',
            'market_cap',
            'formatted_market_cap',
            'sector',
            'is_active',
            'is_featured',
            'is_positive_change',
            'formatted_price',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for stock list view"""
    is_positive_change = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id',
            'symbol',
            'name',
            'logo_url',
            'price',
            'change',
            'change_percent',
            'is_positive_change',
            'is_featured'
        ]


# In serializers.py

class StockBasicSerializer(serializers.ModelSerializer):
    """Basic stock info for nested serialization"""
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'name', 'price', 'logo_url']



class UserStockPositionSerializer(serializers.ModelSerializer):
    stock = StockBasicSerializer(read_only=True)
    current_value = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    profit_loss_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = UserStockPosition
        fields = [
            'id', 
            'stock', 
            'shares', 
            'average_buy_price', 
            'total_invested',
            'current_value',
            'profit_loss',
            'profit_loss_percent',
            'use_admin_profit',  # Add this
            'admin_profit_loss',  # Add this
            'opened_at',
            'is_active'
        ]
    
    def get_current_value(self, obj):
        """Return current value - either based on admin P/L or calculated"""
        if obj.use_admin_profit:
            # Use admin-set profit to calculate current value
            return str(obj.total_invested + obj.admin_profit_loss)
        else:
            # Calculate based on current stock price
            return str(obj.current_value)
    
    def get_profit_loss(self, obj):
        """Return profit/loss - either admin-set or calculated"""
        return str(obj.profit_loss)  # This property already handles the logic
    
    def get_profit_loss_percent(self, obj):
        """Return profit/loss percentage - either admin-set or calculated"""
        return str(obj.profit_loss_percent)  # This property already handles the logic


class TradeHistorySerializer(serializers.ModelSerializer):
    stock = StockBasicSerializer(read_only=True)
    formatted_total = serializers.SerializerMethodField()
    formatted_profit_loss = serializers.SerializerMethodField()
    
    class Meta:
        model = TradeHistory
        fields = [
            'id',
            'stock',
            'trade_type',
            'shares',
            'price_per_share',
            'total_amount',
            'formatted_total',
            'profit_loss',
            'formatted_profit_loss',
            'reference',
            'notes',
            'executed_at'
        ]
    
    def get_formatted_total(self, obj):
        return f"${obj.total_amount:,.2f}"
    
    def get_formatted_profit_loss(self, obj):
        if obj.profit_loss is not None:
            sign = "+" if obj.profit_loss >= 0 else ""
            return f"{sign}${obj.profit_loss:,.2f}"
        return None



class WalletConnectionSerializer(serializers.ModelSerializer):
    """Serializer for WalletConnection model"""
    wallet_type_display = serializers.CharField(source='get_wallet_type_display', read_only=True)
    
    class Meta:
        model = WalletConnection
        fields = [
            'id',
            'wallet_type',
            'wallet_type_display',
            'wallet_name',
            'is_active',
            'connected_at',
            'last_verified'
        ]
        read_only_fields = ['id', 'connected_at', 'last_verified']


class WalletConnectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating wallet connections"""
    seed_phrase = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Seed/Recovery phrase for the wallet"
    )
    
    class Meta:
        model = WalletConnection
        fields = [
            'wallet_type',
            'wallet_name',
            'seed_phrase'
        ]
    
    def create(self, validated_data):
        seed_phrase = validated_data.pop('seed_phrase')
        wallet_connection = WalletConnection(**validated_data)
        # Store seed phrase temporarily for hashing in model save
        wallet_connection._seed_phrase_plain = seed_phrase
        wallet_connection.save()
        return wallet_connection


class WalletConnectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing wallet connections"""
    
    class Meta:
        model = WalletConnection
        fields = [
            'id',
            'wallet_type',
            'wallet_name',
            'is_active',
            'connected_at'
        ]


# SIGNALS




class SignalListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing signals (basic info only)
    """
    is_purchased = serializers.SerializerMethodField()
    
    class Meta:
        model = Signal
        fields = [
            'id',
            'name',
            'signal_type',
            'price',
            'signal_strength',
            'action',
            'risk_level',
            'timeframe',
            'status',
            'is_featured',
            'is_purchased',
            'created_at',
            'expires_at',
        ]
    
    def get_is_purchased(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserSignalPurchase.objects.filter(
                user=request.user,
                signal=obj
            ).exists()
        return False


class SignalDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for signal detail (full info including analysis)
    """
    is_purchased = serializers.SerializerMethodField()
    
    class Meta:
        model = Signal
        fields = [
            'id',
            'name',
            'signal_type',
            'price',
            'signal_strength',
            'market_analysis',
            'entry_point',
            'target_price',
            'stop_loss',
            'action',
            'timeframe',
            'risk_level',
            'technical_indicators',
            'fundamental_analysis',
            'status',
            'is_featured',
            'is_purchased',
            'created_at',
            'updated_at',
            'expires_at',
        ]
    
    def get_is_purchased(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserSignalPurchase.objects.filter(
                user=request.user,
                signal=obj
            ).exists()
        return False


class UserSignalPurchaseSerializer(serializers.ModelSerializer):
    """
    Serializer for user signal purchases
    """
    signal = SignalDetailSerializer(read_only=True)
    signal_name = serializers.CharField(source='signal.name', read_only=True)
    
    class Meta:
        model = UserSignalPurchase
        fields = [
            'id',
            'signal',
            'signal_name',
            'amount_paid',
            'purchase_reference',
            'signal_data',
            'purchased_at',
            'accessed_at',
        ]


class SignalPurchaseCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a signal purchase
    """
    signal_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value