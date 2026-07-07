from decimal import Decimal
from django.core.management.base import BaseCommand
from app.models import AdminWallet
from app import fmp_client

# AdminWallet.currency  →  FMP quote symbol
CURRENCY_TO_FMP = {
    "BTC":        "BTCUSD",
    "ETH":        "ETHUSD",
    "SOL":        "SOLUSD",
    "BNB":        "BNBUSD",
    "TRX":        "TRXUSD",
    "XRP":        "XRPUSD",
    # Stablecoins — always ~$1.00; FMP may not have these, so we hardcode
    "USDT ERC20": None,
    "USDT TRC20": None,
    "USDC":       None,
}

STABLECOIN_RATE = Decimal("1.000000")


class Command(BaseCommand):
    help = "Sync live crypto prices from FMP into AdminWallet.amount (deposit rate)."

    def handle(self, *args, **options):
        wallets = AdminWallet.objects.filter(is_active=True)
        if not wallets.exists():
            self.stdout.write("No active wallets found.")
            return

        # Collect unique FMP symbols needed (exclude stablecoins)
        symbols_needed = {
            CURRENCY_TO_FMP[w.currency]
            for w in wallets
            if w.currency in CURRENCY_TO_FMP and CURRENCY_TO_FMP[w.currency]
        }

        price_map = {}
        if symbols_needed:
            try:
                quotes = fmp_client.get_quotes(list(symbols_needed))
                price_map = {
                    q["symbol"].upper(): Decimal(str(q["price"]))
                    for q in quotes
                    if "symbol" in q and "price" in q and q["price"]
                }
            except Exception as exc:
                self.stderr.write(f"FMP API error: {exc}")
                return

        updated = skipped = 0
        for wallet in wallets:
            fmp_sym = CURRENCY_TO_FMP.get(wallet.currency)

            if fmp_sym is None:
                # Stablecoin — set to 1.00
                new_rate = STABLECOIN_RATE
            else:
                new_rate = price_map.get(fmp_sym.upper())
                if new_rate is None:
                    self.stderr.write(f"  No price for {fmp_sym} ({wallet.currency}) — skipped")
                    skipped += 1
                    continue

            wallet.amount = new_rate
            wallet.save(update_fields=["amount", "updated_at"])
            self.stdout.write(f"  {wallet.currency}: ${new_rate:,.6f}")
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Crypto rates sync: {updated} updated, {skipped} skipped")
        )
