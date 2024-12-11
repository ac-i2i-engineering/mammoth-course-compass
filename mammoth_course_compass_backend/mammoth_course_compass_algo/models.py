from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg

"""
Models for managing courses and course ratings at Amherst College.

This module contains the core models for the course rating system:
- Course: Represents an academic course with its details and aggregated ratings
- CourseRating: Represents a student's rating and review of a specific course

These models work together to provide a comprehensive course rating and review system.
"""

class Course(models.Model):
    """
    Course model representing an academic course at Amherst College with details about the course. 
    This class stores course information and provides methods for retrieving rating data.

    Parameters
    ----------
    code : str
        The course code identifier (e.g., "COSC111")
    title : str  
        The full title of the course
    description : str
        A detailed description of the course content
    department : str
        The 4-letter department code (e.g., "COSC", "BCBP")
    professor : str
        Professor of the course
    keywords : str, optional
        Course keywords used for content-based filtering
    prerequisites : ManyToManyField
        Related Course objects that are prerequisites for this course

    Methods
    -------
    get_rating_statistics()
        Returns a dictionary containing current rating statistics
    __str__()
        Returns a string representation of the course (code and title)
    """

    code = models.CharField(max_length=8)  # e.g., "COSC-111"
    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=4) # Use 4-letter department code, e.g., "COSC", "BCBP"
    professor = models.CharField(max_length=100)
    # Add fields that will be used for content-based filtering (currently implementing a content-based filtering recommendation system)
    keywords = models.TextField(blank=True)  # store course keywords
    prerequisites = models.ManyToManyField('self', blank=True)

    # Rating statistics
    def get_rating_statistics(self):
        """
        Returns a dictionary of all rating statistics
        Calculates the values directly from courseRating
        """
        ratings = CourseRating.objects.filter(course=self)
        count = ratings.count()

        def safe_round(value):
            return round(value, 2) if value is not None else None

        return {
            'materials': safe_round(ratings.aggregate(Avg('materials'))['materials__avg']),
            'course_content': safe_round(ratings.aggregate(Avg('course_content'))['course_content__avg']),
            'workload': safe_round(ratings.aggregate(Avg('workload'))['workload__avg']),
            'difficulty': safe_round(ratings.aggregate(Avg('difficulty'))['difficulty__avg']),
            'professor': safe_round(ratings.aggregate(Avg('professor'))['professor__avg']),
            'overall': safe_round(ratings.aggregate(Avg('overall'))['overall__avg']),
            'total_ratings': count,
            'would_take_again_percentage': safe_round(ratings.filter(would_take_again=True).count() / count * 100) if count > 0 else None
        }

    def __str__(self):
        return f"{self.code}: {self.title}"

class CourseRating(models.Model):
    """
    CourseRating model representing a student's rating and review of a specific course. This class 
    stores individual rating data across multiple categories and provides methods for calculating 
    overall ratings.

    Parameters
    ----------
    user : ForeignKey
        Reference to the User who submitted the rating
    course : ForeignKey
        Reference to the Course being rated
    timestamp : datetime
        When the rating was submitted
    review : str, optional
        Text review of the course
    overall : float, optional
        Calculated overall rating based on category ratings
    materials : int
        Rating for relevancy/usefulness of materials on a 1-5 scale
    course_content : int
        Rating for course content quality on a 1-5 scale
    workload : int
        Rating for course workload (1=easy, 5=difficult)
    difficulty : int
        Rating for course difficulty (1=easy, 5=difficult)
    professor : int
        Rating of the professor on a 1-5 scale
    would_take_again : bool, optional
        Whether the student would take the course again
    attendance_mandatory : bool, optional
        Whether course attendance was mandatory

    Methods
    -------
    calculate_overall_rating()
        Calculates weighted average rating across all categories
    get_category_averages()
        Returns dictionary of ratings for each category
    __str__()
        Returns string representation of the rating

    Meta
    ----
    unique_together : [user, course]
        Ensures one rating per user per course
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    review = models.TextField(blank=True)
    overall = models.FloatField(null=True, blank=True)

    # Rating categories (all on 1-5 scale)
    materials = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate the quality of instruction and teaching effectiveness"
    )
    
    course_content = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate the quality and relevance of course materials and content"
    )
    
    workload = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate the manageability of assignments and workload (1 = very easy, 5 = very difficult)"
    )
    
    difficulty = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate the difficulty level (1 = very easy, 5 = very difficult)"
    )
    
    professor = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate how engaging, helpful the professor was"
    )
    
    # Optional fields that might be useful
    would_take_again = models.BooleanField(
        default=None, 
        null=True,
        help_text="Would you take this course again?"
    )
    
    attendance_mandatory = models.BooleanField(
        default=None, 
        null=True,
        help_text="Was attendance mandatory?"
    )
    
    class Meta:
        unique_together = ['user', 'course']
    
    def calculate_overall_rating(self):
        """
        Calculate overall rating using weighted average of categories.
        For workload and difficulty, we invert the scores since their scales are reversed
        (1 = heavy/difficult which is generally considered less favorable)
        """
        # Invert workload and difficulty scores (1->5, 2->4, 3->3, 4->2, 5->1)
        adjusted_workload = 6 - self.workload
        adjusted_difficulty = 6 - self.difficulty
        
        # adjust weights of different categories (currently all even)
        weights = {
            'materials': 0.20,
            'course_content': 0.20,
            'workload': 0.20,
            'difficulty': 0.20,
            'professor': 0.20,
        }
        
        overall = (
            self.materials * weights['materials'] +
            self.course_content * weights['course_content'] +
            adjusted_workload * weights['workload'] +
            adjusted_difficulty * weights['difficulty'] +
            self.professor * weights['professor']
        )
        
        return round(overall, 2)

    def get_category_averages(self):
        """
        Returns a dictionary of average ratings for each category
        """
        return {
            'materials': self.materials,
            'course_content': self.course_content,
            'workload': self.workload,
            'difficulty': self.difficulty,
            'professor': self.professor,
            'overall': self.calculate_overall_rating()
        }

    def __str__(self):
        return f"{self.user.username}'s rating for {self.course.code} (Overall: {self.calculate_overall_rating()})"