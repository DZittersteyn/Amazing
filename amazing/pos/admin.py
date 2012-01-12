from pos.models import User
from django.contrib import admin

class UserAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'adress', 'city', 'bank_account', 'email', 'barcode', 'isAdmin')

admin.site.register(User, UserAdmin)
