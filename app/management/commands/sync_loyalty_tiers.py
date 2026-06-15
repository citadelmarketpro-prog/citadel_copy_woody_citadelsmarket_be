"""
Management command to sync all users' loyalty tiers based on their total completed deposits.

Safe for production — does NOT credit rank bonuses or create notifications.
Only sets: current_loyalty_status, next_loyalty_status, next_amount_to_upgrade.

Usage:
    python manage.py sync_loyalty_tiers          # dry run (shows what would change)
    python manage.py sync_loyalty_tiers --apply   # actually write changes to the database
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum

from app.models import CustomUser, Transaction


TIER_ORDER  = CustomUser.LOYALTY_TIER_ORDER
TIER_CONFIG = CustomUser.LOYALTY_TIER_CONFIG
CHUNK_SIZE  = 100   # fetch this many user IDs at a time — avoids server-side cursors


def determine_tier(total_deposits):
    """Return the highest tier a user qualifies for based on total deposits."""
    tier = "iron"
    for key in TIER_ORDER:
        if total_deposits >= TIER_CONFIG[key]["min_deposit"]:
            tier = key
    return tier


def get_next_tier_info(current_tier):
    """Return (next_tier_key, next_amount_to_upgrade) for a given tier."""
    idx = TIER_ORDER.index(current_tier)
    if idx < len(TIER_ORDER) - 1:
        next_key = TIER_ORDER[idx + 1]
        return next_key, Decimal(str(TIER_CONFIG[next_key]["min_deposit"]))
    # Already at highest tier
    return current_tier, Decimal("0.00")


class Command(BaseCommand):
    help = "Sync every user's loyalty tier based on their total completed deposits."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Write changes to the database. Without this flag the command is a safe dry run.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        if not apply:
            self.stdout.write(self.style.WARNING(
                "\n  DRY RUN — no changes will be saved. Add --apply to write to the database.\n"
            ))

        # Fetch all user PKs up front into a plain Python list.
        # This avoids server-side cursors (the cause of the
        # "cursor does not exist" error on PostgreSQL) because the
        # full ID list is small and fits comfortably in memory.
        all_ids = list(
            CustomUser.objects.order_by("id").values_list("id", flat=True)
        )
        total_users = len(all_ids)
        updated       = 0
        already_correct = 0
        errors        = []

        self.stdout.write(f"Processing {total_users} user(s) in chunks of {CHUNK_SIZE}...\n")

        # Process in chunks so each DB round-trip is bounded.
        for chunk_start in range(0, total_users, CHUNK_SIZE):
            chunk_ids = all_ids[chunk_start: chunk_start + CHUNK_SIZE]

            # Fetch full objects for this chunk only — no open cursor held.
            users_chunk = CustomUser.objects.filter(id__in=chunk_ids).order_by("id")

            for user in users_chunk:
                try:
                    total_deposits = Transaction.objects.filter(
                        user=user,
                        transaction_type="deposit",
                        status="completed",
                    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

                    correct_tier        = determine_tier(total_deposits)
                    next_tier, next_amount = get_next_tier_info(correct_tier)

                    needs_update = (
                        user.current_loyalty_status != correct_tier
                        or user.next_loyalty_status  != next_tier
                        or user.next_amount_to_upgrade != next_amount
                    )

                    if not needs_update:
                        already_correct += 1
                        continue

                    old_tier = user.current_loyalty_status

                    if apply:
                        user.current_loyalty_status  = correct_tier
                        user.next_loyalty_status     = next_tier
                        user.next_amount_to_upgrade  = next_amount
                        user.save(update_fields=[
                            "current_loyalty_status",
                            "next_loyalty_status",
                            "next_amount_to_upgrade",
                        ])

                    updated += 1
                    self.stdout.write(
                        f"  {'UPDATED' if apply else 'WOULD UPDATE'}: "
                        f"{user.email} | "
                        f"deposits=${total_deposits:,.2f} | "
                        f"{old_tier} -> {correct_tier} | "
                        f"next={next_tier} (${next_amount:,.2f})"
                    )

                except Exception as exc:
                    errors.append((user.email, str(exc)))
                    self.stderr.write(self.style.ERROR(
                        f"  ERROR: {user.email} — {exc}"
                    ))

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"  Total users:      {total_users}")
        self.stdout.write(f"  Already correct:  {already_correct}")
        self.stdout.write(f"  {'Updated' if apply else 'Would update'}:       {updated}")

        if errors:
            self.stdout.write(self.style.ERROR(f"  Errors:           {len(errors)}"))
            for email, msg in errors:
                self.stderr.write(f"    - {email}: {msg}")
        else:
            self.stdout.write(self.style.SUCCESS("  Errors:           0"))

        if not apply and updated > 0:
            self.stdout.write(self.style.WARNING(
                f"\n  Run again with --apply to save these {updated} change(s).\n"
            ))
        elif apply:
            self.stdout.write(self.style.SUCCESS("\n  Done. All changes saved.\n"))
        else:
            self.stdout.write(self.style.SUCCESS("\n  All users are already on the correct tier.\n"))
