from django.contrib import admin
from .models import UserProfile, Course, CourseRating

admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(CourseRating)
