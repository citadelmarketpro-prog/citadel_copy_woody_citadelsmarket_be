"""
Management command to backfill initial_investment_amount for UserTraderCopy records
where the field is 0 (created before the field was properly set).

Usage:
    python manage.py fix_investment_amounts           # dry run — shows what would change
    python manage.py fix_investment_amounts --apply   # writes changes to the database
"""

from django.core.management.base import BaseCommand
from app.models import UserTraderCopy


class Command(BaseCommand):
    help = "Backfill initial_investment_amount for UserTraderCopy records where it is 0"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually save changes (default is dry-run)",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        if not apply:
            self.stdout.write(
                "\nDRY RUN — no changes will be saved. Add --apply to write to the database.\n"
            )

        # All records where investment is zero
        zero_records = UserTraderCopy.objects.filter(
            initial_investment_amount=0
        ).select_related("user", "trader")

        total = zero_records.count()
        self.stdout.write(f"Found {total} UserTraderCopy record(s) with initial_investment_amount = 0\n")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to fix.\n"))
            return

        updated = 0
        skipped = 0

        for record in zero_records:
            # Use minimum_threshold_at_start if it was captured, otherwise fall back
            # to the trader's current min_account_threshold
            if record.minimum_threshold_at_start and record.minimum_threshold_at_start > 0:
                new_amount = record.minimum_threshold_at_start
                source = "minimum_threshold_at_start"
            elif record.trader and record.trader.min_account_threshold and record.trader.min_account_threshold > 0:
                new_amount = record.trader.min_account_threshold
                source = "trader.min_account_threshold"
            else:
                self.stdout.write(
                    f"  SKIP: {record.user.email} → {record.trader.name if record.trader else '?'} "
                    f"| no threshold available to backfill"
                )
                skipped += 1
                continue

            self.stdout.write(
                f"  {'UPDATE' if apply else 'WOULD UPDATE'}: "
                f"{record.user.email} → {record.trader.name} "
                f"| {source} = ${new_amount:,.2f}"
            )

            if apply:
                record.initial_investment_amount = new_amount
                record.save(update_fields=["initial_investment_amount"])

            updated += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"  Total records:  {total}")
        self.stdout.write(f"  {'Updated' if apply else 'Would update'}:    {updated}")
        self.stdout.write(f"  Skipped:        {skipped}")

        if apply:
            self.stdout.write(self.style.SUCCESS(f"\n  Done. {updated} record(s) updated.\n"))
        else:
            self.stdout.write(
                f"\n  Run again with --apply to save {updated} change(s).\n"
            )
