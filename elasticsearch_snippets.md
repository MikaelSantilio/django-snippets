## ElasticSearch DSL Snippets

### List Nested Fields

```python
# Pass data on format: users = [
#         {'first_name': 'Mikael', 'last_name': 'Santilio'},
#         {'first_name': 'Joao', 'last_name': 'Silva'}
#     ]
users = fields.ListField(
    fields.NestedField(
        properties={
            'first_name': fields.TextField(
                analyzer=html_strip,
                fields={'raw': fields.KeywordField()}
            ),
            'last_name': fields.TextField(
                analyzer=html_strip,
                fields={'raw': fields.KeywordField()}
            ),
        },)
)

# OR

users = fields.NestedField(
    properties={
        'first_name': fields.TextField(
            analyzer=html_strip,
            fields={'raw': fields.KeywordField()}
        ),
        'last_name': fields.TextField(
            analyzer=html_strip,
            fields={'raw': fields.KeywordField()}
        ),
    },
   multi=True)
```

### Check Changes on Bulk Files Elastic Search

```python
from datetime import datetime
from itertools import zip_longest

import pytz
from django.conf import settings
from django_elasticsearch_dsl import Document


class TimestampDocument(Document):

    def _check_changes_documents(self, source_original_document, source_new_document):
        changes = False
        for key in source_new_document:
            if key not in source_original_document and source_new_document[key] is None:
                continue
            if key not in source_original_document:
                changes = True
                break
            if source_new_document[key] != source_original_document[key]:
                changes = True
                break
        return changes

    def _prepare_action(self, object_instance, action, document):
        result = {
            '_op_type': action,
            '_index': self._index._name,
            '_id': object_instance.pk,
            '_source': (
                self.prepare(object_instance) if action != 'delete' else None
            ),
        }
        if document:
            original_document_dict = document.to_dict()
            changes = self._check_changes_documents(original_document_dict, result['_source'])
            if changes or '@timestamp' not in original_document_dict:
                tz_LOCAL = pytz.timezone(settings.TIME_ZONE)
                output_date = datetime.now(tz_LOCAL)
                result['_source']['@timestamp'] = output_date
            else:
                result['_source']['@timestamp'] = original_document_dict['@timestamp']
        else:
            tz_LOCAL = pytz.timezone(settings.TIME_ZONE)
            output_date = datetime.now(tz_LOCAL)
            result['_source']['@timestamp'] = output_date
        return result

    def _get_objects_pks(self, object_list):
        pks = []
        for object_instance in object_list:
            pks.append(object_instance.pk)
        return pks

    def _get_actions(self, object_list, action):
        object_array = list(object_list)
        documents_generator = self.mget(self._get_objects_pks(object_array))
        docs = list(documents_generator)

        for object_instance, doc in zip_longest(object_array, docs):
            yield self._prepare_action(object_instance=object_instance, action=action, document=doc)


```

### Check Changes on Bulk Files Elastic Search with SQLAlchemy

