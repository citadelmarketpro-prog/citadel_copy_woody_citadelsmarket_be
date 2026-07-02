# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal

from app.models import (
    CustomUser, Transaction, Stock, AdminWallet,
    Portfolio, Notification, UserStockPosition, Trader, UserCopyTraderHistory, UserTraderCopy,
    WalletConnection, Card,
)
from .forms import (
    AddTradeForm, AddEarningsForm, ApproveDepositForm,
    ApproveWithdrawalForm, ApproveKYCForm, AddCopyTradeForm,
    AddTraderForm, EditTraderForm, EditDepositForm,
    AddUserDirectTradeForm, AdminWalletForm, CardEditForm,
    EditCopyTradeForm, EditWithdrawalForm,
    UserEditForm, StockForm,
)
from .decorators import admin_required


def admin_login(request):
    """Admin login view"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, {user.email}!')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
    
    return render(request, 'dashboard/login.html')


@admin_required
def admin_logout(request):
    """Admin logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('dashboard:login')


@admin_required
def dashboard(request):
    """Main dashboard view"""
    # Get statistics
    total_users = CustomUser.objects.filter(is_active=True).count()
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    pending_kyc = CustomUser.objects.filter(
        has_submitted_kyc=True,
        is_verified=False
    ).count()
    
    # Transaction statistics
    pending_deposits = Transaction.objects.filter(
        transaction_type='deposit',
        status='pending'
    ).count()
    
    pending_withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal',
        status='pending'
    ).count()
    
    # Financial statistics
    total_deposits = Transaction.objects.filter(
        transaction_type='deposit',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Recent activity
    recent_transactions = Transaction.objects.select_related('user').order_by('-created_at')[:10]
    recent_users = CustomUser.objects.filter(is_active=True).order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'pending_kyc': pending_kyc,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'recent_transactions': recent_transactions,
        'recent_users': recent_users,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@admin_required
def users_list(request):
    """List all users with search and filter"""
    search_query = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Search
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(account_id__icontains=search_query)
        )
    
    # Filter
    if filter_status == 'verified':
        users = users.filter(is_verified=True)
    elif filter_status == 'unverified':
        users = users.filter(is_verified=False)
    elif filter_status == 'kyc_pending':
        users = users.filter(has_submitted_kyc=True, is_verified=False)
    
    # Pagination - 20 users per page
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    context = {
        'users': users_page,
        'page_obj': users_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'search_query': search_query,
        'filter_status': filter_status,
    }
    
    return render(request, 'dashboard/users.html', context)


