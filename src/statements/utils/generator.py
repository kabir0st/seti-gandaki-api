from bikram import samwat

from django.apps import apps

from statements.models.settings import StatementSettings


def get_fiscal_year(invoiced_date):
    start_fiscal_year = 0
    end_fiscal_year = 0
    settings = StatementSettings.load()
    nepali_date = samwat.from_ad(invoiced_date.date())
    invoice_month_day = nepali_date.strftime("%m-%d")

    fiscal_change_month_day = (
        f"{settings.fiscal_year_change_month_in_bs:02d}-"
        f"{settings.fiscal_year_change_day_in_bs:02d}")
    if invoice_month_day < fiscal_change_month_day:
        start_fiscal_year = int(invoiced_date.year) - 1
        end_fiscal_year = int(invoiced_date.year)
        nepali_start = int(nepali_date.year) - 1
        nepali_end = int(nepali_date.year)
    else:
        start_fiscal_year = int(invoiced_date.year)
        end_fiscal_year = int(invoiced_date.year) + 1
        nepali_start = int(nepali_date.year)
        nepali_end = int(nepali_date.year) + 1

    dates = {
        'bs': str(nepali_start)[2:] + "-" + str(nepali_end)[2:],
        'ad': str(start_fiscal_year)[2:] + "-" + str(end_fiscal_year)[2:],
        'ird_fy': str(nepali_start) + '.' + str(nepali_end)[1:]
    }
    return dates


def get_missing_serial(years):
    Invoice = apps.get_model('statements.Invoice')
    invoice_serials = Invoice.objects.filter(
        fiscal_year_bs=years['bs']).order_by('serial').values_list('serial',
                                                                   flat=True)
    bill_serials = Invoice.objects.filter(
        fiscal_year_bs=years['bs']).order_by('serial').values_list('serial',
                                                                   flat=True)
    max_serial = max(max(invoice_serials), max(bill_serials))
    all_serials = set(range(1, max_serial + 1))
    missing_invoice_serials = all_serials.difference(invoice_serials)
    missing_bill_serials = all_serials.difference(bill_serials)
    intersection_set = set(missing_invoice_serials) & set(missing_bill_serials)
    missing = sorted(list(intersection_set))
    if missing:
        return missing[0]
    return None


def generate_invoice_number(invoice, is_taxable):
    years = get_fiscal_year(invoice.invoiced_on)
    serial = None
    Invoice = apps.get_model('statements.Invoice')
    latest = Invoice.objects.filter(
        fiscal_year_bs=years['bs'],
        is_taxable=is_taxable).order_by('-serial').first()
    if latest:
        serial = latest.serial
        serial = serial + 1
    else:
        serial = 1
    invoice_number = "INV" + \
        str(serial).zfill(6) + "-" + years['bs']
    if is_taxable:
        invoice_number = "TAX-" + invoice_number
    else:
        invoice_number = "NT-" + invoice_number
    return ([invoice_number, years, str(serial).zfill(6)])
