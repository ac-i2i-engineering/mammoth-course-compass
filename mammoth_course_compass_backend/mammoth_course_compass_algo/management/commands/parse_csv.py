import os
from django.core.management.base import BaseCommand
from mammoth_course_compass_algo.clean_data import load_and_validate_csv, clean_ratings_data, create_course_ratings

class Command(BaseCommand):
    help = 'Import course ratings from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Path to the CSV file containing course ratings')

    def handle(self, *args, **kwargs):
        file_path = kwargs['filepath']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR('File does not exist'))
            return
        
        try:
            df = load_and_validate_csv(file_path)
            df_cleaned = clean_ratings_data(df)
            created, failed = create_course_ratings(df_cleaned)
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported {created} ratings. Failed: {failed}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))