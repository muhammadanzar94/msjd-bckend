from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    class Role(models.TextChoices):
        SYSTEM_ADMIN = 'system_admin', 'System Admin'
        MASJID_ADMIN = 'masjid_admin', 'Masjid Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MASJID_ADMIN)
    phone = models.CharField(max_length=30, blank=True)
    is_approved = models.BooleanField(
        default=False,
        help_text='Masjid admins must be approved by a system admin before they can create a masjid'
    )
    masjid = models.ForeignKey(
        'masjids.Masjid',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='admins',
        help_text='Which masjid this admin manages (blank for system admins)'
    )

    def save(self, *args, **kwargs):
        if self.role == self.Role.SYSTEM_ADMIN:
            self.is_approved = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} ({self.role})'