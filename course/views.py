from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect

from course.models import Course, CourseForm
from user.decorators import teacher_required


def index(request):
    """
    Show index of available courses
    """
    return render(request, "course/index.html",
                  {'courses': Course.objects.all().order_by('-code')})


def course_page(request, course_id):
    # Show information about course
    # List tasks
    # List slides
    pass


@teacher_required
def new(request):
    """
    Teacher form for creating a course
    """

    if request.method == 'POST':  # Form was submitted
        courseForm = CourseForm(request.POST)
        if courseForm.is_valid():
            course = courseForm.save(commit=False)
            course.save()
            # Give a message back to the user
            messages.add_message(request, messages.SUCCESS, 'Course added successfully!')
            return redirect('/') # use URL /course_list/ for course_page view above
            #return redirect('course_list') # use URL /course_list/ for course_page view above
        else:
            # Render form with errors
            pass
    else:
        courseForm = CourseForm()

    return render(request, 'course/new.html', {'form': courseForm})


@teacher_required
def edit(request, course_id):
    # form
    pass


@teacher_required
def delete(request, course_id):
    pass