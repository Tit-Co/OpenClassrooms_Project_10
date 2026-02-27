from django.contrib import admin
from accounts.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'username',
                    'is_staff',
                    'is_active',
                    'age',
                    'can_be_contacted',
                    'can_data_be_shared')


admin.site.register(User, UserAdmin)
