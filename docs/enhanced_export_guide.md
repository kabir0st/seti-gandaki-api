# Enhanced Global Export Functionality

This document describes the improved global export functionality that provides human-readable Excel exports with intelligent field handling and relationship support.

## Overview

The enhanced export system automatically:
- Converts field names to human-readable headers
- Excludes non-human-readable fields (passwords, tokens, binary data, etc.)
- Formats data appropriately (dates, booleans, choices)
- Handles relationships intelligently
- Applies professional Excel styling

## Key Functions

### 1. `global_model_export()` - Main Export Function

Use this function anywhere in your codebase to export model data to Excel.

```python
from core.utils.functions import global_model_export

# Basic usage - export all active businesses
excel_file = global_model_export(
    'statements.Business',
    filters={'is_active': True},
    document_name='Active_Businesses'
)

# Advanced usage with custom queryset
from statements.models import Business
businesses = Business.objects.filter(name__icontains='tech')
excel_file = global_model_export(
    Business,
    queryset=businesses,
    exclude_fields=['registration_number'],
    include_relations=['contact_person'],
    document_name='Tech_Companies'
)
```

**Parameters:**
- `model_class_or_string`: Django model class or string like 'app.ModelName'
- `queryset`: Optional queryset to export (defaults to all objects)
- `exclude_fields`: List of field names to exclude
- `include_relations`: List of relationship fields to include
- `document_name`: Custom Excel file name
- `human_readable_headers`: Convert field names to Title Case (default: True)
- `auto_exclude_non_human_fields`: Auto-exclude technical fields (default: True)
- `filters`: Dictionary of filters to apply

### 2. `export_data_from_response()` - Export API Response Data

Export data from API responses, dictionaries, or lists.

```python
from core.utils.functions import export_data_from_response

# Export API response data
data = [
    {'user_name': 'John', 'email': 'john@example.com', 'is_active': True},
    {'user_name': 'Jane', 'email': 'jane@example.com', 'is_active': False}
]

excel_file = export_data_from_response(
    data,
    document_name='User_Report',
    human_readable_headers=True
)
```

## ViewSet Integration

The `DefaultViewSet` export endpoint now supports enhanced parameters:

```
GET /api/model/export/?human_readable_headers=true&auto_exclude_non_human_fields=true
```

**URL Parameters:**
- `human_readable_headers`: Enable/disable human-readable headers (default: true)
- `auto_exclude_non_human_fields`: Auto-exclude technical fields (default: true)
- `exclude`: Comma-separated list of fields to exclude
- `include_relations`: Comma-separated list of relationships to include
- `document_name`: Custom document name
- `start`: Starting index for pagination
- `end`: Ending index for pagination

## Field Processing

### Human-Readable Headers

Field names are automatically converted:
- `user_name` → "User Name"
- `email_address` → "Email Address"
- `is_active` → "Is Active"
- `created_at` → "Created At"

Common abbreviations are handled:
- `id` → "ID"
- `url` → "URL"
- `api` → "API"
- `uuid` → "UUID"

### Automatic Field Exclusion

These field types are automatically excluded when `auto_exclude_non_human_fields=True`:
- `ImageField`, `FileField` - Binary data
- `TextField` - Usually too long for Excel
- `JSONField` - Complex data structures
- `ManyToManyField` - Complex relationships
- Password fields, tokens, secrets
- Technical fields like `uuid`, `slug`

### Data Formatting

Values are formatted for human readability:
- **Booleans**: `True` → "Yes", `False` → "No"
- **Dates**: `2024-01-15 10:30:00` → "2024-01-15 10:30:00"
- **Choices**: Uses display values from field choices
- **Decimals**: Formatted to 2 decimal places
- **Foreign Keys**: Uses the object's `__str__` method

### Relationship Handling

Include related object data:

```python
# Include staff information in attendance export
excel_file = global_model_export(
    'hrm.Attendance',
    include_relations=['staff'],
    document_name='Attendance_With_Staff'
)
```

Related fields are prefixed: "Staff - Name", "Staff - Email"

## Excel Styling

Generated Excel files include:
- **Professional header styling**: Blue background, white bold text
- **Auto-adjusted column widths**: Based on content length
- **Consistent formatting**: Proper alignment and spacing
- **Sheet naming**: Uses model verbose names when available

## Usage Examples

### 1. Export from Django Management Command

```python
# management/commands/export_monthly_report.py
from django.core.management.base import BaseCommand
from core.utils.functions import global_model_export
from django.http import HttpResponse

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Export last month's attendance
        from datetime import datetime, timedelta
        last_month = datetime.now() - timedelta(days=30)
        
        excel_file = global_model_export(
            'hrm.Attendance',
            filters={'date__gte': last_month},
            include_relations=['staff'],
            document_name='Monthly_Attendance_Report'
        )
        
        # Save to file
        with open('monthly_report.xlsx', 'wb') as f:
            f.write(excel_file.getvalue())
```

### 2. Export from Custom View

```python
# views.py
from django.http import HttpResponse
from core.utils.functions import global_model_export

def export_business_report(request):
    excel_file = global_model_export(
        'statements.Business',
        filters={'is_active': True, 'is_customer': True},
        exclude_fields=['registration_number'],
        document_name='Customer_Businesses'
    )
    
    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="customer_businesses.xlsx"'
    return response
```

### 3. Export from Celery Task

```python
# tasks.py
from celery import shared_task
from core.utils.functions import global_model_export
from django.core.mail import EmailMessage

@shared_task
def send_weekly_report():
    excel_file = global_model_export(
        'statements.Business',
        filters={'created_at__week': datetime.now().isocalendar()[1]},
        document_name='Weekly_New_Businesses'
    )
    
    email = EmailMessage(
        'Weekly Business Report',
        'Please find attached the weekly business report.',
        'reports@company.com',
        ['manager@company.com']
    )
    email.attach('weekly_report.xlsx', excel_file.getvalue(), 
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.send()
```

## Configuration Options

You can customize the export behavior by modifying the default parameters:

```python
# For technical exports (keep original field names)
excel_file = global_model_export(
    'statements.Business',
    human_readable_headers=False,
    auto_exclude_non_human_fields=False
)

# For end-user reports (maximum readability)
excel_file = global_model_export(
    'statements.Business',
    human_readable_headers=True,
    auto_exclude_non_human_fields=True,
    include_relations=['contact_person']
)
```

## Best Practices

1. **Use descriptive document names**: Include dates, filters, or purpose
2. **Limit large exports**: Use pagination or filters for performance
3. **Include relevant relationships**: Only include relationships users need
4. **Test with sample data**: Verify output format before production use
5. **Handle errors gracefully**: Wrap exports in try-catch blocks
6. **Consider caching**: Cache frequently requested exports

## Performance Considerations

- Use `select_related()` for included foreign key relationships
- Apply filters to limit data size
- Consider pagination for very large datasets
- Monitor memory usage for large exports

## Troubleshooting

**Common Issues:**

1. **Empty Excel file**: Check if queryset has data and filters are correct
2. **Missing relationships**: Ensure relationship field names are correct
3. **Formatting issues**: Verify field types and choices are properly defined
4. **Memory errors**: Reduce dataset size or implement pagination

**Debug Tips:**

```python
# Test with small dataset first
excel_file = global_model_export(
    'statements.Business',
    queryset=Business.objects.all()[:10],  # Limit to 10 records
    document_name='Test_Export'
)
```