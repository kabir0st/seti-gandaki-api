import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

# Import all models from the statements app
from statements.models.business import Business
from statements.models.purchase_invoice import (PurchaseBill, PurchaseItem,
                                                Vehicle)
from statements.models.support import Staff

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds data for the statements app using Faker.'

    def handle(self, *args, **options):
        fake = Faker()
        self.stdout.write(
            self.style.SUCCESS(
                'Starting database seeding for statements app...'))

        # Ensure a superuser exists for 'issued_by' or other FKs.
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING(
                    'No superuser found. Please create a superuser first.'))
            # Optionally, create one here if desired, or just return
            # User.objects.create_superuser('admin', 'admin@example.com',
            #                                'password')
            # self.stdout.write(self.style.SUCCESS('Default superuser created.')) # noqa
            # Warn and proceed; some FKs might fail if they require a user
            # and allow null=False / blank=False
            pass

        # Get or create a default user for FK relations if needed
        # Placeholder: Adjust per your User model and requirements.
        default_user = User.objects.filter(is_superuser=True).first()
        if not default_user and User.objects.exists():
            default_user = User.objects.first()

        # Seeding order matters due to ForeignKeys

        # 1. Staff
        self.stdout.write(self.style.HTTP_INFO('Seeding Staff...'))
        staff_members = []
        for _ in range(10):
            staff = Staff.objects.create(
                name=fake.name(),
                phone_number=fake.phone_number(),  # Corrected from email
                pan=fake.unique.bothify(
                    text='?????####?').upper(),  # Example PAN
                assigned_salary=Decimal(random.uniform(30000,
                                                       120000)).quantize(
                                                           Decimal('0.01')),
                address=fake.address())
            staff_members.append(staff)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {len(staff_members)} staff members.'))

        # 2. Business
        self.stdout.write(self.style.HTTP_INFO('Seeding Businesses...'))
        businesses = []
        for _ in range(15):
            business = Business.objects.create(
                name=fake.company(),
                registration_number=fake.unique.ean(length=13),
                contact_person=fake.name(),
                contact_email=fake.email(),
                phone_number=fake.phone_number(),
                address=fake.address(),
                is_active=fake.boolean(chance_of_getting_true=90))
            businesses.append(business)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {len(businesses)} businesses.'))

        # 3. Vehicle
        self.stdout.write(self.style.HTTP_INFO('Seeding Vehicles...'))
        vehicles = []
        for _ in range(20):
            vehicle = Vehicle.objects.create(
                license_plate=fake.unique.license_plate(),
                vehicle_type=random.choice(
                    ['Truck', 'Van', 'Car', 'Motorcycle']),
                note=fake.sentence(),
                is_active=fake.boolean(chance_of_getting_true=95))
            # Assign some primary staff to vehicles
            if staff_members:
                vehicle.primary_staffs.set(
                    random.sample(staff_members,
                                  k=min(len(staff_members),
                                        random.randint(1, 2))))
            vehicles.append(vehicle)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {len(vehicles)} vehicles.'))

        # 4. PurchaseBill and PurchaseItem
        self.stdout.write(
            self.style.HTTP_INFO('Seeding Purchase Bills and Items...'))
        purchase_bills = []
        for i in range(30):
            from_business_instance = random.choice(
                businesses) if businesses else None
            bill_date = fake.date_between(start_date='-2y', end_date='today')
            bill_number = f'PB-{fake.unique.ean(length=8)}-{bill_date.year}'
            pb = PurchaseBill.objects.create(
                purchase_date=bill_date,
                from_business=from_business_instance,
                purchase_bill_number=bill_number,
                grace_discount=Decimal(random.uniform(0, 500)).quantize(
                    Decimal('0.01')),
                shipping_and_handling_costs=Decimal(random.uniform(
                    0, 1000)).quantize(Decimal('0.01')),
                additional_costs=Decimal(random.uniform(0, 300)).quantize(
                    Decimal('0.01')),
                additional_costs_remarks=fake.sentence()
                if random.choice([True, False]) else '',
                paid_amount=Decimal(0),  # Will be updated by items
                status=random.choice(
                    [s[0] for s in PurchaseBill.STATUS_CHOICES]),
                notes=fake.paragraph(
                    nb_sentences=3) if random.choice([True, False]) else '',
                bill_started_from=bill_date,
                bill_completed_on=fake.date_between(start_date=bill_date,
                                                    end_date='today')
                if random.choice([True, False]) else None,
            )
            if vehicles:
                pb.assigned_vehicles.set(
                    random.sample(vehicles,
                                  k=min(len(vehicles), random.randint(0, 2))))
            if staff_members:
                pb.assigned_staffs.set(
                    random.sample(staff_members,
                                  k=min(len(staff_members),
                                        random.randint(0, 3))))

            # Create PurchaseItems for this bill
            # total_bill_sub_total_for_pb = Decimal(0) # Unused
            # total_bill_amount_for_pb = Decimal(0) # Unused

            for _ in range(random.randint(1, 5)):
                quantity = Decimal(random.uniform(1, 100)).quantize(
                    Decimal('0.01'))
                unit_price = Decimal(random.uniform(10, 500)).quantize(
                    Decimal('0.01'))
                discount_percentage = Decimal(random.uniform(0, 25)).quantize(
                    Decimal('0.01'))
                tax_percent_applied = Decimal(random.choice(
                    [0, 5, 10, 13])).quantize(Decimal('0.01'))

                # Calc as per PurchaseItem pre_save (simplified direct create)
                sub_total = quantity * unit_price
                bill_amount_item = sub_total * (1 - discount_percentage / 100)
                taxable_amount_item = Decimal(0)
                tax_amount_item = Decimal(0)
                if tax_percent_applied > 0:
                    taxable_amount_item = bill_amount_item
                    tax_amount_item = taxable_amount_item * (
                        tax_percent_applied / 100)
                    bill_amount_item += tax_amount_item

                PurchaseItem.objects.create(
                    purchase_bill=pb,
                    item=fake.word().capitalize() + " " + fake.word(),
                    item_description=fake.sentence(nb_words=6),
                    quantity=quantity,
                    unit_of_measurement=random.choice(
                        ['kg', 'ltr', 'pcs', 'meter', 'cubic meter']),
                    unit_price=unit_price,
                    sub_total=sub_total.quantize(Decimal('0.01')),
                    discount_percentage=discount_percentage,
                    taxable_amount=taxable_amount_item.quantize(
                        Decimal('0.01')),
                    tax_percent_applied=tax_percent_applied,
                    tax_amount=tax_amount_item.quantize(Decimal('0.01')),
                    bill_amount=bill_amount_item.quantize(Decimal('0.01')))
            # `update_purchase_bill_totals` signal handles pb.sub_total and
            # pb.bill_amount. Refresh and set paid_amount if needed.
            pb.refresh_from_db()
            pb.paid_amount = pb.bill_amount * Decimal(random.uniform(
                0.5, 1)) if pb.status == 'complete' else Decimal(0)
            pb.save(update_fields=['paid_amount'])
            purchase_bills.append(pb)
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {len(purchase_bills)} purchase bills with items.'))

        # 5. GatePass and GatePassMovement
        self.stdout.write(
            self.style.HTTP_INFO('Seeding Gate Passes and Movements...'))

        self.stdout.write(
            self.style.SUCCESS(
                'Database seeding for statements app completed successfully!'))
