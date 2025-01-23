
from django.core.management.base import BaseCommand
from mammoth_course_compass_algo.models import Course

class Command(BaseCommand):
    help = 'Create courses in the database'

    def handle(self, *args, **kwargs):
        # Add your courses here
        courses_to_create = [
            {'code': '175', 'title': 'Introduction to Computer Science', 'department': 'COSC'},
            {'code': '1', 'title': 'How to Make a Fake Class', 'department': 'COSC'},
            # Add more courses as needed
        ]

        created_count = 0
        for course_data in courses_to_create:
            try:
                Course.objects.get_or_create(
                    code=course_data['code'],
                    defaults={
                        'title': course_data['title'],
                        'department': course_data['department']
                    }
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create course {course_data['code']}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} courses'))