from django.contrib import admin
from .models import Order, UserProfile, Items


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user']


class ItemsAdmin(admin.ModelAdmin):
    list_display = ['order', 'item_name', 'quantity', 'price']
    list_filter = ['item_name', 'price']
    search_fields = ['item_name']


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'image']
    search_fields = ['user']


admin.site.register(Order, OrderAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Items, ItemsAdmin)
