import pytest
from unittest import mock
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase
from mammoth_course_compass_algo.models import Course, CourseRating

@pytest.fixture
def mock_course():
    with mock.patch('mammoth_course_compass_algo.models.Course.objects.create') as mock_create:
        mock_course = mock.Mock(spec=Course)
        mock_course.code = "COSC111"
        mock_course.title = "Introduction to Computer Science"
        mock_course.description = "An introductory course to computer science."
        mock_course.department = "COSC"
        mock_course.professor = "Prof. John Doe"
        mock_course.keywords = "computer science, programming, algorithms"
        mock_course.__str__ = mock.Mock(return_value="COSC111: Introduction to Computer Science")
        mock_create.return_value = mock_course
        yield mock_course

@pytest.fixture
def mock_user():
    with mock.patch('django.contrib.auth.models.User.objects.create_user') as mock_create_user:
        mock_user = mock.Mock(spec=User)
        mock_user.username = 'testuser'
        mock_create_user.return_value = mock_user
        yield mock_user

@pytest.fixture
def mock_course_rating(mock_user, mock_course):
    with mock.patch('mammoth_course_compass_algo.models.CourseRating.objects.create') as mock_create:
        mock_rating = mock.Mock(spec=CourseRating)
        mock_rating.user = mock_user
        mock_rating.course = mock_course
        mock_rating.materials = 4
        mock_rating.course_content = 5
        mock_rating.workload = 3
        mock_rating.difficulty = 2
        mock_rating.professor = 5
        mock_rating.would_take_again = True
        mock_rating.attendance_mandatory = False
        mock_rating.__str__ = mock.Mock(return_value="testuser's rating for COSC111 (Overall: 4.4)")
        mock_rating.calculate_overall_rating = mock.Mock(return_value=4.4)
        mock_rating.get_category_averages = mock.Mock(return_value={
            'materials': 4,
            'course_content': 5,
            'workload': 3,
            'difficulty': 2,
            'professor': 5,
            'overall': 4.4
        })
        
        def create_side_effect(*args, **kwargs):
            if kwargs.get('user') == mock_user and kwargs.get('course') == mock_course:
                raise IntegrityError("UNIQUE constraint failed: user, course")
            return mock_rating
        
        mock_create.side_effect = create_side_effect
        yield mock_rating

class CourseModelTest(TestCase):

    @pytest.fixture(autouse=True)
    def _setup(self, mock_course):
        self.course = mock_course

    def test_course_creation(self):
        self.assertEqual(self.course.code, "COSC111")
        self.assertEqual(self.course.title, "Introduction to Computer Science")
        self.assertEqual(self.course.description, "An introductory course to computer science.")
        self.assertEqual(self.course.department, "COSC")
        self.assertEqual(self.course.professor, "Prof. John Doe")
        self.assertEqual(self.course.keywords, "computer science, programming, algorithms")

    def test_course_str(self):
        self.assertEqual(str(self.course), "COSC111: Introduction to Computer Science")

    def test_get_rating_statistics_no_ratings(self):
        self.course.get_rating_statistics.return_value = {
            'materials': None,
            'course_content': None,
            'workload': None,
            'difficulty': None,
            'professor': None,
            'overall': None,
            'total_ratings': 0,
            'would_take_again_percentage': None
        }
        stats = self.course.get_rating_statistics()
        self.assertEqual(stats, {
            'materials': None,
            'course_content': None,
            'workload': None,
            'difficulty': None,
            'professor': None,
            'overall': None,
            'total_ratings': 0,
            'would_take_again_percentage': None
        })

class CourseRatingModelTest(TestCase):

    @pytest.fixture(autouse=True)
    def _setup(self, mock_user, mock_course, mock_course_rating):
        self.user = mock_user
        self.course = mock_course
        self.rating = mock_course_rating

    def test_course_rating_creation(self):
        self.assertEqual(self.rating.user, self.user)
        self.assertEqual(self.rating.course, self.course)
        self.assertEqual(self.rating.materials, 4)
        self.assertEqual(self.rating.course_content, 5)
        self.assertEqual(self.rating.workload, 3)
        self.assertEqual(self.rating.difficulty, 2)
        self.assertEqual(self.rating.professor, 5)
        self.assertTrue(self.rating.would_take_again)
        self.assertFalse(self.rating.attendance_mandatory)

    def test_course_rating_str(self):
        self.assertEqual(str(self.rating), "testuser's rating for COSC111 (Overall: 4.4)")

    def test_calculate_overall_rating(self):
        self.assertEqual(self.rating.calculate_overall_rating(), 4.4)

    def test_get_category_averages(self):
        averages = self.rating.get_category_averages()
        self.assertEqual(averages, {
            'materials': 4,
            'course_content': 5,
            'workload': 3,
            'difficulty': 2,
            'professor': 5,
            'overall': 4.4
        })

    def test_unique_together_constraint(self):
        with self.assertRaises(IntegrityError):
            CourseRating.objects.create(
                user=self.user,
                course=self.course,
                materials=3,
                course_content=4,
                workload=2,
                difficulty=3,
                professor=4
            )

    def test_get_rating_statistics_with_ratings(self):
        self.course.get_rating_statistics.return_value = {
            'materials': 4.0,
            'course_content': 5.0,
            'workload': 3.0,
            'difficulty': 2.0,
            'professor': 5.0,
            'overall': 4.4,
            'total_ratings': 1,
            'would_take_again_percentage': 100.0
        }
        stats = self.course.get_rating_statistics()
        self.assertEqual(stats, {
            'materials': 4.0,
            'course_content': 5.0,
            'workload': 3.0,
            'difficulty': 2.0,
            'professor': 5.0,
            'overall': 4.4,
            'total_ratings': 1,
            'would_take_again_percentage': 100.0
        })