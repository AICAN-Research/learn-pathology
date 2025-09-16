from datetime import timedelta
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from user.models import User
from slide.models import Slide


def index(request):
    context = {}
    if request.user.is_superuser or request.user.is_teacher:
        # Count number of online users, using the User.last_seen field
        context['active_users'] = User.objects.filter(
            last_seen__gt=timezone.now() - timedelta(minutes=settings.LAST_SEEN_TIMEOUT)).count()
        if settings.USE_FEIDE_LOGIN:
            from allauth.socialaccount.models import SocialAccount
            # Check if user is FEIDE user, if so no need to check for password reset
            context['feide_users'] = SocialAccount.objects.all().count()
            context['users'] = User.objects.exclude(username__in=SocialAccount.objects.values('user__username')).count()
        else:
            context['users'] = User.objects.all().count()
        context['images'] = Slide.objects.all().count()
    return render(request, 'learnpathology/frontpage.html', context)


def test_one_column(request):
    return render(request, 'learnpathology/single_content_layout.html')


def test_two_column(request):
    return render(request, 'learnpathology/two_column_layout.html')


def test_one_column(request):
    return render(request, 'learnpathology/single_content_layout.html')


def test_two_column(request):
    return render(request, 'learnpathology/two_column_layout.html')


def privacy_info(request):
    return render(request, 'learnpathology/privacy_info.html')