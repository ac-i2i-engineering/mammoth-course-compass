import os
from django.core.management.base import BaseCommand
from access_amherst_algo.email_scraper.email_saver import process_email_events

class Command(BaseCommand):
    help = "Process email events and save them to the database"

    def handle(self, *args, **kwargs):
        try:
            process_email_events()
            self.stdout.write(self.style.SUCCESS("Successfully processed email events"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing email events: {e}"))
