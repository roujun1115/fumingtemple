from django.contrib import admin
from .models import Committee, Andou, Light, Donation

@admin.register(Andou)
class AndouAdmin(admin.ModelAdmin):
    list_display = ('year', 'item', 'name', 'payment_status')
    list_filter = ('year', 'payment_status')
    search_fields = ('name',)

admin.site.register(Committee)
admin.site.register(Light)
admin.site.register(Donation)