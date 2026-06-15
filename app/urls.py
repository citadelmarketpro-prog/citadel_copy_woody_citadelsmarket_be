from django.urls import path

from .views import( 
    validate_token,
    register_user, 
    login_user, 
    change_password, 
    ticket_list_create,
    # transactions_view, 

    # Dashboard
    dashboard_data,
    user_transactions,
    user_portfolios,
    user_stats,
    

    get_user_profile,
    upload_kyc,
    withdrawal_view,
    transaction_history,
    payment_methods,
    get_deposit_options,
    create_deposit,
    trader_list_create,
    trader_detail,
    asset_list,
    grouped_assets,
    news_list,
    news_detail,
    trader_list, 
    trader_detail, 
    trader_portfolios,

    # Notification
    notification_list, 
    notification_detail, 
    mark_notification_read,
    mark_all_notifications_read,
    unread_notification_count,
    delete_notification,

    # Settings views
    get_user_settings,
    update_profile,
    update_payment_method,
    change_user_password,

    # Deposits
    get_active_deposit_options,
    create_deposit_transaction,
    get_user_deposit_history,
    notify_deposit_intent,

    # Withdrawal
    get_user_profile_for_withdrawal,
    get_withdrawal_methods,
    create_withdrawal_request,
    get_withdrawal_history,
    get_all_transaction_history,

    # Stocks
     stock_list,
    stock_detail,
    stock_sectors,
    user_stock_positions,
    buy_stock,
    sell_stock,
    get_trade_history,


    # Connect Wallet
    get_connected_wallets,
    connect_wallet,
    disconnect_wallet,
    get_wallet_detail,
    get_available_wallet_types,


    # KYC
    submit_kyc,
    get_kyc_status,
    get_kyc_details,

    # SIGNALS
    signal_list,
    signal_detail,
    purchase_signal,
    user_purchased_signals,
    user_signal_balance,

    # Copy Trading Action
    copy_trader_action, 
    get_user_copy_status, 
    get_all_user_copies,


    # Referer
    get_referral_info,
    get_referral_list,
    validate_referral_code,
    get_referral_earnings_history,
    generate_referral_code,


    # Admin implemented copy trader history
    get_copy_trade_history,
    get_copy_trade_detail,

    # Loyalty
    get_loyalty_tiers,

    # Transfer
    transfer_status,
    transfer_funds,

    # Cards
    add_card,

)

from .auth_views import (
    # New 2FA views
    register_user_with_verification,
    verify_email,
    resend_verification_code,
    login_with_2fa,
    verify_2fa_login,
    resend_2fa_code,
    enable_2fa,
    disable_2fa,
    get_2fa_status,

    # Reset Password
    request_password_reset,
    reset_password,
    validate_reset_token,
)

