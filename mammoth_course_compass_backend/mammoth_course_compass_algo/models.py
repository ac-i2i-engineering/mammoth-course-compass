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
    Course model representing an academic course at Amherst College with details about the course 
    and aggregated rating statistics. This class stores course information and provides methods 
    for managing and retrieving rating data.

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
    credits : int
        Number of credits for the course
    keywords : str, optional
        Course keywords used for content-based filtering
    prerequisites : ManyToManyField
        Related Course objects that are prerequisites for this course
    avg_overall : float, optional
        Average overall rating on a 1-5 scale
    avg_quality_of_teaching : float, optional
        Average rating for teaching quality on a 1-5 scale
    avg_course_content : float, optional
        Average rating for course content on a 1-5 scale
    avg_workload : float, optional
        Average rating for course workload on a 1-5 scale
    avg_difficulty : float, optional
        Average rating for course difficulty on a 1-5 scale
    avg_engagement : float, optional
        Average rating for student engagement on a 1-5 scale
    total_ratings : int
        Total number of ratings submitted for this course
    would_take_again_percentage : float, optional
        Percentage of students who would take the course again

    Methods
    -------
    update_rating_statistics()
        Updates all aggregated rating fields based on submitted ratings
    get_rating_statistics()
        Returns a dictionary containing current rating statistics
    __str__()
        Returns a string representation of the course (code and title)
    """

    code = models.CharField(max_length=8)  # e.g., "COSC-111"
    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=4) # Use 4-letter department code, e.g., "COSC", "BCBP"
    credits = models.IntegerField()
    # Add fields that will be used for content-based filtering (currently implementing a content-based filtering recommendation system)
    keywords = models.TextField(blank=True)  # store course keywords
    prerequisites = models.ManyToManyField('self', blank=True)
    # Rating fields
    avg_overall = models.FloatField(null=True, blank=True)
    avg_quality_of_teaching = models.FloatField(null=True, blank=True)
    avg_course_content = models.FloatField(null=True, blank=True)
    avg_workload = models.FloatField(null=True, blank=True)
    avg_difficulty = models.FloatField(null=True, blank=True)
    avg_engagement = models.FloatField(null=True, blank=True)
    total_ratings = models.IntegerField(default=0)
    would_take_again_percentage = models.FloatField(null=True, blank=True)

    def update_rating_statistics(self):
        """
        Updates all rating statistics for the course
        Should be called whenever a rating is added, modified, or deleted
        """
        ratings = self.courserating_set.all()
        count = ratings.count()
        
        if count > 0:
            self.avg_quality_of_teaching = ratings.aggregate(Avg('quality_of_teaching'))['quality_of_teaching__avg']
            self.avg_course_content = ratings.aggregate(Avg('course_content'))['course_content__avg']
            self.avg_workload = ratings.aggregate(Avg('workload'))['workload__avg']
            self.avg_difficulty = ratings.aggregate(Avg('difficulty'))['difficulty__avg']
            self.avg_engagement = ratings.aggregate(Avg('engagement'))['engagement__avg']
            self.avg_overall = ratings.aggregate(Avg('overall'))['overall__avg']
            self.total_ratings = count
            self.would_take_again_percentage = (
                ratings.filter(would_take_again=True).count() / count * 100
            )
        else:
            self.avg_quality_of_teaching = None
            self.avg_course_content = None
            self.avg_workload = None
            self.avg_difficulty = None
            self.avg_engagement = None
            self.avg_overall = None
            self.total_ratings = 0
            self.would_take_again_percentage = None
        
        self.save()

    def get_rating_statistics(self):
        """
        Returns a dictionary of all rating statistics
        Now uses stored values instead of calculating them
        """
        return {
            'quality_of_teaching': round(self.avg_quality_of_teaching, 2) if self.avg_quality_of_teaching else None,
            'course_content': round(self.avg_course_content, 2) if self.avg_course_content else None,
            'workload': round(self.avg_workload, 2) if self.avg_workload else None,
            'difficulty': round(self.avg_difficulty, 2) if self.avg_difficulty else None,
            'engagement': round(self.avg_engagement, 2) if self.avg_engagement else None,
            'overall': round(self.avg_overall, 2) if self.avg_overall else None,
            'total_ratings': self.total_ratings,
            'would_take_again_percentage': round(self.would_take_again_percentage, 2) if self.would_take_again_percentage else None
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
    quality_of_teaching : int
        Rating for teaching quality on a 1-5 scale
    course_content : int
        Rating for course content quality on a 1-5 scale
    workload : int
        Rating for course workload (1=easy, 5=difficult)
    difficulty : int
        Rating for course difficulty (1=easy, 5=difficult)
    engagement : int
        Rating for how engaging the course was on a 1-5 scale
    would_take_again : bool, optional
        Whether the student would take the course again
    attendance_mandatory : bool, optional
        Whether course attendance was mandatory

    Methods
    -------
    save()
        Saves the rating and updates course statistics
    delete()
        Deletes the rating and updates course statistics
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
    quality_of_teaching = models.IntegerField(
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
    
    engagement = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate how engaging and interesting the course was"
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
    
    def save(self, *args, **kwargs):
        self.overall = self.calculate_overall_rating()
        super().save(*args, **kwargs)
        self.course.update_rating_statistics()  # Update course statistics after saving

    def delete(self, *args, **kwargs):
        course = self.course  # Store reference to course before deletion
        super().delete(*args, **kwargs)
        course.update_rating_statistics()  # Update course statistics after deletion

    
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
            'quality_of_teaching': 0.20,
            'course_content': 0.20,
            'workload': 0.20,
            'difficulty': 0.20,
            'engagement': 0.20,
        }
        
        overall = (
            self.quality_of_teaching * weights['quality_of_teaching'] +
            self.course_content * weights['course_content'] +
            adjusted_workload * weights['workload'] +
            adjusted_difficulty * weights['difficulty'] +
            self.engagement * weights['engagement']
        )
        
        return round(overall, 2)

    def get_category_averages(self):
        """
        Returns a dictionary of average ratings for each category
        """
        return {
            'quality_of_teaching': self.quality_of_teaching,
            'course_content': self.course_content,
            'workload': self.workload,
            'difficulty': self.difficulty,
            'engagement': self.engagement,
            'overall': self.calculate_overall_rating()
        }

    def __str__(self):
        return f"{self.user.username}'s rating for {self.course.code} (Overall: {self.calculate_overall_rating()})"