from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from course.models import Course
from course.forms import CourseForm, DeleteCourseForm, SlideSelectionForm
from slide.models import Slide
from tag.models import Tag
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


@teacher_required
def slide_selection(request, course_id):
    """
    Teacher form for adding slide(s) to a course
    """

    course = get_object_or_404(Course, id=course_id)

    allSlides = Slide.objects.all()
    """filteredSlides = Slide.objects.all()

    # Filters
    organs = request.GET.getlist('organ[]')
    if len(organs) > 0:
        filteredSlides = filteredSlides.filter(tags__in=organs)
    systems = request.GET.getlist('system[]')
    if len(systems) > 0:
        filteredSlides = filteredSlides.filter(tags__in=systems)
    tags = request.GET.getlist('tag[]')
    if len(tags) > 0:
        filteredSlides = filteredSlides.filter(tags__in=systems)"""


    if request.method == 'POST':  # Form was submitted

        selectedSlides = [int(slide_id) for slide_id in request.POST.getlist('slide_selection')]

        for slide in allSlides:
            # If selected, but not currently in course
            if slide.id in selectedSlides and slide not in course.slide.all():
                course.slide.add(slide)
            # If unselected, but currently in course
            elif slide.id not in selectedSlides and slide in course.slide.all():
                course.slide.remove(slide)

        course.save()
        # Give a message back to the user
        messages.add_message(request, messages.SUCCESS,
                             'The course slides were updated')
        return redirect('course:view', course_id)

    else:  # GET
        selectedSlides = [slide.id for slide in course.slide.all()]

    context = {
        'course': course,
        'selection': selectedSlides,
        'slides': allSlides,
        #'filtered_slides': filteredSlides,
        #'organ_tags': Tag.objects.filter(is_organ=True),
        #'system_tags': Tag.objects.filter(is_system=True),
        #'other_tags': Tag.objects.filter(is_system=False, is_organ=False),
        #'selected_organ_tags': organs,
        #'selected_system_tags': systems,
        #'selected_other_tags': tags,
    }

    return render(request, 'course/slide_selection.html', context)
