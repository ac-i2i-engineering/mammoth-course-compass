# forms.py
from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'department', 'professor', 'keywords', 'prerequisites']

class CSVUploadForm(forms.Form):
    file = forms.FileField()