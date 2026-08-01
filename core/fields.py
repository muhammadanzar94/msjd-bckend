from django.conf import settings
from rest_framework import serializers


class AbsoluteFileFieldMixin:
    """Builds the absolute media URL from settings.PUBLIC_BASE_URL instead of
    the literal request Host whenever it's configured.

    Django is often called server-to-server by the Next.js frontend via
    http://127.0.0.1:8000 (both for the public site and the dashboard),
    which would otherwise leak into every image/video URL returned to the
    browser as an unreachable "http://127.0.0.1:8000/media/..." link.
    Falls back to the normal request-based behavior when PUBLIC_BASE_URL
    isn't set (e.g. local dev, where request and browser share a host).
    """

    def to_representation(self, value):
        if not value:
            return None
        url = value.url
        base = getattr(settings, 'PUBLIC_BASE_URL', '')
        if base:
            return f"{base.rstrip('/')}{url}"
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class AbsoluteImageField(AbsoluteFileFieldMixin, serializers.ImageField):
    pass


class AbsoluteFileField(AbsoluteFileFieldMixin, serializers.FileField):
    pass