```python
from collections import deque
from datetime import datetime
from itertools import zip_longest

import pytz
import sqlalchemy
from django.conf import settings
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.exceptions import ModelFieldNotMappedError
from django_elasticsearch_dsl.fields import BooleanField, DateField, IntegerField, TextField
from elasticsearch.helpers import parallel_bulk

model_sqlalchemy_field_class_to_field_class = {
    sqlalchemy.Integer: IntegerField,
    sqlalchemy.Boolean: BooleanField,
    sqlalchemy.String: TextField,
    sqlalchemy.Text: TextField,
    sqlalchemy.Date: DateField,
    sqlalchemy.DateTime: DateField
}


class SQLAlchemyDocument(Document):

    def get_indexing_queryset(self, database):
        model = self.meta_sqlalchemy()['model']
        return database.query_all(model)

    def prepare(self, instance):
        data = {
            field: value
            for field, value in self._prepared_dict_fields(instance)
        }
        return data

    def _prepared_dict_fields(self, instance):
        fields = []
        for field in dir(instance):
            if field.startswith('_') or field in ['metadata', 'pk']:
                continue
            value = getattr(instance, field, 'Attribute is not found')
            if value == 'Attribute is not found':
                continue
            fields.append((field, value))
        return fields

    @classmethod
    def to_field(cls, field_name, model_field):
        try:
            return model_sqlalchemy_field_class_to_field_class[
                model_field.__class__](attr=field_name)
        except KeyError:
            raise ModelFieldNotMappedError(
                "Cannot convert sqlalchemy model field {} "
                "to an Elasticsearch field!".format(field_name)
            )

    def parallel_bulk(self, actions, **kwargs):
        bulk_actions = parallel_bulk(client=self._get_connection(), actions=actions, **kwargs)
        deque(bulk_actions, maxlen=0)
        return (1, [])

    def _prepare_action(self, object_instance, action):
        result = {
            '_op_type': action,
            '_index': self._index._name,
            '_id': object_instance.pk,
            '_source': (
                self.prepare(object_instance) if action != 'delete' else None
            ),
        }
        tz_LOCAL = pytz.timezone(settings.TIME_ZONE)
        output_date = datetime.now(tz_LOCAL)
        result['_source']['@timestamp'] = output_date
        return result

    def update(self, thing, refresh=None, action='index', parallel=False, **kwargs):
        kwargs['refresh'] = True
        object_list = thing
        return self._bulk(
            self._get_actions(object_list, action),
            parallel=parallel,
            **kwargs
        )


class SQLAlchemyTimestampDocument(SQLAlchemyDocument):

    def _check_changes_documents(self, source_original_document, source_new_document):
        changes = False
        for key in source_new_document:
            if key not in source_original_document and not source_new_document[key] is None:
                changes = True
                break
            elif key not in source_original_document and source_new_document[key] is None:
                continue
            if source_new_document[key] != source_original_document[key]:
                changes = True
                break
        return changes

    def _set_timestamp(self, result, document_instance):
        if document_instance:
            original_document_dict = document_instance.to_dict()
            changes = self._check_changes_documents(original_document_dict, result['_source'])
            if changes:
                tz_LOCAL = pytz.timezone(settings.TIME_ZONE)
                output_date = datetime.now(tz_LOCAL)
                result['_source']['@timestamp'] = output_date
            else:
                result['_source']['@timestamp'] = original_document_dict['@timestamp']
        else:
            tz_LOCAL = pytz.timezone(settings.TIME_ZONE)
            output_date = datetime.now(tz_LOCAL)
            result['_source']['@timestamp'] = output_date

        return result

    def _prepare_action(self, object_instance, action, document_instance):
        result = {
            '_op_type': action,
            '_index': self._index._name,
            '_id': object_instance.pk,
            '_source': (
                self.prepare(object_instance) if action != 'delete' else None
            ),
        }
        return self._set_timestamp(result=result, document_instance=document_instance)

    def _get_objects_pks(self, object_list):
        pks = []
        for object_instance in object_list:
            pks.append(object_instance.pk)
        return pks

    def _get_actions(self, object_list, documents_list, action):

        for object_instance, document_instance in zip_longest(object_list, documents_list):
            yield self._prepare_action(
                object_instance=object_instance, action=action, document_instance=document_instance)

    def update(self, thing, refresh=None, action='index', parallel=False, **kwargs):
        kwargs['refresh'] = True
        object_list = thing
        object_list = list(object_list)

        documents_list = self.mget(self._get_objects_pks(object_list))
        documents_list = list(documents_list)

        return self._bulk(
            self._get_actions(object_list, documents_list, action),
            parallel=parallel,
            **kwargs
        )

```

### Bulk Data Celery Task

```python
from __future__ import absolute_import, unicode_literals

from celery import task
from django.conf import settings
from django.db.utils import ConnectionHandler
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl.connections import connections


def check_db_connection(db_key):
    try:
        ConnectionHandler(databases=settings.DATABASES)[db_key].ensure_connection()
        return True

    except Exception:
        return False


def bulk_data(Document, parallel=True):
    indices = registry.get_indices({Document.Django.model})

    model_index = indices.pop()
    if not connections.get_connection().indices.exists(index=model_index._name):
        model_index.create()

    qs = Document().get_indexing_queryset()
    Document().update(qs, parallel=parallel)


@task(name='bulk_data_by_db')
def bulk_data_by_db(db_key, parallel=True):
    if not check_db_connection(db_key):
        return False

    models = registry.get_models()
    models_from_db = set()

    for model in models:
        if model._meta.db_key == db_key:
            models_from_db.add(model)

    for doc in registry.get_documents(models_from_db):
        bulk_data(doc, parallel)

```

### AutoDiscover documents.py

```python
import os
from importlib import import_module


def abspath_to_pypath(abs_path, file, cwd_path):

    main_path = abs_path.replace(cwd_path, '')
    path_doc_array = main_path.split('/')
    path_doc_array.append(file)

    path_documents = '.'.join(path_doc_array).strip('.py')

    return path_documents


def autodiscover_documents(file_path):

    caller_folder = os.path.dirname(file_path)
    cwd_path = os.getcwd()

    for current, folders, files in os.walk(caller_folder):
        if current.endswith("__pycache__") or current.endswith("migrations"):
            continue

        basename_path = os.path.basename(current)

        for file in files:
            if file == "documents.py":
                path_documents = abspath_to_pypath(current, file, cwd_path)
                import_module(path_documents)

            elif file != "__init__.py" and file.endswith(".py") and basename_path == "documents":
                path_documents = abspath_to_pypath(current, file, cwd_path)
                import_module(path_documents)


autodiscover_documents(__file__)
```