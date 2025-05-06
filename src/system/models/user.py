import random
import uuid

from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.cache import cache
from django.core.validators import validate_image_file_extension
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils import timezone

from core.utils.functions import limit_size


class UserbaseManager(BaseUserManager):

    def create_superuser(self, phone_number, password, **other_fields):
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)
        return self.create_user(phone_number, password, **other_fields)

    def create_user(self, phone_number, password, **other_fields):
        other_fields.setdefault("is_superuser", False)
        if not phone_number:
            raise ValueError("You must provide an phone_number")
        user = self.model(phone_number=phone_number, **other_fields)
        user.set_password(password)
        user.save()
        return user


def image_path_item(instance, filename):
    return f'users/{instance.uuid}/ct_{filename}'


def profile_image_path(instance, filename):
    return f'users/{instance.uuid}/pf_{filename}'


def image_path_item_2(instance, filename):
    return f'users/{instance.uuid}/vt_{filename}'


class UserBase(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    added_by = models.ForeignKey('UserBase',
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True)
    phone_number = models.CharField(unique=True, max_length=30)

    email = models.EmailField(unique=True, null=True, blank=True)

    given_name = models.CharField(max_length=255, default='')
    family_name = models.CharField(max_length=255, default='')

    profile_image = models.ImageField(
        upload_to=profile_image_path,
        null=True,
        blank=True,
        validators=[limit_size, validate_image_file_extension])

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=True)
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []
    objects = UserbaseManager()

    def __str__(self):
        return f'{self.full_name}'

    @property
    def retrieve_url(self):
        return f'/users/{self.uuid}/'

    @property
    def full_name(self):
        return f'{self.given_name} {self.family_name}'

    def update_cache(self, access_token):
        remaining_time = cache.ttl(access_token)
        cache.set(access_token, self, remaining_time)
        refresh = cache.get(f'refresh_{access_token}')
        remaining_time = cache.ttl(f'refresh_{access_token}')
        cache.set(refresh, self, remaining_time)


class VerificationCode(models.Model):
    code = models.CharField(null=True,
                            blank=True,
                            max_length=6,
                            editable=False)
    email = models.EmailField()
    is_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiration_time = models.DateTimeField(null=True, blank=True)
    otp_for = models.CharField(max_length=255, default='email_verification')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', 'email'],
                                    name='verification_unique_constraints')
        ]

    def has_expire(self):
        return self.expiration_time and self.expiration_time < timezone.now()

    def check_code(self, code):
        if self.expiration_time and self.expiration_time < timezone.now():
            return False, 'Code has already expired.'
        if self.code == str(code):
            return True, None
        return False, 'Invalid verification code.'

    @classmethod
    def generate(cls, email, otp_for):
        old_codes = cls.objects.filter(email=email, otp_for=otp_for)
        if old_codes:
            for old_code in old_codes:
                if not old_code.has_expire():
                    raise ValidationError(
                        'Last verification code has not expired yet.')
                old_codes.delete()
        verification_code = cls(email=email, otp_for=otp_for)
        verification_code.expiration_time = timezone.now(
        ) + timezone.timedelta(minutes=5)
        verification_code.save()
        return verification_code


@receiver(pre_save, sender=VerificationCode)
def pre_save_verification_code(sender, instance, *args, **kwargs):
    if not instance.code:
        instance.code = str(random.randint(111111, 999999))


@receiver(post_save, sender=VerificationCode)
def post_save_handler_verification_code(sender, instance, created, **kwargs):
    if not instance.is_email_sent:
        pass
        # send_emails('password_reset.html', [instance.email],
        #  'Password Reset.',
        #             {'code': instance.code}, {
        #                 'model': 'system.VerificationCode',
        #                 'id': instance.id
        #             })
