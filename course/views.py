from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from course.models import Course
from course.forms import CourseForm, DeleteCourseForm
from slide.models import Slide
from task.models import Task
from user.decorators import teacher_required


def index(request):
    """
    Show index of available courses
    """

    courses = Course.objects.all()
    return render(request, "course/index.html",
                  {'courses': Course.objects.all().order_by('code')})


def course_page(request, course_id):
    """
    Display a course page with course information and related slides and tasks
    """

    course = Course.objects.get(id=course_id)
    tasks = Task.objects.filter(course=course)
    slides = Slide.objects.filter(course=course)

    return render(request, 'course/course_page.html', {
        'course': course,
        'tasks': tasks,
        'slides': slides,
    })


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
            return redirect('course:index')
        else:
            # Render form with errors
            pass
    else:
        courseForm = CourseForm()

    return render(request, 'course/new.html', {'form': courseForm})


@teacher_required
def edit(request, course_id):
    """
    Teacher form for editing a course
    """

    course = get_object_or_404(Course, id=course_id)
    courseForm = CourseForm(request.POST or None, instance=course)

    if request.method == 'POST':  # Form was submitted
        if courseForm.is_valid():
            courseForm.save()
            messages.add_message(request, messages.SUCCESS,
                 f'The course {course.code} - {course.title} was altered!')
            return redirect('course:index')

    return render(request, 'course/edit.html', {'form': courseForm})


@teacher_required
def delete(request, course_id):
    """
    View to delete a course from the course database
    """

    if request.method == 'POST':  # Form was submitted
        form = DeleteCourseForm(request.POST)

        if form.is_valid():
            course = Course.objects.get(id=course_id)
            txt = f"{course.code} - {course.title}"

            if form.cleaned_data['confirmDelete']:
                course.delete()
                messages.add_message(request, messages.SUCCESS, f'The course {txt} was deleted')
            else:
                messages.add_message(request, messages.SUCCESS, f'The course {txt} was not deleted')

            return redirect('course:index')

    else:  # GET method
        # Render page with course info and "Delete? Yes/No"
        if course_id in Course.objects.all().values_list('id', flat=True):
            course = Course.objects.all().get(id=course_id)
            return render(request, 'course/delete.html',
                          {'form': DeleteCourseForm(), 'course': course})

        else:  # In case user enters invalid URL directly
            messages.add_message(request, messages.WARNING, 'Did not find course')
            return redirect('course:index')

    return redirect('course:index')
