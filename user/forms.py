from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from user.models import User


class AddNewUserForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


if settings.USE_FEIDE_LOGIN:
    from feide.models import ApprovedUser

    class ApproveFeideUserForm(forms.ModelForm):
        class Meta:
            model = ApprovedUser
            fields = ('username',)
            field_classes = {'username': forms.EmailField}
