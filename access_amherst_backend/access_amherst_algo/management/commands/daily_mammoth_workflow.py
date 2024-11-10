import os
import shutil
from django.core.management.base import BaseCommand
from access_amherst_algo.email_scraper.email_parser import parse_email
from access_amherst_algo.email_scraper.email_saver import process_email_events


class Command(BaseCommand):
    help = "Parse Daily Mammoth into DB"

    def handle(self, *args, **kwargs):
        json_outputs_dir = "access_amherst_algo/email_scraper/json_outputs"

        parse_email("Daily Mammoth")

        try:
            process_email_events()
            self.stdout.write(
                self.style.SUCCESS("Successfully parsed Daily Mammoth into DB")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error processing email events: {e}")
            )
        finally:
            # Clear the json_outputs directory
            self._clear_directory(json_outputs_dir)
            self.stdout.write(
                self.style.SUCCESS("Cleaned up json_outputs directory.")
            )

    @staticmethod
    def _clear_directory(directory):
        """Clears all files in the specified directory."""
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