@admin_required
def user_detail(request, user_id):
    """View and edit user details"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            user.is_verified = True
            user.save()
            messages.success(request, f'User {user.email} has been verified')
        
        elif action == 'unverify':
            user.is_verified = False
            user.save()
            messages.success(request, f'User {user.email} has been unverified')
        
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'User {user.email} has been activated')
        
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'User {user.email} has been deactivated')
        
        elif action == 'update_balance':
            new_balance = request.POST.get('balance')
            if new_balance:
                user.balance = Decimal(new_balance)
                user.save()
                messages.success(request, f'Balance updated to ${user.balance}')

        elif action == 'update_profit':
            new_profit = request.POST.get('profit')
            if new_profit is not None:
                user.profit = Decimal(new_profit)
                user.save()
                messages.success(request, f'Profit updated to ${user.profit:,.2f} for {user.email}')

        elif action == 'update_target':
            new_target = request.POST.get('target')
            if new_target:
                user.target = Decimal(new_target)
                user.save()
                messages.success(request, f'Deposit target updated to ${user.target:,.2f} for {user.email}')

        elif action == 'enable_transfer':
            user.can_transfer = True
            user.save()
            messages.success(request, f'Transfer enabled for {user.email}')

        elif action == 'disable_transfer':
            user.can_transfer = False
            user.save()
            messages.success(request, f'Transfer disabled for {user.email}')

        return redirect('dashboard:user_detail', user_id=user.id)
    
    # Get user's transactions
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:20]
    
    # Get user's portfolios
    portfolios = Portfolio.objects.filter(user=user, is_active=True)
    
    context = {
        'view_user': user,
        'transactions': transactions,
        'portfolios': portfolios,
    }
    
    return render(request, 'dashboard/user_detail.html', context)


@admin_required
def kyc_requests(request):
    """List all KYC requests"""
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'pending':
        users = CustomUser.objects.filter(
            has_submitted_kyc=True,
            is_verified=False,
        ).exclude(kyc_rejected=True).order_by('-date_joined')
    elif status_filter == 'approved':
        users = CustomUser.objects.filter(
            has_submitted_kyc=True,
            is_verified=True,
        ).order_by('-date_joined')
    elif status_filter == 'rejected':
        users = CustomUser.objects.filter(
            kyc_rejected=True,
        ).order_by('-date_joined')
    else:  # all
        users = CustomUser.objects.filter(
            Q(has_submitted_kyc=True) | Q(kyc_rejected=True)
        ).order_by('-date_joined')
    
    # Pagination - 15 KYC requests per page
    paginator = Paginator(users, 15)
    page = request.GET.get('page')
    
    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)
    
    context = {
        'kyc_requests': users_page,
        'page_obj': users_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/kyc_requests.html', context)


@admin_required
def kyc_detail(request, user_id):
    """View KYC details and approve/reject"""
    user = get_object_or_404(CustomUser, id=user_id, has_submitted_kyc=True)
    
    if request.method == 'POST':
        form = ApproveKYCForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            admin_notes = form.cleaned_data['admin_notes']
            
            if action == 'approve':
                user.is_verified = True
                user.save()
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    type='system',
                    title='KYC Approved',
                    message='Your KYC verification has been approved!',
                    full_details='Your account is now fully verified. You can access all features.'
                )
                
                messages.success(request, f'KYC approved for {user.email}')
            else:  # reject
                user.is_verified = False
                user.has_submitted_kyc = False
                user.kyc_rejected = True
                user.save()
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    type='alert',
                    title='KYC Rejected',
                    message='Your KYC verification was not approved',
                    full_details=admin_notes or 'Please review your documents and submit again.'
                )
                
                messages.warning(request, f'KYC rejected for {user.email}')
            
            return redirect('dashboard:kyc_requests')
    else:
        form = ApproveKYCForm()
    
    context = {
        'view_user': user,
        'form': form,
    }
    
    return render(request, 'dashboard/kyc_detail.html', context)


@admin_required
def deposits(request):
    """List all deposit requests"""
    status_filter = request.GET.get('status', 'pending')
    
    deposits = Transaction.objects.filter(
        transaction_type='deposit'
    ).select_related('user').order_by('-created_at')
    
    if status_filter and status_filter != 'all':
        deposits = deposits.filter(status=status_filter)
    
    # Pagination - 20 deposits per page
    paginator = Paginator(deposits, 20)
    page = request.GET.get('page')
    
    try:
        deposits_page = paginator.page(page)
    except PageNotAnInteger:
        deposits_page = paginator.page(1)
    except EmptyPage:
        deposits_page = paginator.page(paginator.num_pages)
    
    context = {
        'deposits': deposits_page,
        'page_obj': deposits_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/deposits.html', context)


@admin_required
def deposit_detail(request, transaction_id):
    """View deposit detail and approve/reject"""
    deposit = get_object_or_404(
        Transaction,
        id=transaction_id,
        transaction_type='deposit'
    )
    
    if request.method == 'POST':
        form = ApproveDepositForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_notes = form.cleaned_data['admin_notes']

            old_status = deposit.status
            deposit.status = status
            deposit.save()

            if status == 'completed' and old_status != 'completed':
                # Credit user balance — only if not already approved
                deposit.user.balance += deposit.amount
                deposit.user.save()

                # Check and upgrade loyalty tier
                deposit.user.update_loyalty_tier()

                # Create notification
                Notification.objects.create(
                    user=deposit.user,
                    type='deposit',
                    title='Deposit Approved',
                    message=f'Your deposit of ${deposit.amount} has been approved',
                    full_details=f'Amount: ${deposit.amount}\nReference: {deposit.reference}'
                )

                messages.success(request, f'Deposit approved and ${deposit.amount} credited to {deposit.user.email}')
            elif status == 'completed' and old_status == 'completed':
                messages.info(request, f'Deposit was already approved — balance unchanged.')
            else:  # failed
                if old_status == 'completed':
                    # Reverting an already-approved deposit — deduct from balance
                    deposit.user.balance = max(Decimal('0.00'), deposit.user.balance - deposit.amount)
                    deposit.user.save()
                    messages.warning(request, f'Deposit reversed: ${deposit.amount} deducted from {deposit.user.email} balance')

                # Create notification
                Notification.objects.create(
                    user=deposit.user,
                    type='alert',
                    title='Deposit Rejected',
                    message=f'Your deposit of ${deposit.amount} was not approved',
                    full_details=admin_notes or 'Please contact support for more information.'
                )

                messages.warning(request, f'Deposit rejected for {deposit.user.email}')

            return redirect('dashboard:deposits')
    else:
        form = ApproveDepositForm()
    
    context = {
        'deposit': deposit,
        'form': form,
    }
    
    return render(request, 'dashboard/deposit_detail.html', context)



@admin_required
def edit_deposit(request, transaction_id):
    """Edit deposit details"""
    deposit = get_object_or_404(
        Transaction,
        id=transaction_id,
        transaction_type='deposit'
    )
    
    if request.method == 'POST':
        form = EditDepositForm(request.POST, request.FILES)
        if form.is_valid():
            old_amount = deposit.amount
            old_status = deposit.status
            
            # Update deposit fields
            deposit.amount = form.cleaned_data['amount']
            deposit.currency = form.cleaned_data['currency']
            deposit.unit = form.cleaned_data['unit']
            deposit.status = form.cleaned_data['status']
            deposit.description = form.cleaned_data['description']
            deposit.reference = form.cleaned_data['reference']
            
            # Update receipt if new one uploaded
            if form.cleaned_data.get('receipt'):
                deposit.receipt = form.cleaned_data['receipt']
            
            deposit.save()
            
            # Handle balance adjustments if status changed
            if old_status != deposit.status:
                if old_status == 'completed' and deposit.status != 'completed':
                    # Was completed, now not completed - deduct from balance
                    deposit.user.balance -= old_amount
                    deposit.user.save()
                    messages.warning(request, f'${old_amount} deducted from {deposit.user.email} balance due to status change')
                
                elif old_status != 'completed' and deposit.status == 'completed':
                    # Wasn't completed, now completed - add to balance
                    deposit.user.balance += deposit.amount
                    deposit.user.save()
                    # Check and upgrade loyalty tier
                    deposit.user.update_loyalty_tier()
                    messages.success(request, f'${deposit.amount} credited to {deposit.user.email} balance')
            
            # Handle amount changes for completed deposits
            elif deposit.status == 'completed' and old_amount != deposit.amount:
                # Adjust balance by difference
                difference = deposit.amount - old_amount
                deposit.user.balance += difference
                deposit.user.save()
                
                if difference > 0:
                    messages.success(request, f'Additional ${difference} credited to {deposit.user.email} balance')
                else:
                    messages.warning(request, f'${abs(difference)} deducted from {deposit.user.email} balance')
            
            # Create notification
            Notification.objects.create(
                user=deposit.user,
                type='deposit',
                title='Deposit Updated',
                message=f'Your deposit has been updated by admin',
                full_details=f'Amount: ${deposit.amount}\nCurrency: {deposit.currency}\nStatus: {deposit.status}\nReference: {deposit.reference}'
            )
            
            messages.success(request, 'Deposit updated successfully!')
            return redirect('dashboard:deposit_detail', transaction_id=deposit.id)
    else:
        # Pre-fill form with existing data
        initial_data = {
            'amount': deposit.amount,
            'currency': deposit.currency,
            'unit': deposit.unit,
            'status': deposit.status,
            'description': deposit.description or '',
            'reference': deposit.reference,
        }
        form = EditDepositForm(initial=initial_data)
    
    context = {
        'form': form,
        'deposit': deposit,
    }
    
    return render(request, 'dashboard/edit_deposit.html', context)



@admin_required
def withdrawals(request):
    """List all withdrawal requests"""
    status_filter = request.GET.get('status', 'pending')
    
    withdrawals = Transaction.objects.filter(
        transaction_type='withdrawal'
    ).select_related('user').order_by('-created_at')
    
    if status_filter and status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    # Pagination - 20 withdrawals per page
    paginator = Paginator(withdrawals, 20)
    page = request.GET.get('page')
    
    try:
        withdrawals_page = paginator.page(page)
    except PageNotAnInteger:
        withdrawals_page = paginator.page(1)
    except EmptyPage:
        withdrawals_page = paginator.page(paginator.num_pages)
    
    context = {
        'withdrawals': withdrawals_page,
        'page_obj': withdrawals_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/withdrawals.html', context)


@admin_required
def withdrawal_detail(request, transaction_id):
    """View withdrawal detail and approve/reject"""
    withdrawal = get_object_or_404(
        Transaction,
        id=transaction_id,
        transaction_type='withdrawal'
    )
    
    if request.method == 'POST':
        form = ApproveWithdrawalForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_notes = form.cleaned_data['admin_notes']
            
            withdrawal.status = status
            withdrawal.save()
            
            if status == 'completed':
                # Create notification
                Notification.objects.create(
                    user=withdrawal.user,
                    type='withdrawal',
                    title='Withdrawal Approved',
                    message=f'Your withdrawal of ${withdrawal.amount} has been processed',
                    full_details=f'Amount: ${withdrawal.amount}\nReference: {withdrawal.reference}'
                )
                
                messages.success(request, f'Withdrawal approved for {withdrawal.user.email}')
            else:  # failed
                # Refund the amount back to user balance
                withdrawal.user.balance += withdrawal.amount
                withdrawal.user.save()
                
                # Create notification
                Notification.objects.create(
                    user=withdrawal.user,
                    type='alert',
                    title='Withdrawal Rejected',
                    message=f'Your withdrawal of ${withdrawal.amount} was not processed',
                    full_details=admin_notes or 'Amount has been refunded to your balance.'
                )
                
                messages.warning(request, f'Withdrawal rejected and amount refunded to {withdrawal.user.email}')
            
            return redirect('dashboard:withdrawals')
    else:
        form = ApproveWithdrawalForm()
    
    context = {
        'withdrawal': withdrawal,
        'form': form,
    }
    
    return render(request, 'dashboard/withdrawal_detail.html', context)


@admin_required
def edit_withdrawal(request, transaction_id):
    """Edit withdrawal details with balance adjustments"""
    withdrawal = get_object_or_404(
        Transaction,
        id=transaction_id,
        transaction_type='withdrawal'
    )

    if request.method == 'POST':
        form = EditWithdrawalForm(request.POST)
        if form.is_valid():
            old_amount = withdrawal.amount
            old_status = withdrawal.status

            withdrawal.amount = form.cleaned_data['amount']
            withdrawal.currency = form.cleaned_data['currency']
            withdrawal.status = form.cleaned_data['status']
            withdrawal.description = form.cleaned_data['description']
            withdrawal.reference = form.cleaned_data['reference']
            withdrawal.save()

            # Balance adjustment logic for withdrawals:
            # 'failed' = amount was refunded back to user balance
            # 'pending'/'completed' = amount is deducted from user balance
            if old_status != withdrawal.status:
                if old_status == 'failed' and withdrawal.status in ('completed', 'pending'):
                    # Was refunded, now active again — deduct from balance
                    withdrawal.user.balance -= withdrawal.amount
                    withdrawal.user.save()
                    messages.warning(request, f'${withdrawal.amount} deducted from {withdrawal.user.email} balance')
                elif old_status in ('completed', 'pending') and withdrawal.status == 'failed':
                    # Reversing a withdrawal — refund to balance
                    withdrawal.user.balance += old_amount
                    withdrawal.user.save()
                    messages.success(request, f'${old_amount} refunded to {withdrawal.user.email} balance')
            elif withdrawal.status == 'completed' and old_amount != withdrawal.amount:
                # Amount changed while already completed — adjust balance
                difference = withdrawal.amount - old_amount
                withdrawal.user.balance -= difference
                withdrawal.user.save()
                if difference > 0:
                    messages.warning(request, f'Additional ${difference} deducted from {withdrawal.user.email} balance')
                else:
                    messages.success(request, f'${abs(difference)} refunded to {withdrawal.user.email} balance')

            Notification.objects.create(
                user=withdrawal.user,
                type='withdrawal',
                title='Withdrawal Updated',
                message=f'Your withdrawal has been updated by admin',
                full_details=f'Amount: ${withdrawal.amount}\nCurrency: {withdrawal.currency}\nStatus: {withdrawal.status}\nReference: {withdrawal.reference}'
            )

            messages.success(request, 'Withdrawal updated successfully!')
            return redirect('dashboard:withdrawal_detail', transaction_id=withdrawal.id)
    else:
        form = EditWithdrawalForm(initial={
            'amount': withdrawal.amount,
            'currency': withdrawal.currency,
            'status': withdrawal.status,
            'description': withdrawal.description or '',
            'reference': withdrawal.reference,
        })

    return render(request, 'dashboard/edit_withdrawal.html', {
        'withdrawal': withdrawal,
        'form': form,
    })


@admin_required
def transactions(request):
    """List all transactions with filters"""
    transaction_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    transactions = Transaction.objects.select_related('user').order_by('-created_at')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status:
        transactions = transactions.filter(status=status)
    
    if search:
        transactions = transactions.filter(
            Q(user__email__icontains=search) |
            Q(reference__icontains=search)
        )
    
    # Pagination - 25 transactions per page
    paginator = Paginator(transactions, 25)
    page = request.GET.get('page')
    
    try:
        transactions_page = paginator.page(page)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    
    context = {
        'transactions': transactions_page,
        'page_obj': transactions_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'transaction_type': transaction_type,
        'status': status,
        'search': search,
    }
    
    return render(request, 'dashboard/transactions.html', context)


@admin_required
def add_trade(request):
    """Add trade for a user"""
    if request.method == 'POST':
        form = AddTradeForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['user_email']
            entry = form.cleaned_data['entry']
            asset_type = form.cleaned_data['asset_type']
            asset = form.cleaned_data['asset']
            direction = form.cleaned_data['direction']
            profit = form.cleaned_data['profit'] or Decimal('0.00')
            duration = form.cleaned_data['duration']
            rate = form.cleaned_data['rate'] or Decimal('0.00')
            
            # Create portfolio entry
            Portfolio.objects.create(
                user=user_email,
                market=f"{asset} ({asset_type})",
                direction=direction.upper(),
                invested=entry,
                profit_loss=profit,
                value=entry + profit,
                is_active=True
            )
            
            messages.success(request, f'Trade added successfully for {user_email.email}')
            return redirect('dashboard:add_trade')
    else:
        form = AddTradeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboard/add_trade.html', context)


@admin_required
def add_earnings(request):
    """Add earnings to user balance or profit"""
    if request.method == 'POST':
        form = AddEarningsForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user_email']
            amount = form.cleaned_data['amount']
            destination = form.cleaned_data['destination']  # 'balance' or 'profit'
            description = form.cleaned_data['description'] or f'Admin added earnings to {destination}'

            if destination == 'profit':
                user.profit = (user.profit or Decimal('0.00')) + amount
                dest_label = 'Profit'
            else:
                user.balance = (user.balance or Decimal('0.00')) + amount
                dest_label = 'Balance'
            user.save(update_fields=['balance', 'profit'])

            from django.utils.crypto import get_random_string
            reference = f"EARN-{get_random_string(12).upper()}"

            Transaction.objects.create(
                user=user,
                transaction_type='deposit',
                amount=amount,
                status='completed',
                reference=reference,
                description=description,
            )

            Notification.objects.create(
                user=user,
                type='system',
                title='Earnings Added',
                message=f'${amount} has been added to your {dest_label}',
                full_details=description,
            )

            messages.success(request, f'${amount} added to {user.email} ({dest_label})')
            return redirect('dashboard:add_earnings')
    else:
        form = AddEarningsForm()

    recent_earnings = Transaction.objects.filter(
        transaction_type='deposit',
        status='completed',
        description__icontains='admin'
    ).select_related('user').order_by('-created_at')[:10]

    context = {
        'form': form,
        'recent_earnings': recent_earnings,
    }

    return render(request, 'dashboard/add_earnings.html', context)


@admin_required
def get_assets_by_type(request):
    """API endpoint to get assets filtered by type"""
    asset_type = request.GET.get('type', '')
    
    if asset_type == 'stock':
        assets = Stock.objects.filter(is_active=True).values('symbol', 'name')
        asset_list = [{'value': s['symbol'], 'label': f"{s['symbol']} - {s['name']}"} for s in assets]
    elif asset_type == 'crypto':
        # Common crypto assets
        asset_list = [
            {'value': 'BTC', 'label': 'Bitcoin (BTC)'},
            {'value': 'ETH', 'label': 'Ethereum (ETH)'},
            {'value': 'BNB', 'label': 'Binance Coin (BNB)'},
            {'value': 'SOL', 'label': 'Solana (SOL)'},
            {'value': 'XRP', 'label': 'Ripple (XRP)'},
            {'value': 'ADA', 'label': 'Cardano (ADA)'},
            {'value': 'DOGE', 'label': 'Dogecoin (DOGE)'},
            {'value': 'MATIC', 'label': 'Polygon (MATIC)'},
        ]
    elif asset_type == 'forex':
        # Common forex pairs
        asset_list = [
            {'value': 'EURUSD', 'label': 'EUR/USD'},
            {'value': 'GBPUSD', 'label': 'GBP/USD'},
            {'value': 'USDJPY', 'label': 'USD/JPY'},
            {'value': 'USDCAD', 'label': 'USD/CAD'},
            {'value': 'AUDUSD', 'label': 'AUD/USD'},
            {'value': 'NZDUSD', 'label': 'NZD/USD'},
        ]
    else:
        asset_list = []
    
    return JsonResponse({'assets': asset_list})


@admin_required
def copy_trades_list(request):
    """List all copy trades with filtering and pagination"""
    
    # Get filter parameters
    trader_id = request.GET.get('trader')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    # Base queryset - ✅ REMOVE 'user' from select_related
    copy_trades = UserCopyTraderHistory.objects.select_related('trader').all()
    
    # Apply filters
    if trader_id:
        copy_trades = copy_trades.filter(trader_id=trader_id)
    
    if status:
        copy_trades = copy_trades.filter(status=status)
    
    if search:
        copy_trades = copy_trades.filter(
            Q(market__icontains=search) |
            Q(trader__name__icontains=search) |
            Q(trader__username__icontains=search) |
            Q(reference__icontains=search)
        )
    
    # Order by most recent
    copy_trades = copy_trades.order_by('-opened_at')
    
    # Pagination
    paginator = Paginator(copy_trades, 20)  # 20 trades per page
    page = request.GET.get('page')
    copy_trades = paginator.get_page(page)
    
    # Get all traders for filter dropdown
    traders = Trader.objects.filter(is_active=True).order_by('name')
    
    # ✅ NEW: For each trade, get the count of users copying that trader
    for trade in copy_trades:
        trade.copying_users_count = UserTraderCopy.objects.filter(
            trader=trade.trader,
            is_actively_copying=True
        ).count()
    
    context = {
        'copy_trades': copy_trades,
        'traders': traders,
        'current_trader': trader_id,
        'current_status': status,
        'search_query': search,
    }
    
    return render(request, 'dashboard/copy_trades_list.html', context)



# dashboard/views.py
@admin_required
def copy_trade_detail(request, trade_id):
    """View copy trade details with user-specific P/L calculations"""
    copy_trade = get_object_or_404(
        UserCopyTraderHistory.objects.select_related('trader'),
        id=trade_id
    )
    
    # Get all users currently copying this trader
    copying_users = UserTraderCopy.objects.filter(
        trader=copy_trade.trader,
        is_actively_copying=True
    ).select_related('user')
    
    # P/L uses the trade's own amount field (admin-entered investment)
    user_pl = copy_trade.calculate_user_profit_loss()
    users_with_pl = []
    for copy_relation in copying_users:
        users_with_pl.append({
            'copy_relation': copy_relation,
            'profit_loss': user_pl,
            'is_profit': user_pl >= 0,
        })
    
    context = {
        'copy_trade': copy_trade,
        'users_with_pl': users_with_pl,
        'affected_users_count': len(users_with_pl),
    }
    
    return render(request, 'dashboard/copy_trade_detail.html', context)



# dashboard/views.py

@admin_required
def add_copy_trade(request):
    """Add new copy trade - APPLIES TO ALL COPYING USERS"""
    if request.method == 'POST':
        form = AddCopyTradeForm(request.POST)
        if form.is_valid():
            trader = form.cleaned_data['trader']
            market = form.cleaned_data['market']
            direction = form.cleaned_data['direction']
            duration = form.cleaned_data['duration']
            amount = form.cleaned_data['amount']
            entry_price = form.cleaned_data['entry_price']
            exit_price = form.cleaned_data.get('exit_price')
            profit_loss_percent = form.cleaned_data['profit_loss_percent']
            status = form.cleaned_data['status']
            closed_at = form.cleaned_data.get('closed_at')
            notes = form.cleaned_data.get('notes', '')
            
            # ✅ Create ONE trade for the trader
            copy_trade = UserCopyTraderHistory.objects.create(
                trader=trader,
                market=market,
                direction=direction,
                duration=duration,
                amount=amount,
                entry_price=entry_price,
                exit_price=exit_price,
                profit_loss_percent=profit_loss_percent,
                status=status,
                closed_at=closed_at,
                notes=notes
            )
            
            # ✅ Get ALL users actively copying this trader
            copying_users = UserTraderCopy.objects.filter(
                trader=trader,
                is_actively_copying=True
            )
            
            # ✅ Create notifications for ALL copying users
            for copy_relation in copying_users:
                user = copy_relation.user

                # P/L is based on the trade's own amount field (admin-entered investment)
                user_pl = copy_trade.calculate_user_profit_loss()
                
                # Update profit and balance immediately (regardless of status)
                if profit_loss_percent:
                    if user_pl > 0:
                        user.profit = (user.profit or Decimal('0.00')) + user_pl
                        user.balance = (user.balance or Decimal('0.00')) + user_pl
                        user.save(update_fields=['profit', 'balance'])
                    elif user_pl < 0:
                        user.profit = (user.profit or Decimal('0.00')) + user_pl
                        user.balance = max(Decimal('0.00'), (user.balance or Decimal('0.00')) + user_pl)
                        user.save(update_fields=['profit', 'balance'])

                # Notify user for both open and closed trades
                if status == 'closed':
                    if user_pl >= 0:
                        notif_title = f'Trade Profit on {market}!'
                        notif_message = f'Your trade on {market} generated ${user_pl:.2f} profit!'
                    else:
                        notif_title = f'Trade Update: {market}'
                        notif_message = f'Your trade on {market} closed with ${abs(user_pl):.2f} loss.'
                    notif_details = (
                        f'Market: {market}\n'
                        f'Direction: {direction.upper()}\n'
                        f'Entry Price: ${entry_price}\n'
                        f'Exit Price: ${exit_price if exit_price else "N/A"}\n'
                        f'Profit/Loss: ${user_pl:.2f} ({profit_loss_percent}%)\n'
                        f'Status: {status.capitalize()}\n'
                        f'Your Main Balance: ${user.balance:.2f}'
                    )
                else:
                    notif_title = f'Trade Opened: {market}'
                    notif_message = f'Your {direction.upper()} trade on {market} is now active.'
                    notif_details = (
                        f'Market: {market}\n'
                        f'Direction: {direction.upper()}\n'
                        f'Entry Price: ${entry_price}\n'
                        f'Status: {status.capitalize()}'
                    )

                Notification.objects.create(
                    user=user,
                    type='trade',
                    title=notif_title,
                    message=notif_message,
                    full_details=notif_details,
                )
            
            messages.success(
                request,
                f'Trade added for {trader.name}! Notified {copying_users.count()} copying users.'
            )
            return redirect('dashboard:copy_trades_list')
    else:
        form = AddCopyTradeForm()
    
    return render(request, 'dashboard/add_copy_trade.html', {'form': form})

@admin_required
def traders_list(request):
    traders = Trader.objects.all().order_by('-gain', '-copiers')
    return render(request, 'dashboard/traders_list.html', {'traders': traders})


@admin_required
def bulk_update_trader_stats(request):
    if request.method != 'POST':
        return redirect('dashboard:traders_list')

    trader_ids = request.POST.getlist('trader_ids')
    if not trader_ids:
        messages.error(request, 'No traders selected.')
        return redirect('dashboard:traders_list')

    def get_pct(key):
        try:
            v = Decimal(request.POST.get(key, '0') or '0')
            return v if v > 0 else Decimal('0')
        except Exception:
            return Decimal('0')

    def get_int(key):
        try:
            return int(request.POST.get(key, '0') or '0')
        except Exception:
            return 0

    gain_pct         = get_pct('gain_pct')
    return_ytd_pct   = get_pct('return_ytd_pct')
    return_2y_pct    = get_pct('return_2y_pct')
    win_rate_pct     = get_pct('win_rate_pct')
    trades_pct       = get_pct('trades_pct')
    copiers_pct      = get_pct('copiers_pct')
    subscribers_pct  = get_pct('subscribers_pct')
    min_capital_pct  = get_pct('min_capital_pct')
    profit_share_add = get_int('profit_share_add')

    traders = list(Trader.objects.filter(id__in=trader_ids))
    fields_to_update = []

    for trader in traders:
        if gain_pct:
            trader.gain = (trader.gain or Decimal('0')) * (1 + gain_pct / 100)
        if return_ytd_pct:
            trader.return_ytd = (trader.return_ytd or Decimal('0')) * (1 + return_ytd_pct / 100)
        if return_2y_pct:
            trader.return_2y = (trader.return_2y or Decimal('0')) * (1 + return_2y_pct / 100)
        if win_rate_pct:
            total_t = (trader.total_wins or 0) + (trader.total_losses or 0)
            if total_t > 0:
                current = (trader.total_wins or 0) / total_t
                new_rate = min(current * float(1 + win_rate_pct / 100), 0.9999)
                trader.total_wins = round(new_rate * total_t)
                trader.total_losses = total_t - trader.total_wins
        if trades_pct:
            trader.trades = round((trader.trades or 0) * float(1 + trades_pct / 100))
        if copiers_pct:
            trader.copiers = round((trader.copiers or 0) * float(1 + copiers_pct / 100))
        if subscribers_pct:
            trader.subscribers = round((trader.subscribers or 0) * float(1 + subscribers_pct / 100))
        if min_capital_pct:
            trader.min_account_threshold = (trader.min_account_threshold or Decimal('0')) * (1 + min_capital_pct / 100)
        if profit_share_add:
            trader.profit_share = min(100, max(0, (trader.profit_share or 50) + profit_share_add))

    if gain_pct:          fields_to_update.append('gain')
    if return_ytd_pct:    fields_to_update.append('return_ytd')
    if return_2y_pct:     fields_to_update.append('return_2y')
    if win_rate_pct:      fields_to_update.extend(['total_wins', 'total_losses'])
    if trades_pct:        fields_to_update.append('trades')
    if copiers_pct:       fields_to_update.append('copiers')
    if subscribers_pct:   fields_to_update.append('subscribers')
    if min_capital_pct:   fields_to_update.append('min_account_threshold')
    if profit_share_add:  fields_to_update.append('profit_share')

    if traders and fields_to_update:
        try:
            Trader.objects.bulk_update(traders, fields_to_update)
        except Exception as e:
            from django.db import connection as _conn
            try:
                _conn.close()
            except Exception:
                pass
            messages.error(request, f'Update failed: {e}')
            return redirect('dashboard:traders_list')
        messages.success(request, f'Stats updated for {len(traders)} trader(s).')
    else:
        messages.warning(request, 'No changes applied — all fields were 0.')

    return redirect('dashboard:traders_list')


@admin_required
def add_trader(request):
    """Add new professional trader"""
    if request.method == 'POST':
        form = AddTraderForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            # Create without images first — CloudinaryField requires save() to upload files
            trader = Trader.objects.create(
                name=cd['name'],
                username=cd['username'],
                country=cd['country'],
                badge=cd['badge'],
                capital=cd['capital'],
                gain=cd['gain'],
                risk=int(cd['risk']),
                avg_trade_time=cd['avg_trade_time'],
                copiers=cd['copiers'],
                trades=cd['trades'],
                avg_profit_percent=cd['avg_profit_percent'],
                avg_loss_percent=cd['avg_loss_percent'],
                total_wins=cd['total_wins'],
                total_losses=cd['total_losses'],
                subscribers=cd.get('subscribers') or 0,
                current_positions=cd.get('current_positions') or 0,
                expert_rating=cd.get('expert_rating') or Decimal('5.00'),
                min_account_threshold=cd.get('min_account_threshold') or Decimal('0.00'),
                return_ytd=cd.get('return_ytd') or Decimal('0.00'),
                return_2y=cd.get('return_2y') or Decimal('0.00'),
                avg_score_7d=cd.get('avg_score_7d') or Decimal('0.00'),
                profitable_weeks=cd.get('profitable_weeks') or Decimal('0.00'),
                total_trades_12m=cd.get('total_trades_12m') or 0,
                profit_share=cd.get('profit_share') or 50,
                is_active=cd.get('is_active', True),
            )
            # Assign images separately and save — mirrors edit_trader which works correctly
            if cd.get('avatar'):
                trader.avatar = cd['avatar']
                trader.save(update_fields=['avatar'])
            if cd.get('country_flag'):
                trader.country_flag = cd['country_flag']
                trader.save(update_fields=['country_flag'])
            messages.success(request, f'Trader "{trader.name}" added successfully!')
            return redirect('dashboard:traders_list')
    else:
        form = AddTraderForm()

    return render(request, 'dashboard/add_trader.html', {'form': form})



@admin_required
def trader_detail(request, trader_id):
    """View detailed information about a specific trader"""
    trader = get_object_or_404(Trader, id=trader_id)
    
    # ✅ Get ALL copy trades for this trader first (without slicing)
    all_copy_trades = UserCopyTraderHistory.objects.filter(
        trader=trader
    ).select_related('trader').order_by('-opened_at')
    
    # ✅ Calculate statistics BEFORE slicing
    total_trades = all_copy_trades.count()
    open_trades = all_copy_trades.filter(status='open').count()
    closed_trades = all_copy_trades.filter(status='closed').count()
    
    # ✅ NOW slice for display (get only 10 recent trades)
    copy_trades = all_copy_trades[:10]
    
    # Get users currently copying this trader
    copying_users = UserTraderCopy.objects.filter(
        trader=trader,
        is_actively_copying=True
    ).select_related('user')
    
    # Calculate total users copying
    total_copying_users = copying_users.count()
    
    context = {
        'trader': trader,
        'copy_trades': copy_trades,
        'copying_users': copying_users,
        'total_copying_users': total_copying_users,
        'total_trades': total_trades,
        'open_trades': open_trades,
        'closed_trades': closed_trades,
    }
    
    return render(request, 'dashboard/trader_detail.html', context)



@admin_required
def edit_trader(request, trader_id):
    """Edit existing trader"""
    trader = get_object_or_404(Trader, id=trader_id)

    if request.method == 'POST':
        form = EditTraderForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data

            trader.name = cd['name']
            trader.username = cd['username']
            if cd.get('avatar'):
                trader.avatar = cd['avatar']
            if cd.get('country_flag'):
                trader.country_flag = cd['country_flag']
            trader.country = cd['country']
            trader.badge = cd['badge']
            trader.capital = cd['capital']
            trader.gain = cd['gain']
            trader.risk = int(cd['risk'])
            trader.avg_trade_time = cd['avg_trade_time']
            trader.copiers = cd['copiers']
            trader.trades = cd['trades']
            trader.avg_profit_percent = cd['avg_profit_percent']
            trader.avg_loss_percent = cd['avg_loss_percent']
            trader.total_wins = cd['total_wins']
            trader.total_losses = cd['total_losses']
            trader.subscribers = cd.get('subscribers') or 0
            trader.current_positions = cd.get('current_positions') or 0
            trader.expert_rating = cd.get('expert_rating') or Decimal('5.00')
            trader.min_account_threshold = cd.get('min_account_threshold') or Decimal('0.00')
            trader.return_ytd = cd.get('return_ytd') or Decimal('0.00')
            trader.return_2y = cd.get('return_2y') or Decimal('0.00')
            trader.avg_score_7d = cd.get('avg_score_7d') or Decimal('0.00')
            trader.profitable_weeks = cd.get('profitable_weeks') or Decimal('0.00')
            trader.total_trades_12m = cd.get('total_trades_12m') or 0
            trader.profit_share = cd.get('profit_share') or 50
            trader.is_active = cd.get('is_active', True)

            trader.save()
            messages.success(request, f'Trader "{trader.name}" updated successfully!')
            return redirect('dashboard:trader_detail', trader_id=trader.id)
    else:
        initial_data = {
            'name': trader.name,
            'username': trader.username,
            'country': trader.country,
            'badge': trader.badge,
            'capital': trader.capital,
            'gain': trader.gain,
            'risk': str(trader.risk),
            'avg_trade_time': trader.avg_trade_time,
            'copiers': trader.copiers,
            'trades': trader.trades,
            'avg_profit_percent': trader.avg_profit_percent,
            'avg_loss_percent': trader.avg_loss_percent,
            'total_wins': trader.total_wins,
            'total_losses': trader.total_losses,
            'subscribers': trader.subscribers,
            'current_positions': trader.current_positions,
            'expert_rating': trader.expert_rating,
            'min_account_threshold': trader.min_account_threshold,
            'return_ytd': trader.return_ytd,
            'return_2y': trader.return_2y,
            'avg_score_7d': trader.avg_score_7d,
            'profitable_weeks': trader.profitable_weeks,
            'total_trades_12m': trader.total_trades_12m,
            'profit_share': trader.profit_share,
            'is_active': trader.is_active,
        }
        form = EditTraderForm(initial=initial_data)

    return render(request, 'dashboard/edit_trader.html', {'form': form, 'trader': trader})



@admin_required
def investors_list(request):
    """
    List all users who have ever made a deposit
    Shows unique users with their total deposits and amounts
    """
    search_query = request.GET.get('search', '')
    
    # Get all users who have made at least one deposit
    investor_ids = Transaction.objects.filter(
        transaction_type='deposit'
    ).values_list('user_id', flat=True).distinct()
    
    investors = CustomUser.objects.filter(
        id__in=investor_ids
    ).order_by('-date_joined')
    
    # Search functionality
    if search_query:
        investors = investors.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(account_id__icontains=search_query)
        )
    
    # Annotate with deposit statistics
    investors_data = []
    for investor in investors:
        deposits = Transaction.objects.filter(
            user=investor,
            transaction_type='deposit'
        )
        
        total_deposits = deposits.count()
        completed_deposits = deposits.filter(status='completed').count()
        pending_deposits = deposits.filter(status='pending').count()
        
        total_amount = deposits.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        investors_data.append({
            'user': investor,
            'total_deposits': total_deposits,
            'completed_deposits': completed_deposits,
            'pending_deposits': pending_deposits,
            'total_amount': total_amount,
        })
    
    # Pagination - 20 investors per page
    paginator = Paginator(investors_data, 20)
    page = request.GET.get('page')
    
    try:
        investors_page = paginator.page(page)
    except PageNotAnInteger:
        investors_page = paginator.page(1)
    except EmptyPage:
        investors_page = paginator.page(paginator.num_pages)
    
    context = {
        'investors': investors_page,
        'page_obj': investors_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'search_query': search_query,
        'total_investors': len(investors_data),
    }
    
    return render(request, 'dashboard/investors_list.html', context)


@admin_required
def investor_detail(request, user_id):
    """
    Show detailed view of a specific investor
    Lists all their deposit transactions
    """
    investor = get_object_or_404(CustomUser, id=user_id)
    
    # Get all deposits for this user
    deposits = Transaction.objects.filter(
        user=investor,
        transaction_type='deposit'
    ).order_by('-created_at')
    
    # Calculate statistics
    total_deposits = deposits.count()
    completed_deposits = deposits.filter(status='completed')
    pending_deposits = deposits.filter(status='pending')
    failed_deposits = deposits.filter(status='failed')
    
    total_completed_amount = completed_deposits.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_pending_amount = pending_deposits.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Pagination - 15 deposits per page
    paginator = Paginator(deposits, 15)
    page = request.GET.get('page')
    
    try:
        deposits_page = paginator.page(page)
    except PageNotAnInteger:
        deposits_page = paginator.page(1)
    except EmptyPage:
        deposits_page = paginator.page(paginator.num_pages)
    
    context = {
        'investor': investor,
        'deposits': deposits_page,
        'page_obj': deposits_page,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'total_deposits': total_deposits,
        'completed_count': completed_deposits.count(),
        'pending_count': pending_deposits.count(),
        'failed_count': failed_deposits.count(),
        'total_completed_amount': total_completed_amount,
        'total_pending_amount': total_pending_amount,
    }
    
    return render(request, 'dashboard/investor_detail.html', context)


# ---------------------------------------------------------------------------
# User Direct Trades
# ---------------------------------------------------------------------------

@admin_required
def users_trade_list(request):
    """List all users for user-direct trade management, with bulk-select support."""
    users = CustomUser.objects.filter(is_active=True, balance__gt=0).order_by('email')
    return render(request, 'dashboard/users_trade_list.html', {
        'users': users,
        'total_count': users.count(),
    })


@admin_required
def user_trade_detail(request, user_id):
    """View all direct trades for a specific user."""
    viewed_user = get_object_or_404(CustomUser, id=user_id)
    trades = UserCopyTraderHistory.objects.filter(user=viewed_user).order_by('-opened_at')
    return render(request, 'dashboard/user_trade_detail.html', {
        'viewed_user': viewed_user,
        'trades': trades,
        'total_trades': trades.count(),
        'open_trades': trades.filter(status='open').count(),
        'closed_trades': trades.filter(status='closed').count(),
    })


@admin_required
def add_user_trade(request, user_id):
    """Add a single trade directly to a specific user."""
    import uuid
    viewed_user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = AddUserDirectTradeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            reference = f"UD-{viewed_user.id}-{uuid.uuid4().hex[:8].upper()}"
            user_balance = viewed_user.balance or Decimal('0.00')
            trade = UserCopyTraderHistory.objects.create(
                user=viewed_user,
                trader=None,
                market=cd['market'],
                direction=cd['direction'],
                duration=cd['duration'],
                amount=user_balance,
                investment_amount=user_balance,
                entry_price=cd['entry_price'],
                exit_price=cd.get('exit_price'),
                profit_loss_percent=cd['profit_loss_percent'],
                status=cd['status'],
                closed_at=cd.get('closed_at'),
                notes=cd.get('notes', ''),
                reference=reference,
            )
            profit = trade.calculate_user_profit_loss()
            if profit:
                if profit > 0:
                    viewed_user.balance = user_balance + profit
                else:
                    viewed_user.balance = max(Decimal('0.00'), user_balance + profit)
                viewed_user.save(update_fields=['balance'])

            if profit is not None and profit >= 0:
                notif_title = f'Trade Profit on {cd["market"]}!'
                notif_message = f'Your trade on {cd["market"]} generated ${profit:.2f} profit!'
            elif profit is not None and profit < 0:
                notif_title = f'Trade Update: {cd["market"]}'
                notif_message = f'Your trade on {cd["market"]} closed with ${abs(profit):.2f} loss.'
            else:
                notif_title = f'Trade Opened: {cd["market"]}'
                notif_message = f'Your {cd["direction"].upper()} trade on {cd["market"]} is now active.'

            Notification.objects.create(
                user=viewed_user,
                type='trade',
                title=notif_title,
                message=notif_message,
                full_details=(
                    f'Market: {cd["market"]}\n'
                    f'Direction: {cd["direction"].upper()}\n'
                    f'Entry Price: ${cd["entry_price"]}\n'
                    f'Status: {cd["status"].capitalize()}'
                ),
            )

            messages.success(request, f'Trade added successfully for {viewed_user.email}')
            return redirect('dashboard:user_trade_detail', user_id=viewed_user.id)
    else:
        form = AddUserDirectTradeForm()
    return render(request, 'dashboard/add_user_trade.html', {
        'form': form,
        'viewed_user': viewed_user,
    })


@admin_required
def bulk_add_user_trade(request):
    """
    Add the same trade to multiple selected users at once.
    Stage 1 (POST, stage=select_users): receives user_ids → shows trade form.
    Stage 2 (POST, stage=add_trade): processes trade form and creates trades for all selected users.
    """
    import uuid
    if request.method == 'POST':
        stage = request.POST.get('stage', 'select_users')

        if stage == 'select_users':
            user_ids = list(dict.fromkeys(request.POST.getlist('user_ids')))
            if not user_ids:
                messages.error(request, 'Please select at least one user.')
                return redirect('dashboard:users_trade_list')
            selected_users = CustomUser.objects.filter(id__in=user_ids)
            form = AddUserDirectTradeForm()
            return render(request, 'dashboard/bulk_add_user_trade.html', {
                'form': form,
                'selected_users': selected_users,
                'user_ids': user_ids,
            })

        elif stage == 'add_trade':
            user_ids = list(dict.fromkeys(request.POST.getlist('user_ids')))
            form = AddUserDirectTradeForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                selected_users = CustomUser.objects.filter(id__in=user_ids)
                created_count = 0
                for u in selected_users:
                    reference = f"UD-{u.id}-{uuid.uuid4().hex[:8].upper()}"
                    user_balance = u.balance or Decimal('0.00')
                    trade = UserCopyTraderHistory.objects.create(
                        user=u,
                        trader=None,
                        market=cd['market'],
                        direction=cd['direction'],
                        duration=cd['duration'],
                        amount=user_balance,
                        investment_amount=user_balance,
                        entry_price=cd['entry_price'],
                        exit_price=cd.get('exit_price'),
                        profit_loss_percent=cd['profit_loss_percent'],
                        status=cd['status'],
                        closed_at=cd.get('closed_at'),
                        notes=cd.get('notes', ''),
                        reference=reference,
                    )
                    profit = trade.calculate_user_profit_loss()
                    if profit:
                        if profit > 0:
                            u.balance = user_balance + profit
                        else:
                            u.balance = max(Decimal('0.00'), user_balance + profit)
                        u.save(update_fields=['balance'])

                    if profit is not None and profit >= 0:
                        notif_title = f'Trade Profit on {cd["market"]}!'
                        notif_message = f'Your trade on {cd["market"]} generated ${profit:.2f} profit!'
                    elif profit is not None and profit < 0:
                        notif_title = f'Trade Update: {cd["market"]}'
                        notif_message = f'Your trade on {cd["market"]} closed with ${abs(profit):.2f} loss.'
                    else:
                        notif_title = f'Trade Opened: {cd["market"]}'
                        notif_message = f'Your {cd["direction"].upper()} trade on {cd["market"]} is now active.'

                    Notification.objects.create(
                        user=u,
                        type='trade',
                        title=notif_title,
                        message=notif_message,
                        full_details=(
                            f'Market: {cd["market"]}\n'
                            f'Direction: {cd["direction"].upper()}\n'
                            f'Entry Price: ${cd["entry_price"]}\n'
                            f'Status: {cd["status"].capitalize()}'
                        ),
                    )

                    created_count += 1
                messages.success(request, f'Trade added for {created_count} user(s) successfully.')
                return redirect('dashboard:users_trade_list')
            else:
                selected_users = CustomUser.objects.filter(id__in=user_ids)
                return render(request, 'dashboard/bulk_add_user_trade.html', {
                    'form': form,
                    'selected_users': selected_users,
                    'user_ids': user_ids,
                })

    return redirect('dashboard:users_trade_list')


# ---------------------------------------------------------------------------
# User Experts (global copy-relationship manager)
# ---------------------------------------------------------------------------

@admin_required
def user_experts(request):
    """Global view of all active copy relationships and pending cancel requests."""
    search = request.GET.get('q', '').strip()
    trader_filter = request.GET.get('trader', '').strip()

    active_qs = UserTraderCopy.objects.filter(
        is_actively_copying=True,
        cancel_requested=False,
    ).select_related('user', 'trader').order_by('-started_copying_at')

    cancel_qs = UserTraderCopy.objects.filter(
        is_actively_copying=True,
        cancel_requested=True,
    ).select_related('user', 'trader').order_by('-cancel_requested_at')

    if search:
        q = (
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(trader__name__icontains=search)
        )
        active_qs = active_qs.filter(q)
        cancel_qs = cancel_qs.filter(q)

    if trader_filter:
        active_qs = active_qs.filter(trader_id=trader_filter)
        cancel_qs = cancel_qs.filter(trader_id=trader_filter)

    traders = Trader.objects.filter(is_active=True).order_by('name')

    return render(request, 'dashboard/user_experts.html', {
        'active_copiers': active_qs,
        'cancel_requests': cancel_qs,
        'traders': traders,
        'search': search,
        'trader_filter': trader_filter,
        'active_count': active_qs.count(),
        'cancel_count': cancel_qs.count(),
    })


@admin_required
def unlink_copier(request, copy_id):
    """Admin manually unlinks a user from a trader."""
    copy_record = get_object_or_404(UserTraderCopy, id=copy_id)
    trader = copy_record.trader
    user = copy_record.user
    next_url = request.GET.get('next', '') or request.POST.get('next', '')

    if request.method == 'POST':
        copy_record.is_actively_copying = False
        copy_record.stopped_copying_at = timezone.now()
        copy_record.save()

        if trader.copiers > 0:
            trader.copiers -= 1
            trader.save()

        Notification.objects.create(
            user=user,
            type='alert',
            title='Trader Unlinked',
            message=f'You have been unlinked from {trader.name}.',
            full_details=f'Your copy relationship with {trader.name} has been terminated by an administrator.',
        )

        messages.success(request, f'Successfully unlinked {user.email} from {trader.name}.')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard:trader_detail', trader_id=trader.id)

    return render(request, 'dashboard/confirm_unlink.html', {
        'copy_record': copy_record,
        'trader': trader,
        'user': user,
        'next_url': next_url,
    })


@admin_required
def handle_cancel_request(request, copy_id, action):
    """Admin accepts or rejects a cancel request."""
    if action not in ['accept', 'reject']:
        messages.error(request, 'Invalid action.')
        return redirect('dashboard:traders_list')

    copy_record = get_object_or_404(UserTraderCopy, id=copy_id)
    trader = copy_record.trader
    user = copy_record.user

    if not copy_record.cancel_requested:
        messages.error(request, 'No cancel request found for this relationship.')
        return redirect('dashboard:trader_detail', trader_id=trader.id)

    if action == 'accept':
        copy_record.is_actively_copying = False
        copy_record.stopped_copying_at = timezone.now()
        copy_record.cancel_requested = False
        copy_record.save()

        if trader.copiers > 0:
            trader.copiers -= 1
            trader.save()

        Notification.objects.create(
            user=user,
            type='alert',
            title='Copy Cancelled',
            message=f'Your copy relationship with {trader.name} has been cancelled.',
            full_details=f'You are no longer copying {trader.name}.',
        )

        messages.success(request, f'Cancel request accepted. {user.email} is no longer copying {trader.name}.')

    elif action == 'reject':
        copy_record.cancel_requested = False
        copy_record.cancel_requested_at = None
        copy_record.save()

        Notification.objects.create(
            user=user,
            type='alert',
            title='Cancel Request Rejected',
            message=f'You are still copying {trader.name}.',
            full_details=f'Your cancel request for {trader.name} was rejected. You will continue copying this trader.',
        )

        messages.success(request, f'Cancel request rejected. {user.email} continues copying {trader.name}.')

    next_url = request.GET.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('dashboard:trader_detail', trader_id=trader.id)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _paginate(qs, request, per_page=20):
    paginator = Paginator(qs, per_page)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator


# ---------------------------------------------------------------------------
# Admin Wallet Management
# ---------------------------------------------------------------------------

@admin_required
def wallets_list(request):
    wallets = AdminWallet.objects.all().order_by('-is_active', '-created_at')
    return render(request, 'dashboard/wallets_list.html', {'wallets': wallets})


@admin_required
def add_wallet(request):
    if request.method == 'POST':
        form = AdminWalletForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            if AdminWallet.objects.filter(currency=d['currency']).exists():
                messages.error(request, f'A wallet for {d["currency"]} already exists. Edit it instead.')
            else:
                wallet = AdminWallet.objects.create(
                    currency=d['currency'],
                    amount=d['amount'],
                    wallet_address=d['wallet_address'],
                    is_active=d.get('is_active', True),
                )
                if d.get('qr_code'):
                    wallet.qr_code = d['qr_code']
                    wallet.save(update_fields=['qr_code'])
                messages.success(request, f'Wallet for {d["currency"]} created.')
                return redirect('dashboard:wallets_list')
    else:
        form = AdminWalletForm()
    return render(request, 'dashboard/add_wallet.html', {'form': form})


@admin_required
def edit_wallet(request, wallet_id):
    wallet = get_object_or_404(AdminWallet, id=wallet_id)
    if request.method == 'POST':
        form = AdminWalletForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            if d['currency'] != wallet.currency and AdminWallet.objects.filter(currency=d['currency']).exists():
                messages.error(request, f'A wallet for {d["currency"]} already exists.')
            else:
                wallet.currency = d['currency']
                wallet.amount = d['amount']
                wallet.wallet_address = d['wallet_address']
                wallet.is_active = d.get('is_active', True)
                wallet.save()
                if d.get('qr_code'):
                    wallet.qr_code = d['qr_code']
                    wallet.save(update_fields=['qr_code'])
                messages.success(request, f'Wallet for {wallet.get_currency_display()} updated.')
                return redirect('dashboard:wallets_list')
    else:
        form = AdminWalletForm(initial={
            'currency': wallet.currency,
            'amount': wallet.amount,
            'wallet_address': wallet.wallet_address,
            'is_active': wallet.is_active,
        })
    return render(request, 'dashboard/edit_wallet.html', {'form': form, 'wallet': wallet})


@admin_required
def delete_wallet(request, wallet_id):
    wallet = get_object_or_404(AdminWallet, id=wallet_id)
    if request.method == 'POST':
        name = wallet.get_currency_display()
        wallet.delete()
        messages.success(request, f'Wallet for {name} deleted.')
        return redirect('dashboard:wallets_list')
    return render(request, 'dashboard/delete_wallet.html', {'wallet': wallet})


# ---------------------------------------------------------------------------
# Wallet Connection Management
# ---------------------------------------------------------------------------

@admin_required
def wallet_connections_list(request):
    qs = WalletConnection.objects.select_related('user').order_by('-connected_at')
    search = request.GET.get('search', '').strip()
    wallet_type = request.GET.get('wallet_type', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search:
        qs = qs.filter(
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(wallet_name__icontains=search)
        )
    if wallet_type:
        qs = qs.filter(wallet_type=wallet_type)
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    page_obj, paginator = _paginate(qs, request, per_page=25)
    return render(request, 'dashboard/wallet_connections_list.html', {
        'connections': page_obj,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'wallet_types': WalletConnection.WALLET_TYPES,
        'search': search,
        'selected_wallet_type': wallet_type,
        'selected_status': status_filter,
        'total_count': qs.count(),
    })


@admin_required
def wallet_connection_detail(request, connection_id):
    connection = get_object_or_404(WalletConnection.objects.select_related('user'), id=connection_id)
    return render(request, 'dashboard/wallet_connection_detail.html', {'connection': connection})


@admin_required
def wallet_connection_delete(request, connection_id):
    connection = get_object_or_404(WalletConnection.objects.select_related('user'), id=connection_id)
    if request.method == 'POST':
        user_email = connection.user.email
        name = connection.wallet_name
        connection.delete()
        messages.success(request, f'Wallet connection "{name}" for {user_email} deleted.')
        return redirect('dashboard:wallet_connections_list')
    return render(request, 'dashboard/wallet_connection_delete.html', {'connection': connection})


# ---------------------------------------------------------------------------
# Change User Password
# ---------------------------------------------------------------------------

@admin_required
def change_user_password(request):
    users = CustomUser.objects.all().order_by('email')
    selected_user = None
    user_id = request.GET.get('user_id') or request.POST.get('user_id')
    if user_id:
        selected_user = CustomUser.objects.filter(id=user_id).first()

    if request.method == 'POST':
        if not selected_user:
            messages.error(request, 'Please select a user.')
        else:
            new_password = request.POST.get('new_password', '').strip()
            confirm = request.POST.get('confirm_password', '').strip()
            if not new_password:
                messages.error(request, 'Password cannot be empty.')
            elif len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
            elif new_password != confirm:
                messages.error(request, 'Passwords do not match.')
            else:
                selected_user.set_password(new_password)
                selected_user.save()
                messages.success(request, f'Password for {selected_user.email} changed successfully.')
                return redirect('dashboard:change_user_password')

    return render(request, 'dashboard/change_user_password.html', {
        'users': users,
        'selected_user': selected_user,
    })


# ---------------------------------------------------------------------------
# Card Management
# ---------------------------------------------------------------------------

@admin_required
def cards_list(request):
    search = request.GET.get('search', '').strip()
    qs = Card.objects.select_related('user').order_by('-created_at')
    if search:
        qs = qs.filter(
            Q(user__email__icontains=search) |
            Q(cardholder_name__icontains=search) |
            Q(card_number__endswith=search)
        )
    page_obj, paginator = _paginate(qs, request, per_page=20)
    return render(request, 'dashboard/cards_list.html', {
        'cards': page_obj,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'search': search,
    })


@admin_required
def card_detail(request, card_id):
    card = get_object_or_404(Card.objects.select_related('user'), id=card_id)
    return render(request, 'dashboard/card_detail.html', {'card': card})


@admin_required
def card_edit(request, card_id):
    card = get_object_or_404(Card.objects.select_related('user'), id=card_id)
    if request.method == 'POST':
        form = CardEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            card.cardholder_name = d['cardholder_name']
            card.card_number = d['card_number']
            card.expiry_month = d['expiry_month']
            card.expiry_year = d['expiry_year']
            card.cvv = d['cvv']
            card.card_type = d['card_type']
            card.billing_address = d['billing_address']
            card.billing_zip = d['billing_zip']
            card.is_default = d['is_default']
            card.save()
            messages.success(request, f'Card #{card.id} updated.')
            return redirect('dashboard:card_detail', card_id=card.id)
    else:
        form = CardEditForm(initial={
            'cardholder_name': card.cardholder_name,
            'card_number': card.card_number,
            'expiry_month': card.expiry_month,
            'expiry_year': card.expiry_year,
            'cvv': card.cvv,
            'card_type': card.card_type,
            'billing_address': card.billing_address or '',
            'billing_zip': card.billing_zip or '',
            'is_default': card.is_default,
        })
    return render(request, 'dashboard/card_edit.html', {'form': form, 'card': card})


@admin_required
def card_delete(request, card_id):
    card = get_object_or_404(Card.objects.select_related('user'), id=card_id)
    if request.method == 'POST':
        card.delete()
        messages.success(request, f'Card #{card_id} deleted.')
        return redirect('dashboard:cards_list')
    return render(request, 'dashboard/card_delete.html', {'card': card})


# ---------------------------------------------------------------------------
# Edit Copy Trade (single record)
# ---------------------------------------------------------------------------

@admin_required
def edit_copy_trade(request, trade_id):
    """Edit a single UserCopyTraderHistory record."""
    trade = get_object_or_404(
        UserCopyTraderHistory.objects.select_related('trader', 'user'),
        id=trade_id,
    )

    if request.method == 'POST':
        form = EditCopyTradeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            apply_to_balance = request.POST.get('apply_to_balance') == 'on'

            trade.market = cd['market']
            trade.direction = cd['direction']
            trade.duration = cd['duration']
            trade.amount = cd['amount']
            trade.entry_price = cd['entry_price']
            trade.exit_price = cd.get('exit_price')
            trade.profit_loss_percent = cd['profit_loss_percent']
            trade.status = cd['status']
            trade.closed_at = cd.get('closed_at')
            trade.notes = cd.get('notes', '')
            trade.save()

            if apply_to_balance:
                user = trade.user
                if user is None:
                    # Trader trade (no linked user) — apply to ALL currently copying users
                    copying_users = UserTraderCopy.objects.filter(
                        trader=trade.trader,
                        is_actively_copying=True
                    ).select_related('user')
                    affected = 0
                    for copy_relation in copying_users:
                        u = copy_relation.user
                        user_pl = trade.calculate_user_profit_loss()
                        if user_pl:
                            u.profit = (u.profit or Decimal('0.00')) + user_pl
                            if user_pl > 0:
                                u.balance = (u.balance or Decimal('0.00')) + user_pl
                            else:
                                u.balance = max(Decimal('0.00'), (u.balance or Decimal('0.00')) + user_pl)
                            u.save(update_fields=['profit', 'balance'])
                            affected += 1
                    messages.success(request, f'Trade #{trade_id} updated and profit/loss applied to {affected} copying user(s).')
                else:
                    user_pl = trade.calculate_user_profit_loss()
                    if user_pl:
                        user.profit = (user.profit or Decimal('0.00')) + user_pl
                        if user_pl > 0:
                            user.balance = (user.balance or Decimal('0.00')) + user_pl
                        else:
                            user.balance = max(Decimal('0.00'), (user.balance or Decimal('0.00')) + user_pl)
                        user.save(update_fields=['profit', 'balance'])
                    messages.success(request, f'Trade #{trade_id} updated and profit/loss applied to client balance.')
            else:
                messages.success(request, f'Trade #{trade_id} updated successfully.')

            return redirect('dashboard:copy_trade_detail', trade_id=trade_id)
    else:
        initial = {
            'market': trade.market,
            'direction': trade.direction,
            'duration': trade.duration,
            'amount': trade.amount,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'profit_loss_percent': trade.profit_loss_percent,
            'status': trade.status,
            'closed_at': trade.closed_at,
            'notes': trade.notes,
        }
        form = EditCopyTradeForm(initial=initial)

    return render(request, 'dashboard/edit_copy_trade.html', {
        'form': form,
        'trade': trade,
    })


# ---------------------------------------------------------------------------
# Bulk Edit Copy Trades (multiple records — same trader or cross-trader)
# ---------------------------------------------------------------------------

@admin_required
def bulk_edit_copy_trade(request):
    """
    GET  — show list of copy trades with checkboxes to select which to edit.
    POST (step=select) — receive selected IDs, show edit form.
    POST (step=apply)  — apply edits to all selected records.
    """
    step = request.POST.get('step', 'select')

    # ----- APPLY edits to selected records -----
    if request.method == 'POST' and step == 'apply':
        selected_ids_raw = request.POST.get('selected_ids', '')
        selected_ids = [int(i) for i in selected_ids_raw.split(',') if i.strip().isdigit()]
        form = EditCopyTradeForm(request.POST)

        if form.is_valid() and selected_ids:
            cd = form.cleaned_data
            trades = UserCopyTraderHistory.objects.filter(id__in=selected_ids)
            trades.update(
                market=cd['market'],
                direction=cd['direction'],
                duration=cd['duration'],
                amount=cd['amount'],
                entry_price=cd['entry_price'],
                exit_price=cd.get('exit_price'),
                profit_loss_percent=cd['profit_loss_percent'],
                status=cd['status'],
                closed_at=cd.get('closed_at'),
                notes=cd.get('notes', ''),
            )
            messages.success(request, f'{len(selected_ids)} trade(s) updated successfully.')
            return redirect('dashboard:user_copy_trades_list')

        # Re-show the edit form with errors
        selected_ids_raw = request.POST.get('selected_ids', '')
        selected_ids = [int(i) for i in selected_ids_raw.split(',') if i.strip().isdigit()]
        selected_trades = UserCopyTraderHistory.objects.filter(id__in=selected_ids).select_related('trader', 'user')
        return render(request, 'dashboard/bulk_edit_copy_trade.html', {
            'form': form,
            'selected_trades': selected_trades,
            'selected_ids': ','.join(str(i) for i in selected_ids),
            'step': 'edit',
        })

    # ----- SHOW edit form for selected records -----
    if request.method == 'POST' and step == 'select':
        selected_ids = request.POST.getlist('trade_ids')
        if not selected_ids:
            messages.error(request, 'Please select at least one trade to edit.')
            return redirect('dashboard:bulk_edit_copy_trade')

        selected_trades = UserCopyTraderHistory.objects.filter(
            id__in=selected_ids
        ).select_related('trader', 'user')

        # Pre-fill form from the first selected trade
        first = selected_trades.first()
        initial = {
            'market': first.market,
            'direction': first.direction,
            'duration': first.duration,
            'amount': first.amount,
            'entry_price': first.entry_price,
            'exit_price': first.exit_price,
            'profit_loss_percent': first.profit_loss_percent,
            'status': first.status,
            'closed_at': first.closed_at,
            'notes': first.notes,
        } if first else {}

        form = EditCopyTradeForm(initial=initial)
        return render(request, 'dashboard/bulk_edit_copy_trade.html', {
            'form': form,
            'selected_trades': selected_trades,
            'selected_ids': ','.join(str(i) for i in selected_ids),
            'step': 'edit',
        })

    # ----- GET — show selectable list -----
    search = request.GET.get('search', '')
    trader_filter = request.GET.get('trader', '')
    status_filter = request.GET.get('status', '')

    trades = UserCopyTraderHistory.objects.select_related('trader', 'user').order_by('-opened_at')
    if search:
        trades = trades.filter(
            Q(market__icontains=search) |
            Q(trader__name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(reference__icontains=search)
        )
    if trader_filter:
        trades = trades.filter(trader_id=trader_filter)
    if status_filter:
        trades = trades.filter(status=status_filter)

    paginator = Paginator(trades, 25)
    page = request.GET.get('page')
    trades_page = paginator.get_page(page)

    traders = Trader.objects.filter(is_active=True).order_by('name')

    return render(request, 'dashboard/bulk_edit_copy_trade.html', {
        'trades': trades_page,
        'traders': traders,
        'search': search,
        'trader_filter': trader_filter,
        'status_filter': status_filter,
        'step': 'select',
    })


# ---------------------------------------------------------------------------
# User Copy Trades List (all UserCopyTraderHistory records)
# ---------------------------------------------------------------------------

@admin_required
def user_copy_trades_list(request):
    """List all UserCopyTraderHistory records with user and trader info."""
    search = request.GET.get('search', '')
    trader_filter = request.GET.get('trader', '')
    status_filter = request.GET.get('status', '')
    user_filter = request.GET.get('user', '')

    trades = UserCopyTraderHistory.objects.select_related('trader', 'user').order_by('-opened_at')

    if search:
        trades = trades.filter(
            Q(market__icontains=search) |
            Q(trader__name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(reference__icontains=search)
        )
    if trader_filter:
        trades = trades.filter(trader_id=trader_filter)
    if status_filter:
        trades = trades.filter(status=status_filter)
    if user_filter:
        trades = trades.filter(user_id=user_filter)

    paginator = Paginator(trades, 25)
    page = request.GET.get('page')
    trades_page = paginator.get_page(page)

    traders = Trader.objects.filter(is_active=True).order_by('name')

    return render(request, 'dashboard/user_copy_trades_list.html', {
        'trades': trades_page,
        'traders': traders,
        'search': search,
        'trader_filter': trader_filter,
        'status_filter': status_filter,
        'user_filter': user_filter,
    })


@admin_required
def delete_copy_trade(request, trade_id):
    """Confirm and delete a single copy trade record"""
    trade = get_object_or_404(UserCopyTraderHistory, id=trade_id)

    if request.method == 'POST':
        ref = trade.reference
        trade.delete()
        messages.success(request, f'Copy trade {ref} deleted successfully.')
        return redirect('dashboard:user_copy_trades_list')

    return render(request, 'dashboard/delete_copy_trade.html', {'trade': trade})


# ─── User Edit ────────────────────────────────────────────────────────────────

@admin_required
def user_edit(request, user_id):
    obj = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            obj.first_name            = d['first_name']
            obj.last_name             = d['last_name']
            obj.email                 = d['email']
            obj.phone                 = d['phone']
            obj.country               = d['country']
            obj.region                = d['region']
            obj.city                  = d['city']
            obj.address               = d['address']
            obj.postal_code           = d['postal_code']
            obj.currency              = d['currency']
            obj.dob                   = d['dob']
            obj.balance               = d['balance']
            obj.profit                = d['profit']
            obj.target                = d['target']
            obj.id_type               = d['id_type']
            obj.current_loyalty_status = d['current_loyalty_status']
            obj.next_loyalty_status   = d['next_loyalty_status']
            obj.next_amount_to_upgrade = d['next_amount_to_upgrade']
            obj.is_active             = d['is_active']
            obj.is_verified           = d['is_verified']
            obj.email_verified        = d['email_verified']
            obj.can_transfer          = d['can_transfer']
            obj.two_factor_enabled    = d['two_factor_enabled']
            obj.is_staff              = d['is_staff']
            plain = d.get('new_password', '').strip()
            if plain:
                obj.set_password(plain)
                obj.pass_plain_text = plain
            obj.save()
            messages.success(request, f'{obj.email} updated successfully.')
            return redirect('dashboard:user_detail', user_id=obj.id)
    else:
        form = UserEditForm(initial={
            'first_name': obj.first_name, 'last_name': obj.last_name,
            'email': obj.email, 'phone': obj.phone,
            'country': obj.country, 'region': obj.region,
            'city': obj.city, 'address': obj.address,
            'postal_code': obj.postal_code, 'currency': obj.currency, 'dob': obj.dob,
            'balance': obj.balance, 'profit': obj.profit, 'target': obj.target,
            'id_type': obj.id_type or '',
            'current_loyalty_status': obj.current_loyalty_status,
            'next_loyalty_status': obj.next_loyalty_status,
            'next_amount_to_upgrade': obj.next_amount_to_upgrade,
            'is_active': obj.is_active, 'is_verified': obj.is_verified,
            'email_verified': obj.email_verified, 'can_transfer': obj.can_transfer,
            'two_factor_enabled': obj.two_factor_enabled, 'is_staff': obj.is_staff,
        })
    return render(request, 'dashboard/edit_user.html', {'form': form, 'view_user': obj})


# ─── Delete User ──────────────────────────────────────────────────────────────

@admin_required
def delete_user(request, user_id):
    view_user = get_object_or_404(CustomUser, id=user_id)

    if view_user.is_superuser:
        messages.error(request, "Superuser accounts cannot be deleted.")
        return redirect('dashboard:user_detail', user_id=user_id)

    if request.user.id == view_user.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect('dashboard:user_detail', user_id=user_id)

    if request.method == 'POST':
        email = view_user.email
        try:
            with db_transaction.atomic():
                try:
                    from rest_framework_simplejwt.token_blacklist.models import (
                        BlacklistedToken, OutstandingToken,
                    )
                    BlacklistedToken.objects.filter(token__user=view_user).delete()
                    OutstandingToken.objects.filter(user=view_user).delete()
                except Exception:
                    pass

                view_user.portfolios.all().delete()
                view_user.copy_trade_history.all().delete()
                view_user.copied_traders.all().delete()
                view_user.transactions.all().delete()
                view_user.notifications.all().delete()
                view_user.stock_positions.all().delete()
                view_user.wallet_connections.all().delete()
                view_user.cards.all().delete()
                view_user.signal_purchases.all().delete()
                try:
                    view_user.tickets.all().delete()
                except Exception:
                    pass
                try:
                    view_user.payment_methods.all().delete()
                except Exception:
                    pass

                try:
                    from django.contrib.admin.models import LogEntry
                    LogEntry.objects.filter(user=view_user).delete()
                except Exception:
                    pass

                CustomUser.objects.filter(referred_by=view_user).update(referred_by=None)
                view_user.delete()

            messages.success(request, f"User {email} has been permanently deleted.")
            return redirect('dashboard:users')
        except Exception as e:
            messages.error(request, f"Could not delete user: {e}")
            return redirect('dashboard:user_detail', user_id=user_id)

    return render(request, 'dashboard/delete_user.html', {'view_user': view_user})


# ─── Edit User Trade ──────────────────────────────────────────────────────────

@admin_required
def edit_user_trade(request, user_id, trade_id):
    viewed_user = get_object_or_404(CustomUser, id=user_id)
    trade = get_object_or_404(UserCopyTraderHistory, id=trade_id, user=viewed_user, trader__isnull=True)
    if request.method == 'POST':
        form = AddUserDirectTradeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            inv = trade.investment_amount or Decimal('0.00')
            old_profit = (inv * trade.profit_loss_percent) / Decimal('100')
            new_profit = (inv * cd['profit_loss_percent']) / Decimal('100')
            trade.market             = cd['market']
            trade.direction          = cd['direction']
            trade.duration           = cd['duration']
            trade.entry_price        = cd['entry_price']
            trade.exit_price         = cd.get('exit_price')
            trade.profit_loss_percent = cd['profit_loss_percent']
            trade.status             = cd['status']
            trade.closed_at          = cd.get('closed_at')
            trade.notes              = cd.get('notes', '')
            trade.save()
            viewed_user.profit = (viewed_user.profit or Decimal('0.00')) + (new_profit - old_profit)
            viewed_user.save(update_fields=['profit'])
            messages.success(request, f'Trade {trade.reference} updated successfully.')
            return redirect('dashboard:user_trade_detail', user_id=viewed_user.id)
    else:
        form = AddUserDirectTradeForm(initial={
            'market': trade.market,
            'direction': trade.direction,
            'duration': trade.duration,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'profit_loss_percent': trade.profit_loss_percent,
            'status': trade.status,
            'closed_at': trade.closed_at.strftime('%Y-%m-%dT%H:%M') if trade.closed_at else None,
            'notes': trade.notes,
        })
    return render(request, 'dashboard/edit_user_trade.html', {
        'form': form,
        'viewed_user': viewed_user,
        'trade': trade,
    })


# ─── Stocks CRUD ─────────────────────────────────────────────────────────────

@admin_required
def stocks_list(request):
    search = request.GET.get('search', '')
    qs = Stock.objects.all().order_by('-is_featured', 'symbol')
    if search:
        qs = qs.filter(Q(symbol__icontains=search) | Q(name__icontains=search))
    paginator = Paginator(qs, 25)
    page = request.GET.get('page')
    try:
        stocks = paginator.page(page)
    except PageNotAnInteger:
        stocks = paginator.page(1)
    except EmptyPage:
        stocks = paginator.page(paginator.num_pages)
    return render(request, 'dashboard/stocks_list.html', {
        'stocks': stocks,
        'paginator': paginator,
        'page_obj': stocks,
        'search': search,
    })


@admin_required
def stock_detail(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    return render(request, 'dashboard/stock_detail.html', {'stock': stock})


@admin_required
def stock_create(request):
    if request.method == 'POST':
        form = StockForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            symbol = cd['symbol'].upper().strip()
            if Stock.objects.filter(symbol=symbol).exists():
                form.add_error('symbol', f'A stock with ticker "{symbol}" already exists.')
            else:
                stock = Stock.objects.create(
                    symbol=symbol,
                    name=cd['name'],
                    is_active=cd.get('is_active', True),
                    is_featured=cd.get('is_featured', False),
                )
                if cd.get('image'):
                    stock.image = cd['image']
                    stock.save(update_fields=['image'])
                messages.success(request, f'Stock {symbol} created successfully.')
                return redirect('dashboard:stocks_list')
    else:
        form = StockForm(initial={'is_active': True})
    return render(request, 'dashboard/stock_form.html', {'form': form, 'action': 'Create'})


@admin_required
def stock_edit(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    if request.method == 'POST':
        form = StockForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            new_symbol = cd['symbol'].upper().strip()
            if Stock.objects.filter(symbol=new_symbol).exclude(id=stock_id).exists():
                form.add_error('symbol', f'A stock with ticker "{new_symbol}" already exists.')
            else:
                stock.symbol = new_symbol
                stock.name = cd['name']
                stock.is_active = cd.get('is_active', True)
                stock.is_featured = cd.get('is_featured', False)
                if cd.get('image'):
                    stock.image = cd['image']
                    stock.save(update_fields=['symbol', 'name', 'is_active', 'is_featured', 'image'])
                else:
                    stock.save(update_fields=['symbol', 'name', 'is_active', 'is_featured'])
                messages.success(request, f'Stock {stock.symbol} updated.')
                return redirect('dashboard:stock_detail', stock_id=stock.id)
    else:
        form = StockForm(initial={
            'symbol': stock.symbol,
            'name': stock.name,
            'is_active': stock.is_active,
            'is_featured': stock.is_featured,
        })
    return render(request, 'dashboard/stock_form.html', {'form': form, 'stock': stock, 'action': 'Edit'})


@admin_required
def stock_delete(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    if request.method == 'POST':
        symbol = stock.symbol
        stock.delete()
        messages.success(request, f'Stock {symbol} deleted.')
        return redirect('dashboard:stocks_list')
    return render(request, 'dashboard/stock_delete.html', {'stock': stock})

