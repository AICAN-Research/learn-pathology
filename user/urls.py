from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', auth_views.logout_then_login, name='logout'),
    path('login/feide/', views.login_feide, name='login_feide')
]