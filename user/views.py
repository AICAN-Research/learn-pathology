from django.shortcuts import render


def login_feide(request):
    return render(request, 'user/feide_login.html')
