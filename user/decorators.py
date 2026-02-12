from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from functools import wraps
from django.contrib import messages
from task.models import Task
from course.models import Course


def student_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a student,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: (u.is_active and u.is_student) or u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def teacher_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a teacher,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: (u.is_active and u.is_teacher) or u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def uploader_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    actual_decorator = user_passes_test(
        lambda u: (u.is_active and u.is_uploader) or u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def superuser_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a superuser,
    redirects to the log-in page if necessary.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def creator_required(view):
    """
    Decorator for views that checks that the current user has created the task
    """
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        task = get_object_or_404(Task, pk=kwargs.get("task_id"))
        if task.created_by != request.user and not request.user.is_superuser:
            action = 'edit' if request.path.__contains__('edit') else 'delete'
            messages.error(
                request,
                "You are not allowed to " + action + " this task."
            )

            next_url = request.GET.get('next')
            referer = request.headers.get('Referer')

            for url in (next_url, referer):
                if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}):
                    return redirect(url)

            return redirect("task:list")
        return view(request, *args, **kwargs)
    return _wrapped


def teacher_involved_required(view):
    """
    Decorator for views that checks that the current user is involved in the course
    """
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if kwargs.get('course_id') is None:
            return view(request, *args, **kwargs)

        course = get_object_or_404(Course, pk=kwargs.get("course_id"))

        if not course.teacher.filter(pk=request.user.pk).exists() and not request.user.is_superuser:
            action = 'edit' if request.path.__contains__('edit') or request.path.__contains__('selection') or request.path.__contains__('new1') else 'delete'
            messages.error(
                request,
                "You are not allowed to " + action + " this course."
            )

            next_url = request.GET.get('next')
            referer = request.headers.get('Referer')

            for url in (next_url, referer):
                if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}):
                    return redirect(url)

            return redirect(reverse("course:index"))
        return view(request, *args, **kwargs)
    return _wrapped
