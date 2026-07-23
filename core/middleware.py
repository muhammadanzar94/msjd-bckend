from django.conf import settings


class TenantMiddleware:
    """Resolves the masjid tenant from the request's subdomain
    (e.g. masjid-noor.localhost -> slug 'masjid-noor') and attaches
    it to the request as `request.masjid` (None if there is no
    subdomain or no masjid matches it).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.masjid = self._resolve_masjid(request)
        return self.get_response(request)

    def _resolve_masjid(self, request):
        host = request.get_host().split(':')[0]
        base_domain = settings.BASE_DOMAIN

        if host == base_domain or not host.endswith(f'.{base_domain}'):
            return None

        subdomain = host[: -len(f'.{base_domain}')]
        if subdomain in ('', 'www'):
            return None

        from masjids.models import Masjid
        return Masjid.objects.filter(slug=subdomain).first()
