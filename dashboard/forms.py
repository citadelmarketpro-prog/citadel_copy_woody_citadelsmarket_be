# dashboard/forms.py
from django import forms
from app.models import CustomUser, Stock, Transaction, AdminWallet, Trader, UserCopyTraderHistory, Card
from decimal import Decimal

class AddTradeForm(forms.Form):
    """Form for adding trades with extensive dropdowns"""
    
    # User selection
    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        }),
        to_field_name='email'
    )
    
    # Entry amount
    entry = forms.DecimalField(
        label="Entry Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '5255'
        })
    )
    
    # Asset type
    ASSET_TYPE_CHOICES = [
        ('', 'Select Type'),
        ('stock', 'Stock'),
        ('crypto', 'Crypto'),
        ('forex', 'Forex'),
    ]
    
    asset_type = forms.ChoiceField(
        choices=ASSET_TYPE_CHOICES,
        label="Type",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Asset (populated dynamically based on type)
    asset = forms.CharField(
        label="Asset",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Select type first'
        })
    )
    
    # Direction
    DIRECTION_CHOICES = [
        ('', 'Select Direction'),
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('futures', 'Futures'),
    ]
    
    direction = forms.ChoiceField(
        choices=DIRECTION_CHOICES,
        label="Direction",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Profit/Loss
    profit = forms.DecimalField(
        label="Profit/Loss",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '0.00'
        })
    )
    
    # Duration
    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 minutes'),
        ('5 minutes', '5 minutes'),
        ('30 minutes', '30 minutes'),
        ('1 hour', '1 hour'),
        ('8 hours', '8 hours'),
        ('10 hours', '10 hours'),
        ('20 hours', '20 hours'),
        ('1 day', '1 day'),
        ('2 days', '2 days'),
        ('3 days', '3 days'),
        ('4 days', '4 days'),
        ('5 days', '5 days'),
        ('6 days', '6 days'),
        ('1 week', '1 week'),
        ('2 weeks', '2 weeks'),
    ]
    
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Duration",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Rate (optional)
    rate = forms.DecimalField(
        label="Rate (Optional)",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '251'
        })
    )


class AddEarningsForm(forms.Form):
    """Quick form for adding earnings to users"""

    DESTINATION_CHOICES = [
        ('balance', 'Balance'),
        ('profit', 'Profit'),
    ]

    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
        to_field_name='email'
    )

    destination = forms.ChoiceField(
        choices=DESTINATION_CHOICES,
        label="Add to",
        initial='balance',
        widget=forms.RadioSelect(attrs={
            'class': 'destination-radio',
        })
    )

    amount = forms.DecimalField(
        label="Earnings Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': '100.00'
        })
    )

    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Bonus, Referral, Trade Profit, etc.'
        })
    )


class ApproveDepositForm(forms.Form):
    """Form for approving deposits"""
    
    STATUS_CHOICES = [
        ('completed', 'Approve'),
        ('failed', 'Reject'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Internal notes about this transaction...'
        })
    )


class ApproveWithdrawalForm(forms.Form):
    """Form for approving withdrawals"""
    
    STATUS_CHOICES = [
        ('completed', 'Approve'),
        ('failed', 'Reject'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Internal notes about this withdrawal...'
        })
    )


