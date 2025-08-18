from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user.models import User


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_teacher', 'is_uploader', 'is_teacher')
    fieldsets = (
        *UserAdmin.fieldsets,  # original form fieldsets, expanded
        (                      # new fieldset added on to the bottom
            'Learn Pathology access level',  # group heading of your choice; set to None for a blank space instead of a header
            {
                'fields': (
                    'is_student',
                    'is_teacher',
                    'is_uploader',
                ),
            },
        ),
    )

admin.site.register(User, CustomUserAdmin)