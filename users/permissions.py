from rest_framework import permissions


class IsSystemAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'system_admin'
        )


class IsMasjidAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'masjid_admin'
            and request.user.is_approved
        )


class IsSystemAdminOrOwnMasjidAdmin(permissions.BasePermission):
    """System admins can touch anything. Masjid admins can only
    touch objects belonging to their own masjid."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'system_admin' or request.user.is_approved)
        )

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'system_admin':
            return True
        # obj can be a Masjid itself, or anything with a `masjid` FK
        target_masjid = obj if obj.__class__.__name__ == 'Masjid' else getattr(obj, 'masjid', None)
        return target_masjid is not None and target_masjid_id_matches(request.user, target_masjid)


def target_masjid_id_matches(user, masjid):
    return user.masjid_id == masjid.id