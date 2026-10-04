from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class UserManager(BaseUserManager):
    """Manager for an email-identified user model (no usernames)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.USER)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superusers must have is_staff=True and is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


phone_validator = RegexValidator(
    regex=r"^\+?[0-9][0-9\s-]{6,18}[0-9]$",
    message="Enter a valid phone number (digits, spaces, dashes, optional leading +).",
)


class User(AbstractUser):
    """Platform user. Email is the login identifier; passwords are hashed by
    Django's configured password hasher and never stored in plaintext."""

    class Role(models.TextChoices):
        USER = "USER", "User"
        ADMIN = "ADMIN", "Admin"

    username = None
    email = models.EmailField("email address", unique=True)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def is_platform_admin(self) -> bool:
        return self.is_active and (self.role == self.Role.ADMIN or self.is_superuser)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
