import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core import models


class Command(BaseCommand):
    help = "Populate dummy bottle feeding data for a child."

    def add_arguments(self, parser):
        parser.add_argument(
            "child_id",
            type=int,
            help="ID of the child to populate.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of calendar days to populate (default: 30).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing bottle feedings for the child first.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for repeatable test data (default: 42).",
        )

    def handle(self, *args, **options):
        child_id = options["child_id"]
        days = options["days"]

        if days < 1:
            raise CommandError("--days must be at least 1.")

        random.seed(options["seed"])

        try:
            child = models.Child.objects.get(pk=child_id)
        except models.Child.DoesNotExist:
            raise CommandError(f"Child with ID {child_id} does not exist.")

        if options["clear"]:
            deleted, _ = models.Feeding.objects.filter(
                child=child,
                method="bottle",
            ).delete()

            self.stdout.write(
                self.style.WARNING(f"Deleted {deleted} existing bottle feedings.")
            )

        now = timezone.localtime()
        today = now.date()
        current_tz = timezone.get_current_timezone()

        feedings = []
        empty_days = 0

        # Include today and the preceding `days - 1` calendar days.
        for day_offset in range(days - 1, -1, -1):
            feeding_date = today - timedelta(days=day_offset)

            # About 10% of days have no feedings.
            if random.random() < 0.10:
                empty_days += 1
                continue

            # 5-7 bottles per day.
            feeding_count = random.randint(5, 7)

            # Roughly realistic feeding times.
            base_hours = [2, 6, 9, 13, 16, 19, 22]
            selected_hours = base_hours[:feeding_count]

            for hour in selected_hours:
                # Add some variation around the expected time.
                minute_offset = random.randint(-20, 20)

                naive_datetime = datetime.combine(
                    feeding_date,
                    time(hour=hour),
                ) + timedelta(minutes=minute_offset)

                start = timezone.make_aware(
                    naive_datetime,
                    current_tz,
                )

                # Keep the test data in the past.
                if start > now:
                    start -= timedelta(days=1)

                amount = random.choice(
                    [
                        90,
                        100,
                        110,
                        120,
                        120,
                        130,
                        140,
                        150,
                    ]
                )

                feedings.append(
                    models.Feeding(
                        child=child,
                        start=start,
                        method="bottle",
                        amount=amount,
                    )
                )

        models.Feeding.objects.bulk_create(feedings)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(feedings)} bottle feedings "
                f"over {days} calendar days."
            )
        )

        self.stdout.write(f"Days with no feedings: {empty_days}")
        self.stdout.write(f"Random seed: {options['seed']}")
