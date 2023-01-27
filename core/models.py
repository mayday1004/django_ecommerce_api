from django.db import models
from django.contrib.auth.models import UserManager, AbstractUser
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class CustomUserManager(UserManager):
    def create_user(self, username, email, password, **extra_fields):
        if not extra_fields.get("phone_number"):
            raise ValueError(_("Please enter a phone number"))
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        if not extra_fields.get("phone_number"):
            raise ValueError(_("Please enter a phone number"))
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(_("Phone"), unique=True, null=False, blank=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "phone_number", "first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.username
