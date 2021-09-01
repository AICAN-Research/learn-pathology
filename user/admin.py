from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user.models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        *UserAdmin.fieldsets,  # original form fieldsets, expanded
        (                      # new fieldset added on to the bottom
            'Learn Pathology access level',  # group heading of your choice; set to None for a blank space instead of a header
            {
                'fields': (
                    'is_student',
                    'is_teacher',
                ),
            },
        ),
    )

admin.site.register(User, CustomUserAdmin)