import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

# Import all models from the statements app
from statements.models.business import Business
from statements.models.logistics import GatePass, GatePassMovement, TripLog
from statements.models.purchase_invoice import (Vehicle, PurchaseBill,
                                                PurchaseItem)
from statements.models.sales_invoice import SalesInvoice, SalesInvoiceLineItem
from statements.models.support import Staff
from django.contrib.auth import get_user_model

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

            pb = PurchaseBill.objects.create(
                purchase_date=bill_date,
                from_business=from_business_instance,
                purchase_bill_number=
                f'PB-{fake.unique.ean(length=8)}-{bill_date.year}',  # noqa
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
        gate_passes = []
        for _ in range(25):
            vehicle_instance = random.choice(vehicles) if vehicles else None
            issued_at = fake.date_time_this_year(
                tzinfo=timezone.get_current_timezone())

            gp = GatePass.objects.create(
                vehicle=vehicle_instance,
                license_plate=vehicle_instance.license_plate
                if vehicle_instance else fake.license_plate(),
                purpose=fake.sentence(nb_words=10),
                driver_name=fake.name() if not vehicle_instance
                or not vehicle_instance.primary_staffs.exists() else
                random.choice(vehicle_instance.primary_staffs.all()).name,
                driver_phone=fake.phone_number(),
                remarks=fake.sentence()
                if random.choice([True, False]) else '',
                issued_by=default_user,  # Assign superuser or first user
                created_at=issued_at)
            gate_passes.append(gp)

            # Create GatePassMovements
            num_movements = random.randint(
                1, 3)  # 1 to 3 pairs of exit/entry or single
            last_time = issued_at
            for i in range(num_movements):
                # First movement: exit (company vehicle) or entry (external).
                # Simplified: alternate or random.
                is_exit_first = fake.boolean(
                ) if i == 0 else False  # Simplified logic

                exit_t = None
                entry_t = None

                if is_exit_first or (i > 0 and gp.movements.last()
                                     and gp.movements.last().entry_time
                                     ):  # If last was entry, next is exit
                    exit_t = fake.date_time_between(
                        start_date=last_time,
                        end_date=last_time +
                        timezone.timedelta(hours=random.randint(1, 5)),
                        tzinfo=timezone.get_current_timezone())
                    last_time = exit_t
                    entry_t = fake.date_time_between(
                        start_date=last_time,
                        end_date=last_time +
                        timezone.timedelta(hours=random.randint(1, 8)),
                        tzinfo=timezone.get_current_timezone(
                        )) if fake.boolean(chance_of_getting_true=70) else None
                    if entry_t:
                        last_time = entry_t
                else:  # First is entry or last was exit
                    entry_t = fake.date_time_between(
                        start_date=last_time,
                        end_date=last_time +
                        timezone.timedelta(hours=random.randint(1, 5)),
                        tzinfo=timezone.get_current_timezone())
                    last_time = entry_t
                    exit_t = fake.date_time_between(
                        start_date=last_time,
                        end_date=last_time +
                        timezone.timedelta(hours=random.randint(1, 8)),
                        tzinfo=timezone.get_current_timezone(
                        )) if fake.boolean(chance_of_getting_true=70) else None
                    if exit_t:
                        last_time = exit_t

                # Only create if at least one time is set
                if exit_t or entry_t:
                    GatePassMovement.objects.create(gate_pass=gp,
                                                    exit_time=exit_t,
                                                    entry_time=entry_t)
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {len(gate_passes)} gate passes with movements.'))

        # 6. TripLog
        self.stdout.write(self.style.HTTP_INFO('Seeding Trip Logs...'))
        trip_logs = []
        # Ensure gate passes and purchase bills exist to link
        if gate_passes and purchase_bills:
            for _ in range(15):
                gate_pass_instance = random.choice(gate_passes)
                # Ensure gate pass has a vehicle for TripLog's __str__
                if not gate_pass_instance.vehicle:
                    if vehicles:
                        gate_pass_instance.vehicle = random.choice(vehicles)
                        gate_pass_instance.save()
                    else:  # Cannot create TripLog if no vehicle assigned
                        continue

                trip_log = TripLog.objects.create(
                    gate_pass=gate_pass_instance,
                    for_purchase_bill=random.choice(purchase_bills)
                    if purchase_bills
                    and fake.boolean(chance_of_getting_true=50) else None,
                    purpose=fake.sentence(nb_words=8),
                    notes=fake.paragraph(nb_sentences=2)
                    if random.choice([True, False]) else '')
                trip_logs.append(trip_log)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {len(trip_logs)} trip logs.'))

        # 7. SalesInvoice and SalesInvoiceLineItem
        self.stdout.write(
            self.style.HTTP_INFO('Seeding Sales Invoices and Line Items...'))
        sales_invoices = []
        for _ in range(20):
            business_instance = random.choice(
                businesses) if businesses else None
            if not business_instance:
                continue  # Cannot create SalesInvoice without a business

            invoice_d = fake.date_this_year()
            # subtotal_val = Decimal(0)  # Unused: Calc from line items

            si = SalesInvoice.objects.create(
                invoice_number=
                f'INV-{fake.unique.ean(length=8)}-{invoice_d.year}',  # noqa
                invoice_date=invoice_d,
                business=business_instance,
                sales_order_number=f'SO-{fake.ean(length=8)}'
                if fake.boolean() else None,
                subtotal=Decimal('0.00'),  # Placeholder, will be updated
                discounts=Decimal(random.uniform(0, 200)).quantize(
                    Decimal('0.01')),
                taxes=Decimal(random.uniform(0, 100)).quantize(
                    Decimal('0.01')),  # Simplified tax
                shipping_delivery=Decimal(random.uniform(0, 150)).quantize(
                    Decimal('0.01')),
                total_amount_due=Decimal(
                    '0.00'),  # Placeholder, will be updated
                payment_terms=random.choice(
                    ['Net 30', 'Net 60', 'Due on Receipt']),
                notes=fake.sentence() if fake.boolean() else '')

            current_invoice_subtotal = Decimal(0)
            for _ in range(random.randint(1, 4)):
                qty = Decimal(random.uniform(1, 50)).quantize(Decimal('0.01'))
                price = Decimal(random.uniform(20,
                                               1000)).quantize(Decimal('0.01'))
                line_total = (qty * price).quantize(Decimal('0.01'))
                current_invoice_subtotal += line_total
                SalesInvoiceLineItem.objects.create(
                    invoice=si,
                    item_description=fake.bs().title(),
                    quantity=qty,
                    unit_of_measurement=random.choice(
                        ['unit', 'set', 'hour', 'service']),
                    unit_price=price,
                    line_item_total=line_total)

            si.subtotal = current_invoice_subtotal.quantize(Decimal('0.01'))
            si.total_amount_due = (si.subtotal - si.discounts + si.taxes +
                                   si.shipping_delivery).quantize(
                                       Decimal('0.01'))
            # Ensure total_amount_due is not negative
            if si.total_amount_due < 0:
                si.total_amount_due = Decimal('0.00')

            si.save()
            sales_invoices.append(si)
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {len(sales_invoices)} sales invoices with items.'))

        self.stdout.write(
            self.style.SUCCESS(
                'Database seeding for statements app completed successfully!'))
