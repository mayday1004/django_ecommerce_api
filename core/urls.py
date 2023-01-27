from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.UserCreated.as_view(), name="sign_up"),
    path("user/me/", views.UserMe.as_view(), name="user_me"),
]
