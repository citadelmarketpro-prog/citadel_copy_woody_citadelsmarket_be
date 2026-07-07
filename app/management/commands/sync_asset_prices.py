import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from app.models import Asset
from app import fmp_client


def _to_fmp_symbol(symbol):
    """Normalise DB symbol to FMP format: remove slashes and spaces."""
    return symbol.replace("/", "").replace(" ", "").upper()


class Command(BaseCommand):
    help = "Sync live bid/ask/low/high/change prices from FMP into the Asset model."

    def handle(self, *args, **options):
        assets = list(Asset.objects.all())
        if not assets:
            self.stdout.write("No assets in database.")
            return

        # Build FMP-symbol → Asset mapping
        symbol_map = {}
        for asset in assets:
            fmp_sym = _to_fmp_symbol(asset.symbol)
            symbol_map[fmp_sym] = asset

        try:
            quotes = fmp_client.get_quotes(list(symbol_map.keys()))
        except Exception as exc:
            self.stderr.write(f"FMP API error: {exc}")
            return

        if not isinstance(quotes, list):
            self.stderr.write(f"Unexpected FMP response: {quotes}")
            return

        updated = not_found = 0
        for quote in quotes:
            fmp_sym = (quote.get("symbol") or "").upper()
            asset = symbol_map.get(fmp_sym)
            if not asset:
                not_found += 1
                continue

            price      = float(quote.get("price") or 0)
            bid        = float(quote.get("bid") or 0) or round(price * 0.9999, 6)
            ask        = float(quote.get("ask") or 0) or round(price * 1.0001, 6)
            day_low    = float(quote.get("dayLow") or quote.get("low") or price)
            day_high   = float(quote.get("dayHigh") or quote.get("high") or price)
            change_pct = float(quote.get("changePercentage") or quote.get("changesPercentage") or 0)

            ts = quote.get("timestamp")
            try:
                t = datetime.datetime.fromtimestamp(int(ts)).time() if ts else datetime.datetime.now().time()
            except Exception:
                t = datetime.datetime.now().time()

            asset.bid    = Decimal(str(round(bid,    6)))
            asset.ask    = Decimal(str(round(ask,    6)))
            asset.low    = Decimal(str(round(day_low, 6)))
            asset.high   = Decimal(str(round(day_high, 6)))
            asset.change = change_pct
            asset.time   = t
            asset.save(update_fields=["bid", "ask", "low", "high", "change", "time"])
            self.stdout.write(f"  {asset.symbol}: bid={bid:.6f} ask={ask:.6f} chg={change_pct:.2f}%")
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Asset price sync: {updated} updated, {not_found} symbols not returned by FMP"
            )
        )
