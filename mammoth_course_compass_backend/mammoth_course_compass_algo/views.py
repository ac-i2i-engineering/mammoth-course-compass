from django.shortcuts import render, redirect
from django.core.management import call_command
from django.http import HttpResponse
from .models import Course, CourseRating
from .forms import CourseForm, CSVUploadForm

def home(request):
    courses = Course.objects.all()
    reviews = CourseRating.objects.all()
    return render(request, 'mammoth_course_compass_algo/home.html', {'courses': courses, 'reviews': reviews})

def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'mammoth_course_compass_algo/create_course.html', {'form': form})

def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            with open('temp.csv', 'wb+') as destination:
                for chunk in csv_file.chunks():
                    destination.write(chunk)
            call_command('parse_csv', 'temp.csv')
            return redirect('home')
    else:
        form = CSVUploadForm()
    return render(request, 'mammoth_course_compass_algo/upload_csv.html', {'form': form})