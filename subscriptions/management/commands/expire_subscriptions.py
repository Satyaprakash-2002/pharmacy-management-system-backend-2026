
from django.core.management.base import BaseCommand

from subscriptions.services import expire_subscriptions


#-----------------------------------------------------------#
# Automatic Subscription Expiry Management Command
#-----------------------------------------------------------#

class Command(BaseCommand):

    help = "Automatically expire subscriptions whose end date has passed."

    def handle(self, *args, **options):

        expired_count = expire_subscriptions()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully expired {expired_count} subscription(s)."
            )
        )