class ApproveKYCForm(forms.Form):
    """Form for approving KYC submissions"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve KYC'),
        ('reject', 'Reject KYC'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Reason for rejection or any notes...'
        })
    )


# dashboard/forms.py - Updated AddCopyTradeForm
class AddCopyTradeForm(forms.Form):
    """Form for adding copy trade history - LEVERAGE REMOVED"""
    
    # User selection
    # user = forms.ModelChoiceField(
    #     queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
    #     label="Select User",
    #     widget=forms.Select(attrs={
    #         'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
    #         'id': 'id_user'
    #     }),
    #     empty_label="Select User"
    # )
    
    # Trader selection
    trader = forms.ModelChoiceField(
        queryset=Trader.objects.filter(is_active=True).order_by('name'),
        label="Select Trader",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        }),
        empty_label="Select Trader"
    )
    
    # Market selection - Updated to match model MARKET_CHOICES
    market = forms.ChoiceField(
        choices=[('', 'Select Market')] + list(UserCopyTraderHistory.MARKET_CHOICES),
        label="Market / Asset",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Direction
    direction = forms.ChoiceField(
        choices=[('', 'Select Direction')] + list(UserCopyTraderHistory.DIRECTION_CHOICES),
        label="Trade Direction",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # LEVERAGE FIELD REMOVED
    
    # Duration
    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 Minutes'),
        ('5 minutes', '5 Minutes'),
        ('10 minutes', '10 Minutes'),
        ('15 minutes', '15 Minutes'),
        ('30 minutes', '30 Minutes'),
        ('1 hour', '1 Hour'),
        ('2 hours', '2 Hours'),
        ('4 hours', '4 Hours'),
        ('12 hours', '12 Hours'),
        ('1 day', '1 Day'),
        ('2 days', '2 Days'),
        ('1 week', '1 Week'),
        ('2 weeks', '2 Weeks'),
        ('1 month', '1 Month'),
    ]
    
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Trade Duration",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Amount
    amount = forms.DecimalField(
        label="Investment Amount",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '1000.00',
            'step': '0.00000001'
        })
    )
    
    # Entry Price
    entry_price = forms.DecimalField(
        label="Entry Price",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '50000.00',
            'step': '0.00000001'
        })
    )
    
    # Exit Price (Optional)
    exit_price = forms.DecimalField(
        label="Exit Price (Optional)",
        max_digits=20,
        decimal_places=8,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '51000.00',
            'step': '0.00000001'
        })
    )
    
    # Profit/Loss
    profit_loss_percent = forms.DecimalField(
        label="Profit / Loss %",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
            'placeholder': '15.50 (positive for profit, negative for loss)',
            'step': '0.01'
        }),
        help_text="Enter as percentage (e.g., 15.50 for +15.5% gain)"
    )
    
    # Status
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + list(UserCopyTraderHistory.STATUS_CHOICES),
        label="Trade Status",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Closed At (Optional)
    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)",
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'datetime-local',
            'placeholder': 'Leave blank if trade is still open'
        })
    )
    
    # Notes
    notes = forms.CharField(
        label="Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Additional notes about this trade...'
        })
    )

class AddTraderForm(forms.Form):
    """Form for adding professional traders - direct input, no dropdown/range combos"""

    _i = 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
    _s = _i
    _f = 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
    _c = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    # --- Basic Info ---
    name = forms.CharField(
        label="Trader Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': _i, 'placeholder': 'Kristijan'
        })
    )
    
    username = forms.CharField(
        label="Username", max_length=100,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '@kristijan'}),
        help_text="Must be unique"
    )
    avatar = forms.ImageField(
        label="Avatar Image", required=False,
        widget=forms.FileInput(attrs={'class': _f, 'accept': 'image/*'})
    )
    country_flag = forms.ImageField(
        label="Country Flag Image", required=False,
        widget=forms.FileInput(attrs={'class': _f, 'accept': 'image/*'})
    )

    COUNTRY_CHOICES = [
        ('', 'Select Country'),
        ('United States', 'United States'), ('United Kingdom', 'United Kingdom'),
        ('Germany', 'Germany'), ('France', 'France'), ('Canada', 'Canada'),
        ('Australia', 'Australia'), ('Singapore', 'Singapore'), ('Hong Kong', 'Hong Kong'),
        ('Japan', 'Japan'), ('South Korea', 'South Korea'), ('India', 'India'),
        ('Brazil', 'Brazil'), ('Mexico', 'Mexico'), ('Netherlands', 'Netherlands'),
        ('Switzerland', 'Switzerland'), ('Sweden', 'Sweden'), ('Norway', 'Norway'),
        ('Denmark', 'Denmark'), ('Spain', 'Spain'), ('Italy', 'Italy'), ('Other', 'Other'),
    ]
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES, label="Country",
        widget=forms.Select(attrs={'class': _s})
    )
    badge = forms.ChoiceField(
        choices=[('', 'Select Badge'), ('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold')],
        label="Badge Level",
        widget=forms.Select(attrs={'class': _s})
    )

    # --- Capital & Gain ---
    capital = forms.CharField(
        label="Starting Capital ($)", max_length=50,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '50000'})
    )
    gain = forms.DecimalField(
        label="Total Gain (%)", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '126799.00', 'step': '0.01'})
    )

    # --- Risk & Time ---
    RISK_CHOICES = [(i, str(i)) for i in range(1, 11)]
    risk = forms.ChoiceField(
        choices=[('', 'Select Risk Level')] + RISK_CHOICES,
        label="Risk Level (1-10)",
        widget=forms.Select(attrs={'class': _s})
    )
    AVG_TRADE_TIME_CHOICES = [
        ('', 'Select Avg Trade Time'),
        ('1 day', '1 Day'), ('3 days', '3 Days'), ('1 week', '1 Week'), ('2 weeks', '2 Weeks'),
        ('3 weeks', '3 Weeks'), ('1 month', '1 Month'), ('2 months', '2 Months'),
        ('3 months', '3 Months'), ('6 months', '6 Months'),
    ]
    avg_trade_time = forms.ChoiceField(
        choices=AVG_TRADE_TIME_CHOICES, label="Avg Trade Time",
        widget=forms.Select(attrs={'class': _s})
    )

    # --- Copiers & Trades ---
    copiers = forms.IntegerField(
        label="Current Copiers",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '40', 'min': '0'})
    )
    trades = forms.IntegerField(
        label="Total Trades",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '251', 'min': '0'})
    )

    # --- Performance Stats ---
    avg_profit_percent = forms.DecimalField(
        label="Avg Profit %", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '86.00', 'step': '0.01'})
    )
    avg_loss_percent = forms.DecimalField(
        label="Avg Loss %", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '8.00', 'step': '0.01'})
    )
    total_wins = forms.IntegerField(
        label="Total Wins",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '1166', 'min': '0'})
    )
    total_losses = forms.IntegerField(
        label="Total Losses",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '160', 'min': '0'})
    )

    # --- Additional Stats ---
    subscribers = forms.IntegerField(
        label="Subscribers", required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '49', 'min': '0'})
    )
    current_positions = forms.IntegerField(
        label="Current Open Positions", required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '3', 'min': '0'})
    )
    expert_rating = forms.DecimalField(
        label="Expert Rating (out of 5.00)", max_digits=3, decimal_places=2, required=False, initial=5.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '4.80', 'step': '0.01', 'min': '0', 'max': '5'})
    )
    min_account_threshold = forms.DecimalField(
        label="Min Account Balance ($)", max_digits=12, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '50000.00', 'step': '0.01'})
    )

    # --- Performance Metrics ---
    return_ytd = forms.DecimalField(
        label="Return YTD %", max_digits=10, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '2187.00', 'step': '0.01'})
    )
    return_2y = forms.DecimalField(
        label="Return 2 Years %", max_digits=10, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '5000.00', 'step': '0.01'})
    )
    avg_score_7d = forms.DecimalField(
        label="Avg Score (7 days)", max_digits=10, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '9.30', 'step': '0.01'})
    )
    profitable_weeks = forms.DecimalField(
        label="Profitable Weeks %", max_digits=5, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '92.00', 'step': '0.01'})
    )
    total_trades_12m = forms.IntegerField(
        label="Total Trades (12 months)", required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '150', 'min': '0'})
    )

    # --- Status ---
    is_active = forms.BooleanField(
        label="Active (Available for Copying)", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': _c})
    )


class EditTraderForm(AddTraderForm):
    """Inherits all fields from AddTraderForm."""
    pass


class EditDepositForm(forms.Form):
    """Form for editing deposit details"""
    
    # Amount
    amount = forms.DecimalField(
        label="Deposit Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '1000.00',
            'step': '0.01'
        })
    )
    
    # Currency
    CURRENCY_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('SOL', 'Solana (SOL)'),
        ('USDT ERC20', 'USDT (ERC20)'),
        ('USDT TRC20', 'USDT (TRC20)'),
        ('BNB', 'Binance Coin (BNB)'),
        ('TRX', 'Tron (TRX)'),
        ('USDC', 'USDC (BASE)'),
    ]
    
    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        label="Currency",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    # Unit (crypto amount)
    unit = forms.DecimalField(
        label="Crypto Unit Amount",
        max_digits=12,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '0.01234567',
            'step': '0.00000001'
        }),
        help_text="Amount of cryptocurrency deposited"
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Status",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    # Description
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Deposit description...'
        })
    )
    
    # Reference
    reference = forms.CharField(
        label="Reference Number",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'DEP-XXXXXXXXXX'
        })
    )
    
    # Receipt (optional - for updating)
    receipt = forms.ImageField(
        label="Update Receipt (Optional)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'accept': 'image/*'
        }),
        help_text="Leave blank to keep existing receipt"
    )


class AddUserDirectTradeForm(forms.Form):
    """Form to add a trade directly to a specific user (not tied to a trader)."""

    _input = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    _select = _input
    _textarea = _input

    market = forms.ChoiceField(
        choices=[('', 'Select Market')] + list(UserCopyTraderHistory.MARKET_CHOICES),
        label="Market / Asset",
        widget=forms.Select(attrs={'class': _select}),
    )

    DIRECTION_CHOICES = [('', 'Select Direction'), ('buy', 'Buy'), ('sell', 'Sell')]
    direction = forms.ChoiceField(
        choices=DIRECTION_CHOICES,
        label="Trade Direction",
        widget=forms.Select(attrs={'class': _select}),
    )

    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 Minutes'), ('5 minutes', '5 Minutes'), ('10 minutes', '10 Minutes'),
        ('15 minutes', '15 Minutes'), ('30 minutes', '30 Minutes'),
        ('1 hour', '1 Hour'), ('2 hours', '2 Hours'), ('4 hours', '4 Hours'), ('12 hours', '12 Hours'),
        ('1 day', '1 Day'), ('2 days', '2 Days'),
        ('1 week', '1 Week'), ('2 weeks', '2 Weeks'), ('1 month', '1 Month'),
    ]
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Trade Duration",
        widget=forms.Select(attrs={'class': _select}),
    )

    entry_price = forms.DecimalField(
        label="Entry Price",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '50000.00', 'step': '0.00000001'}),
    )

    exit_price = forms.DecimalField(
        label="Exit Price (Optional)",
        max_digits=20,
        decimal_places=8,
        required=False,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '51000.00', 'step': '0.00000001'}),
    )

    profit_loss_percent = forms.DecimalField(
        label="Profit / Loss %",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '15.50', 'step': '0.01'}),
        help_text="Positive for profit, negative for loss",
    )

    STATUS_CHOICES = [('', 'Select Status'), ('open', 'Open'), ('closed', 'Closed')]
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Trade Status",
        widget=forms.Select(attrs={'class': _select}),
    )

    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)",
        required=False,
        widget=forms.DateTimeInput(attrs={'class': _input, 'type': 'datetime-local'}),
    )

    notes = forms.CharField(
        label="Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Additional notes...'}),
    )

# ---------------------------------------------------------------------------
# Admin Wallet Form
# ---------------------------------------------------------------------------

class AdminWalletForm(forms.Form):
    _i = 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
    _s = _i
    _f = 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
    _c = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    currency = forms.ChoiceField(
        choices=[('', 'Select Currency')] + list(AdminWallet.CURRENCY_CHOICES),
        label="Currency",
        widget=forms.Select(attrs={'class': _s}),
    )
    amount = forms.DecimalField(
        label="Rate (USD per unit)",
        max_digits=20, decimal_places=6,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '97250.00', 'step': '0.000001'}),
    )
    wallet_address = forms.CharField(
        label="Wallet Address", max_length=255,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'}),
    )
    qr_code = forms.ImageField(
        label="QR Code (Optional)", required=False,
        widget=forms.FileInput(attrs={'class': _f, 'accept': 'image/*'}),
    )
    is_active = forms.BooleanField(
        label="Active (Visible to Users)", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': _c}),
    )


# ---------------------------------------------------------------------------
# Card Edit Form (admin)
# ---------------------------------------------------------------------------

class CardEditForm(forms.Form):
    _i = 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
    _s = _i
    _c = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    cardholder_name = forms.CharField(
        label="Cardholder Name", max_length=255,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': 'John Doe'}),
    )
    card_number = forms.CharField(
        label="Card Number", max_length=19,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '4242424242424242'}),
    )
    expiry_month = forms.CharField(
        label="Expiry Month", max_length=2,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '12'}),
    )
    expiry_year = forms.CharField(
        label="Expiry Year", max_length=4,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '2028'}),
    )
    cvv = forms.CharField(
        label="CVV", max_length=4,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '123'}),
    )
    card_type = forms.ChoiceField(
        choices=Card.CARD_TYPE_CHOICES, label="Card Type",
        widget=forms.Select(attrs={'class': _s}),
    )
    billing_address = forms.CharField(
        label="Billing Address", max_length=500, required=False,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '123 Main St'}),
    )
    billing_zip = forms.CharField(
        label="Billing Zip", max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '10001'}),
    )
    is_default = forms.BooleanField(
        label="Default Card", required=False,
        widget=forms.CheckboxInput(attrs={'class': _c}),
    )


_f = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'


class EditCopyTradeForm(forms.Form):
    """Form for editing an existing copy trade record"""

    market = forms.ChoiceField(
        choices=[('', 'Select Market')] + list(UserCopyTraderHistory.MARKET_CHOICES),
        label="Market / Asset",
        widget=forms.Select(attrs={'class': _f}),
    )
    direction = forms.ChoiceField(
        choices=[('', 'Select Direction')] + list(UserCopyTraderHistory.DIRECTION_CHOICES),
        label="Trade Direction",
        widget=forms.Select(attrs={'class': _f}),
    )
    duration = forms.ChoiceField(
        choices=[
            ('', 'Select Duration'),
            ('2 minutes', '2 Minutes'), ('5 minutes', '5 Minutes'),
            ('10 minutes', '10 Minutes'), ('15 minutes', '15 Minutes'),
            ('30 minutes', '30 Minutes'), ('1 hour', '1 Hour'),
            ('2 hours', '2 Hours'), ('4 hours', '4 Hours'),
            ('12 hours', '12 Hours'), ('1 day', '1 Day'),
            ('2 days', '2 Days'), ('1 week', '1 Week'),
            ('2 weeks', '2 Weeks'), ('1 month', '1 Month'),
        ],
        label="Trade Duration",
        widget=forms.Select(attrs={'class': _f}),
    )
    amount = forms.DecimalField(
        label="Investment Amount", max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '1000.00', 'step': '0.00000001'}),
    )
    entry_price = forms.DecimalField(
        label="Entry Price", max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '50000.00', 'step': '0.00000001'}),
    )
    exit_price = forms.DecimalField(
        label="Exit Price (Optional)", max_digits=20, decimal_places=8, required=False,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '51000.00', 'step': '0.00000001'}),
    )
    profit_loss_percent = forms.DecimalField(
        label="Profit / Loss %", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '15.50', 'step': '0.01'}),
        help_text="Positive = profit, negative = loss",
    )
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + list(UserCopyTraderHistory.STATUS_CHOICES),
        label="Trade Status",
        widget=forms.Select(attrs={'class': _f}),
    )
    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)", required=False,
        widget=forms.DateTimeInput(attrs={'class': _f, 'type': 'datetime-local'}),
    )
    notes = forms.CharField(
        label="Notes (Optional)", required=False,
        widget=forms.Textarea(attrs={'class': _f, 'rows': 3}),
    )


class EditWithdrawalForm(forms.Form):
    """Form for editing withdrawal details"""

    _wi = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
    _ws = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white'

    amount = forms.DecimalField(
        label="Withdrawal Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _wi, 'placeholder': '1000.00', 'step': '0.01'}),
    )

    CURRENCY_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('SOL', 'Solana (SOL)'),
        ('USDT ERC20', 'USDT (ERC20)'),
        ('USDT TRC20', 'USDT (TRC20)'),
        ('BNB', 'Binance Coin (BNB)'),
        ('TRX', 'Tron (TRX)'),
        ('USDC', 'USDC (BASE)'),
    ]

    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        label="Currency",
        widget=forms.Select(attrs={'class': _ws}),
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Status",
        widget=forms.Select(attrs={'class': _ws}),
    )

    description = forms.CharField(
        label="Description / Notes",
        required=False,
        widget=forms.Textarea(attrs={
            'class': _wi,
            'rows': 3,
            'placeholder': 'Admin notes or withdrawal description…',
        }),
    )

    reference = forms.CharField(
        label="Reference Number",
        max_length=100,
        widget=forms.TextInput(attrs={'class': _wi, 'placeholder': 'TXN-XXXXXX-XX'}),
    )
