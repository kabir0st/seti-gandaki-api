import os
import subprocess
import time
from copy import deepcopy
from os import makedirs, path

import openpyxl
import pandas as pd
from django.apps import apps
from django.conf import settings
from django.core.mail import send_mail
from django.db import connection, models
from django.utils.text import slugify
from django.utils.timezone import now

from core.settings.environments import DB_NAME, DB_PASSWORD, DB_USERNAME


def get_path(e_path):
    file_path = f"{e_path}/{str(now().date())}/"
    if path.exists(file_path):
        return file_path
    else:
        makedirs(file_path)
        return file_path


def check_path(e_path):
    file_path = f"{e_path}/"
    if path.exists(file_path):
        return file_path
    else:
        makedirs(file_path)
        return file_path


@celery_app.task
def write_log_file(log_type, msg, is_error=False):
    file_name = 'yield'
    if is_error:
        file_name = 'error'
    file = f"{get_path('logs/'+log_type)}/{file_name}.log"

    with open(file, 'a') as f:
        f.write(f"{now()} : {msg}\n")


@celery_app.task
def push_email(to, subject, message=None, html=None, obj=None):
    res = send_mail(subject,
                    message,
                    settings.EMAIL_HOST_USER, [to],
                    html_message=html)
    if res:
        if obj:
            obj.is_email_sent = True
            obj.save()
            return True
    else:
        write_log_file('app/email', f"Failed To Send Email, {obj}", True)
        return False


def extract_field_data(obj, exclude_fields, include_relations):
    stable_relations = deepcopy(include_relations)
    data = {}
    exclude_fields_type = [
        models.ManyToOneRel, models.ManyToManyField, models.ImageField,
        models.FileField
    ]
    for field in obj._meta.get_fields():
        if field.name not in exclude_fields:
            if field.name in stable_relations:
                if isinstance(field, models.OneToOneRel):
                    if hasattr(obj, field.name):
                        stable_relations.remove(field.name)
                        ext = extract_field_data(getattr(obj, field.name),
                                                 exclude_fields,
                                                 stable_relations)
                        ext = {
                            f'{field.name} : {key}': value
                            for key, value in ext.items()
                        }
                        data = {**ext, **data}

            elif not isinstance(field, tuple(exclude_fields_type)):
                if hasattr(obj, field.name):
                    data[field.name] = str(getattr(obj, field.name))
    return data


@celery_app.task
def export_data_task(document_id, ids, exclude_fields, include_relations):
    from system.models import Document
    document = Document.objects.get(id=document_id)
    try:
        model = apps.get_model(document.model)
        base = connection.schema_name
        exclude_fields = exclude_fields + ['id']
        models = model.objects.filter(id__in=ids)
        data = [
            extract_field_data(obj, exclude_fields, include_relations)
            for obj in models
        ]
        df = pd.DataFrame(data)
        file_path = f"media/{base}/reports/{document.model}/"
        if not path.exists(file_path):
            makedirs(file_path)
        name = slugify(f"{document.created_at}")
        with pd.ExcelWriter(
                f'media/{base}/reports/{document.model}/{name}.xlsx'
        ) as writer:
            df.to_excel(writer,
                        sheet_name=f'{document.model}',
                        index=False,
                        na_rep='Nan')
            worksheet = writer.sheets[f'{document.model}']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(),
                                   len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(
                    col_idx + 1)].width = column_width

        document.document = str(
            f'{file_path.replace(f"media/{base}/", "")}{name}.xlsx')
        document.status = 'Done'
        document.save()
    except Exception as e:
        document.status = f'Error {e}'
        document.save()
