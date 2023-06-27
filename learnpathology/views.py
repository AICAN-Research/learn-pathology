from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def index(request):
    return render(request, 'learnpathology/frontpage.html')


def test_one_column(request):
    return render(request, 'learnpathology/single_content_layout.html')


def test_two_column(request):
    return render(request, 'learnpathology/two_column_layout.html')
