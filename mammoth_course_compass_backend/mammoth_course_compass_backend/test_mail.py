import os
import sys
import django
from dotenv import load_dotenv

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

# Load environment variables first
load_dotenv()

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mammoth_course_compass_backend.settings')
django.setup()

from django.core.mail import send_mail

# Test email sending
try:
    send_mail(
        'Test Subject',
        'Test Message',
        'mammothcoursecompass@gmail.com',
        ['bshen28@amherst.edu'],  # Replace with your Amherst email
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")