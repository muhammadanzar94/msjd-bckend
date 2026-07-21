from django.contrib import admin
from .models import Masjid, MasjidTheme, DonationDetail, MasjidImage


class MasjidThemeInline(admin.StackedInline):
    model = MasjidTheme
    can_delete = False


class DonationDetailInline(admin.TabularInline):
    model = DonationDetail
    extra = 1


class MasjidImageInline(admin.TabularInline):
    model = MasjidImage
    extra = 1
    max_num = 4


@admin.register(Masjid)
class MasjidAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'city', 'country', 'status', 'created_at')
    list_filter = ('status', 'country', 'city')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MasjidThemeInline, DonationDetailInline, MasjidImageInline]
    actions = ['approve_masjids', 'reject_masjids']

    def approve_masjids(self, request, queryset):
        queryset.update(status=Masjid.Status.APPROVED)
    approve_masjids.short_description = 'Approve selected masjids'

    def reject_masjids(self, request, queryset):
        queryset.update(status=Masjid.Status.REJECTED)
    reject_masjids.short_description = 'Reject selected masjids'