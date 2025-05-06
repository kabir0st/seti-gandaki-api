from django.core.management.base import BaseCommand
from django.db import transaction

from system.models.settings import GlobalSettings
from system.models.user import UserBase


class Command(BaseCommand):
    help = 'Populating Admin, Buyers, and Sellers'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting user population'))

        # Create or update admin
        with transaction.atomic():
            # First check by phone number
            admin = UserBase.objects.filter(phone_number="9876543210").first()

            if admin:
                admin.email = "admin@admin.com"
                admin.is_staff = True
                admin.is_superuser = True
                admin.given_name = "Admin"
                admin.family_name = "Dai"
                admin.pan_number = '1'
                admin.set_password('pass')
                admin.save()
                self.stdout.write(self.style.SUCCESS('Admin updated'))
            else:
                # Then check by email as fallback
                admin = UserBase.objects.filter(
                    email="admin@admin.com").first()
                if admin:
                    admin.phone_number = "9876543210"
                    admin.is_staff = True
                    admin.is_superuser = True
                    admin.given_name = "Admin"
                    admin.family_name = "Dai"
                    admin.set_password('pass')
                    admin.save()
                    self.stdout.write(self.style.SUCCESS('Admin updated'))
                else:
                    admin = UserBase.objects.create_superuser(
                        phone_number="9876543210", password='pass')
                    admin.email = "admin@admin.com"
                    admin.given_name = "Admin"
                    admin.family_name = "Dai"
                    admin.is_staff = True
                    admin.save()
                    self.stdout.write(self.style.SUCCESS('Admin created'))

            # Create GlobalSettings if not exists
            if not GlobalSettings.objects.exists():
                GlobalSettings.objects.create()
                self.stdout.write(
                    self.style.SUCCESS('Global settings created'))

        self.stdout.write(self.style.SUCCESS('Completed! Total users:'))
