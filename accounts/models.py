from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CITIZEN = 'citizen'
    ROLE_SUPERADMIN = 'superadmin'
    ROLE_CHOICES = [
        (ROLE_CITIZEN, 'Citoyen'),
        (ROLE_SUPERADMIN, 'Super Administrateur'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default=ROLE_CITIZEN)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def has_role(self, role):
        return self.role == role

    @property
    def is_admin(self):
        return self.role == self.ROLE_SUPERADMIN

    @property
    def is_superadmin(self):
        return self.role == self.ROLE_SUPERADMIN

    def save(self, *args, **kwargs):
        # Synchronise les flags Django natifs
        self.is_staff = self.is_admin
        self.is_superuser = self.is_superadmin
        self.email = self.email.lower()
        super().save(*args, **kwargs)

