from django.contrib import admin
from .models import Order, UserProfile


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user']


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'image']
    search_fields = ['user']


admin.site.register(Order, OrderAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
