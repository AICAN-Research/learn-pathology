from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, LoginView
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from learnpathology import settings
from user.decorators import superuser_required
from user.forms import AddNewUserForm


class CustomLoginView(LoginView):
    template_name = 'user/login.html'

    def form_valid(self, form):
        user = form.get_user()
        print('in user view', user.last_login)
        if user.need_password_reset:
            # Need to reset password
            messages.error(self.request, 'You have a temporary password, please set your own password and keep it secret.')
            super().form_valid(form)
            return redirect('reset_password')

        return super().form_valid(form)


def login_feide(request):
    return render(request, 'user/feide_login.html')


@superuser_required
def admin(request):
    return render(request, 'user/admin.html', {'USE_FEIDE_LOGIN': settings.USE_FEIDE_LOGIN})


@superuser_required
def create_new_user(request):
    if request.method == 'POST':
        form = AddNewUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.need_password_reset = True
            user.save()
            messages.success(request, f'User {user.username} was added and can now login.')
            return redirect('user_admin')
    else:
        form = AddNewUserForm()
    return render(request, 'user/new_user.html', {'form': form})


class CustomPasswordResetView(PasswordChangeView):
    template_name = 'user/password_reset.html'

    def dispatch(self, request, *args, **kwargs):
        # Check that user is not feide user
        if settings.USE_FEIDE_LOGIN:
            from allauth.socialaccount.models import SocialAccount
            if SocialAccount.objects.filter(user=request.user).count() > 0:
                return HttpResponseForbidden("Feide users cannot change their password here.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def password_change_done(request):
    messages.success(request, 'Your password was changed.')
    user = request.user
    user.need_password_reset = False
    user.save()
    return redirect('frontpage')


@superuser_required
def approve_feide_user(request):
    if settings.USE_FEIDE_LOGIN:
        from .forms import ApproveFeideUserForm
        if request.method == 'POST':
            form = ApproveFeideUserForm(request.POST)
            if form.is_valid():
                user = form.save()
                messages.success(request, f'Feide user {user.username} was added and can now login.')
                return redirect('user_admin')
        else:
            form = ApproveFeideUserForm()
        return render(request, 'user/approve_feide_user.html', {'form': form})