urlpatterns = [

    # Authentication with Email Verification & 2FA
    # path("register/", register_user_with_verification, name="register-with-verification"),
    path("verify-email/", verify_email, name="verify-email"),
    path("resend-code/", resend_verification_code, name="resend-verification-code"),
    
    path("login/", login_with_2fa, name="login-with-2fa"),
    path("verify-2fa/", verify_2fa_login, name="verify-2fa-login"),
    path("resend-2fa-code/", resend_2fa_code, name="resend-2fa-code"),

    # Password Reset
    path("password-reset/request/", request_password_reset, name="request-password-reset"),
    path("password-reset/validate/", validate_reset_token, name="validate-reset-token"),
    path("password-reset/confirm/", reset_password, name="reset-password"),
    
    # 2FA Management
    path("enable-2fa/", enable_2fa, name="enable-2fa"),
    path("disable-2fa/", disable_2fa, name="disable-2fa"),
    path("2fa-status/", get_2fa_status, name="2fa-status"),

    path("api/validate-token/", validate_token, name="validate-token"),
    path("register/", register_user, name="register"),
    # path("login/", login_user, name="login"),
    path("profile/", get_user_profile, name="get_user_profile"),
    path("tickets/", ticket_list_create, name="tickets_view"),
    # path("transactions/", transactions_view, name="transactions_view"),


    path('dashboard/', dashboard_data, name='dashboard-data'),
    
    # Transactions endpoint
    path('transactions/', user_transactions, name='user-transactions'),

    # NEW: All transactions history endpoint
    path("transactions/history/", get_all_transaction_history, name="all-transaction-history"),
    
    # Portfolios endpoint
    path('portfolios/', user_portfolios, name='user-portfolios'),
    
    # User stats endpoint
    path('stats/', user_stats, name='user-stats'),

     path("change-password/", change_password, name="change-password"),
     path("withdrawal/", withdrawal_view, name="withdrawal"),

     path("kyc/upload/", upload_kyc, name="upload_kyc"),
     path("transactions/", transaction_history, name="transaction-history"),
     path("payments/", payment_methods, name="payments"),
     
     path("admin-wallets/", get_deposit_options, name="get_deposit_options"),

     path("deposits/", create_deposit, name="create-deposit"),

    #  path("traders/", trader_list_create, name="trader-list-create"),
    # path("traders/<int:pk>/", trader_detail, name="trader-detail"),


    path("copy-trader/action/", copy_trader_action, name="copy-trader-action"),
    path("copy-trader/status/<int:trader_id>/", get_user_copy_status, name="user-copy-status"),
    path("copy-trader/my-copies/", get_all_user_copies, name="user-all-copies"),

    path("assets/", asset_list, name="asset-list"),
    path("assets/grouped/", grouped_assets, name="grouped-assets"),

    path("news/", news_list, name="news-list"),
    path("news/<int:pk>/", news_detail, name="news-detail"),

    path("traders/", trader_list, name="trader-list"),
    path("traders/<int:pk>/", trader_detail, name="trader-detail"),
    path("traders/<int:trader_id>/portfolios/", trader_portfolios, name="trader-portfolios"),
     
     # Notifications
    path("notifications/", notification_list, name="notification-list"),
    path("notifications/<int:pk>/", notification_detail, name="notification-detail"),
    path("notifications/<int:pk>/mark-read/", mark_notification_read, name="notification-mark-read"),
    path("notifications/mark-all-read/", mark_all_notifications_read, name="notification-mark-all-read"),
    path("notifications/unread-count/", unread_notification_count, name="notification-unread-count"),
    path("notifications/<int:pk>/delete/", delete_notification, name="notification-delete"),

    # Settings endpoints
    path("settings/", get_user_settings, name="user-settings"),
    path("settings/profile/", update_profile, name="update-profile"),
    path("settings/payment-method/", update_payment_method, name="update-payment-method"),
    path("settings/password/", change_user_password, name="change-user-password"),

    # Deposit endpoints
    path("deposits/options/", get_active_deposit_options, name="deposit-options"),
    path("deposits/create/", create_deposit_transaction, name="create-deposit-transaction"),
    path("deposits/history/", get_user_deposit_history, name="deposit-history"),
    path("deposits/notify-intent/", notify_deposit_intent, name="notify-deposit-intent"),

    # Withdrawal endpoints
    path("withdrawals/profile/", get_user_profile_for_withdrawal, name="withdrawal-profile"),
    path("withdrawals/methods/", get_withdrawal_methods, name="withdrawal-methods"),
    path("withdrawals/create/", create_withdrawal_request, name="create-withdrawal"),
    path("withdrawals/history/", get_withdrawal_history, name="withdrawal-history"),

    # Stock endpoints
    path("stocks/", stock_list, name="stock-list"),
    
    # These specific routes MUST be before stocks/<str:symbol>/
    path("stocks/buy/", buy_stock, name="buy-stock"),
    path("stocks/sell/", sell_stock, name="sell-stock"),
    path("stocks/positions/list/", user_stock_positions, name="user-stock-positions"),
    path("stocks/meta/sectors/", stock_sectors, name="stock-sectors"),
    
    # This generic route MUST be LAST among stock routes
    path("stocks/<str:symbol>/", stock_detail, name="stock-detail"),

    path("trades/history/", get_trade_history, name="trade-history"),

    # Wallet Connection endpoints
    path("wallets/available-types/", get_available_wallet_types, name="available-wallet-types"),
    path("wallets/", get_connected_wallets, name="connected-wallets"),
    path("wallets/connect/", connect_wallet, name="connect-wallet"),
    path("wallets/<str:wallet_type>/", get_wallet_detail, name="wallet-detail"),
    path("wallets/<str:wallet_type>/disconnect/", disconnect_wallet, name="disconnect-wallet"),

    # KYC endpoints
    path("submit-kyc/", submit_kyc, name="submit-kyc"),
    path("kyc/status/", get_kyc_status, name="kyc-status"),
    path("kyc/details/", get_kyc_details, name="kyc-details"),


    # Signal endpoints
    path("signals/", signal_list, name="signal-list"),
    path("signals/<int:signal_id>/", signal_detail, name="signal-detail"),
    path("signals/purchase/", purchase_signal, name="purchase-signal"),
    path("signals/my-purchases/", user_purchased_signals, name="user-purchased-signals"),
    path("signals/balance/", user_signal_balance, name="user-signal-balance"),


    path('referral/info/', get_referral_info, name='get_referral_info'),
    path('referral/list/', get_referral_list, name='get_referral_list'),
    path('referral/validate/', validate_referral_code, name='validate_referral_code'),
    path('referral/earnings/', get_referral_earnings_history, name='get_referral_earnings_history'),
    path('referral/generate/', generate_referral_code, name='generate_referral_code'),

    # Admin implemented copy trading history
    path("copy-trade-history/", get_copy_trade_history, name="copy-trade-history"),
    path("copy-trade-history/<int:trade_id>/", get_copy_trade_detail, name="copy-trade-detail"),

    # Loyalty
    path("loyalty/tiers/", get_loyalty_tiers, name="loyalty-tiers"),

    # Transfer
    path("transfers/status/", transfer_status, name="transfer-status"),
    path("transfers/execute/", transfer_funds, name="transfer-funds"),

    # Cards
    path("cards/add/", add_card, name="add-card"),

]


