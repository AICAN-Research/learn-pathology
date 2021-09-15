from django.shortcuts import render
from user.decorators import teacher_required


def course_page(request, course_id):
    # Show information about course
    # List tasks
    # List slides
    pass

@teacher_required
def new(request):
    # Form
    pass

@teacher_required
def edit(request, course_id):
    # form
    pass

@teacher_required
def delete(request, course_id):
    pass