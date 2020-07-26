from django.contrib import admin
from . import models


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted',
                    'billing_address',
                    'shipping_address',
                    'payment',
                    'coupon'
                    ]
    list_display_links = ['user', 'billing_address',
                          'shipping_address',
                          'payment',
                          'coupon']
    list_filter = ['being_delivered',
                   'received',
                   'refund_requested',
                   'refund_granted']
    search_fields = ['user__username', 'ref_code']

    actions = [make_refund_accepted]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'country',
        'apartment_address',
        'zip_code',
        'address_type',
        'default',
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip_code']


admin.site.register(models.Item)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.OrderItem)
admin.site.register(models.Payment)
admin.site.register(models.Coupon)
admin.site.register(models.Refund)
admin.site.register(models.Address, AddressAdmin)
