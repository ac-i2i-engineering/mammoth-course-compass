# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Course, CourseRating
from django.core.validators import RegexValidator
from django.core.mail import send_mail
import random
import string
from django.shortcuts import render, redirect

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'department', 'professor', 'keywords', 'prerequisites']

class CSVUploadForm(forms.Form):
    file = forms.FileField()

class CourseReviewForm(forms.ModelForm):
    email = forms.EmailField(
        help_text="Enter your Amherst email address",
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9._%+-]+@amherst\.edu$',
                message='Please use your Amherst email address (@amherst.edu)'
            )
        ]
    )

    class Meta:
        model = CourseRating
        fields = [
            'course',
            'materials',
            'course_content',
            'workload',
            'difficulty',
            'professor',
            'would_take_again',
            'attendance_mandatory',
            'review',
        ]