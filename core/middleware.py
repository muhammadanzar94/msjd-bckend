from django.conf import settings


class TenantMiddleware:
    """Resolves the masjid tenant from the request's subdomain
    (e.g. masjid-noor.localhost -> slug 'masjid-noor') and attaches
    it to the request as `request.masjid` (None if there is no
    subdomain or no masjid matches it).

    Also accepts an explicit `X-Masjid-Slug` header as a fallback: a
    server-to-server caller (e.g. the Next.js frontend) can't override the
    `Host` header — browsers and Node's fetch both forbid it — so it sends
    the slug this way instead. Real browser traffic keeps using the
    subdomain, which is why this only kicks in when no subdomain matched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.masjid = self._resolve_masjid(request)
        return self.get_response(request)

    def _resolve_masjid(self, request):
        from masjids.models import Masjid

        subdomain = self._subdomain_slug(request)
        slug = subdomain or request.headers.get('X-Masjid-Slug')
        if not slug:
            return None

        return Masjid.objects.filter(slug=slug).first()

    def _subdomain_slug(self, request):
        host = request.get_host().split(':')[0]
        base_domain = settings.BASE_DOMAIN

        if host == base_domain or not host.endswith(f'.{base_domain}'):
            return None

        subdomain = host[: -len(f'.{base_domain}')]
        if subdomain in ('', 'www'):
            return None

        return subdomain
