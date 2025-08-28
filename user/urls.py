from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='reset_password'),
    path('password/done/', views.password_change_done, name='password_change_done'),
    path('logout/', auth_views.logout_then_login, name='logout'),
    path('login/feide/', views.login_feide, name='login_feide'),
    path('new/', views.create_new_user, name='create_new_user'),
    path('approve/', views.approve_feide_user, name='approve_feide_user'),
    path('admin/', views.admin, name='user_admin'),
]