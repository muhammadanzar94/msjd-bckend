from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from core.models import TimeStampedModel


def validate_masjid_video_duration(file):
    import subprocess
    import json

    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'json', file.temporary_file_path()],
            capture_output=True, text=True, timeout=10
        )
        duration = float(json.loads(result.stdout)['format']['duration'])
    except Exception:
        raise ValidationError('Could not verify video duration. Please upload a valid video file.')

    if duration > 30:
        raise ValidationError(f'Video must be 30 seconds or less (got {duration:.1f}s).')


class Masjid(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text='Used in subdomain/URL, e.g. masjid-noor')
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    firqa = models.CharField(max_length=100, blank=True, null=True)

    google_maps_link = models.URLField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timezone = models.CharField(
        max_length=50, default='UTC',
        help_text="IANA timezone name, e.g. 'Europe/London', 'Asia/Karachi'"
    )

    logo = models.ImageField(upload_to='masjid_logos/', blank=True, null=True)
    intro_video = models.FileField(
        upload_to='masjid_videos/',
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'webm']),
            validate_masjid_video_duration,
        ],
        help_text='Optional intro video, max 30 seconds'
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return self.name


class MasjidTheme(TimeStampedModel):
    masjid = models.OneToOneField(Masjid, on_delete=models.CASCADE, related_name='theme')
    primary_color = models.CharField(max_length=7, default='#0F6B47')
    secondary_color = models.CharField(max_length=7, default='#F5A623')
    font_family = models.CharField(max_length=50, default='Inter')
    background_image = models.ImageField(upload_to='masjid_backgrounds/', blank=True, null=True)

    def __str__(self):
        return f'Theme for {self.masjid.name}'


class DonationDetail(TimeStampedModel):
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE, related_name='donation_details')
    bank_name = models.CharField(max_length=150)
    account_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=50)
    sort_code = models.CharField(max_length=20, blank=True, null=True)
    iban = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.bank_name} — {self.masjid.name}'


class MasjidImage(TimeStampedModel):
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='masjid_images/')
    order = models.PositiveSmallIntegerField(default=0, help_text='Display order (0-3)')

    class Meta:
        ordering = ['order']

    def clean(self):
        if not self.pk and self.masjid.images.count() >= 4:
            raise ValidationError('A masjid can have a maximum of 4 images.')

    def __str__(self):
        return f'{self.masjid.name} — image {self.order}'