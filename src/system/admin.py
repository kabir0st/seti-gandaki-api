from django.contrib import admin
from unfold.admin import ModelAdmin

from system.models.settings import GlobalSettings

from .models import (FAQ, AuthenticationLog, Document, Inquiries, Notification,
                     UserBase, VerificationCode)


class UserBaseAdmin(ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    search_fields = ('email', 'given_name', 'family_name')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class VerificationCodeAdmin(ModelAdmin):
    list_display = [
        'code', 'email', 'is_email_sent', 'created_at', 'expiration_time'
    ]
    list_filter = ['is_email_sent', 'created_at']
    search_fields = ['email', 'code']
    readonly_fields = ['created_at', 'updated_at', 'expiration_time', 'code']
    actions = ['resend_email']

    def resend_email(self, request, queryset):
        for verification_code in queryset:
            if not verification_code.is_email_sent:
                # send_otp_email.delay(verification_code.id)
                pass
            else:
                self.message_user(
                    request,
                    "Selected verification codes have already been sent.",
                    level='warning')


class DocumentAdmin(ModelAdmin):
    list_display = ('uuid', 'name', 'model', 'status')
    search_fields = ('uuid', 'name', 'model', 'status')
    readonly_fields = ()
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class FAQAdmin(ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'answer')
    readonly_fields = ()
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class AuthenticationLogAdmin(ModelAdmin):
    list_display = ('user', 'ip', 'datetime', 'action')
    search_fields = ('user__email', 'ip', 'datetime', 'action')
    readonly_fields = ('datetime', )
    filter_horizontal = ()
    list_filter = ('action', )
    fieldsets = ()


class InquiriesAdmin(ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('created_at', )


class NotificationAdmin(ModelAdmin):
    list_display = ('user', 'msg', 'model', 'priority', 'read', 'created_at')
    search_fields = ('user__email', 'user__phone_number', 'msg', 'model')
    list_filter = ('read', 'priority', 'model', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user', )


class GlobalSettingsAdmin(ModelAdmin):
    list_display = ('business_name', 'email', 'phone', 'mobile', 'pan_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Contact Information', {
            'fields': ('email', 'phone', 'mobile', 'location')
        }),
        ('Business Settings', {
            'fields': ('shipping_charge', 'multi_vendor_support')
        }),
    )


admin.site.register(AuthenticationLog, AuthenticationLogAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(GlobalSettings, GlobalSettingsAdmin)
admin.site.register(Inquiries, InquiriesAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(UserBase, UserBaseAdmin)
admin.site.register(VerificationCode, VerificationCodeAdmin)
