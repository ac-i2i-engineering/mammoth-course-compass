from django.shortcuts import render, redirect
from django.core.management import call_command
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from .models import Course, CourseRating
from .forms import CourseForm, CSVUploadForm, CourseReviewForm
import string, random

def generate_confirmation_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

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

def create_review(request):
    if request.method == 'POST':
        # Check if this is the confirmation step
        if 'confirmation_code' in request.POST:
            stored_code = request.session.get('confirmation_code')
            submitted_code = request.POST['confirmation_code']
            stored_form_data = request.session.get('form_data')
            
            if stored_code and stored_code == submitted_code and stored_form_data:
                form = CourseReviewForm(stored_form_data)
                if form.is_valid():
                    email = form.cleaned_data['email']
                    user, _ = User.objects.get_or_create(
                        email=email,
                        defaults={'username': email.split('@')[0]}
                    )
                    review = form.save(commit=False)
                    review.user = user
                    review.overall = review.calculate_overall_rating()
                    review.save()
                    
                    # Clear session data
                    del request.session['confirmation_code']
                    del request.session['form_data']
                    return redirect('home')
            return render(request, 'mammoth_course_compass_algo/confirm_email.html', {
                'error': 'Invalid confirmation code',
                'email': request.session.get('form_data', {}).get('email', '')
            })
            
        # Initial form submission
        form = CourseReviewForm(request.POST)
        if form.is_valid():
            # Store form data in session
            request.session['form_data'] = request.POST
            email = form.cleaned_data['email']
            
            # Generate and store confirmation code
            code = generate_confirmation_code()
            request.session['confirmation_code'] = code
            
            # Send verification email
            send_mail(
                'Confirm your course review',
                f'Your confirmation code is: {code}',
                'mammothcoursecompass@gmail.com',
                [email],
                fail_silently=False,
            )
            
            return render(request, 'mammoth_course_compass_algo/confirm_email.html', {
                'email': email
            })
    else:
        form = CourseReviewForm()
    
    return render(request, 'mammoth_course_compass_algo/create_review.html', {'form': form})