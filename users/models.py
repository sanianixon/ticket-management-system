from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("DEVELOPER", "Developer"),
        ("TESTER", "Tester"),
        ("USER", "User"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="USER"
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} - {self.role}"