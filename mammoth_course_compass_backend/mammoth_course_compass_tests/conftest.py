import os
import sys
import django
import pytest

def pytest_configure():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mammoth_course_compass_backend.settings')
    django.setup()

@pytest.fixture
def user(db):
    from django.contrib.auth.models import User
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def course(db):
    from mammoth_course_compass_algo.models import Course
    return Course.objects.create(
        code="COSC111",
        title="Introduction to Computer Science",
        description="An introductory course to computer science.",
        department="COSC",
        professor="Prof. John Doe",
        keywords="computer science, programming, algorithms"
    )

@pytest.fixture
def course_rating(db, user, course):
    from mammoth_course_compass_algo.models import CourseRating
    return CourseRating.objects.create(
        user=user,
        course=course,
        materials=4,
        course_content=5,
        workload=3,
        difficulty=2,
        professor=5,
        would_take_again=True,
        attendance_mandatory=False
    )