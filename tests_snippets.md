## Unit Test Snippets

### Test Views

```python
from django.test import Client, TestCase
from django.urls import reverse
from books.tests.factories import BookFactory, UserFactory

class BookCreateViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='user.test')
        cls.default_passwd = 'django01'
        cls.user.set_password(cls.default_passwd)
        cls.user.save()

    def setUp(self):
        self.client = Client()
        self.url = reverse('books:book_create')

    def test_get_without_login(self):
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_get_with_login(self):
        self.client.login(username=self.user.username, password=self.default_passwd)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'book_create.html')

    def test_post_with_login(self):
        self.client.login(username=self.user.username, password=self.default_passwd)

        book = Book.build()
        context = {
            'name': book.name,
            'genre': book.genre.pk,
            'author': book.author.pk,
        }

        response = self.client.post(self.url, context)
        book_obj = Book.objects.all().last()
        book_url = reverse('books:book_detail', kwargs={'pk': book_obj.pk})
        self.assertRedirects(response, book_url)
```


### Test Forms
```python
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from books.tests.factories import BookFactory


def get_errors(form):
    error_msg = {}
    for field in form:
        if field.errors.data != []:
            error_msg[field.name] = field.errors

    return error_msg


class BookFormTestCase(TestCase):

    def setUp(self):
        self.book = BookFactory.build()
        self.context = {
            'name': self.book.name,
            'genre': self.book.genre.pk,
            'author': self.book.author.pk,
        }
        self.file = {'file': SimpleUploadedFile('file.pdf', b'file')}

    def test_book_form_valid(self):
        form = BookForm(self.context, files=self.file)
        self.assertTrue(form.is_valid())

    def test_book_form_invalid(self):
        form = BookForm({'name': None})
        errors = get_errors(form)

        errors_assert = {
            'name': ['Este campo é obrigatório.'],
            'genre': ['Este campo é obrigatório.'],
            'author': ['Este campo é obrigatório.'],
        }

        self.assertEqual(errors, errors_assert)

```


### Test Models
```python
from django.test import TestCase
from books.tests.factories import BookFactory


class BookTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.book = BookFactory()

    def test_book_has_author(self):
        self.assertTrue(self.book.author)

    def test_name_label(self):
        self.assertEqual(self.processo.get_name_label(), f'{self.book.name} - {self.book.genre}')

    def test_object_name(self):
        self.assertEqual(str(self.book), self.book.name)

```

### Test Formset
```python
    def test_formset_post(self):
        self.client.login(username=self.user.username, password=self.default_passwd)

        response = self.client.post(self.url, {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-genre': 'Programming',
            'form-0-author': 'David Beazley',
            'form-0-name': 'Python Cookbook',
        })
        # print(response.context['form']._errors)
        self.assertEqual(response.status_code, 302)

```


### Test API
```python
from rest_framework.test import APIClient, APITransactionTestCase
from books.tests.factories import BookFactory, UserFactory
from rest_framework import status
from django.urls import reverse


class BookAPITestCase(APITransactionTestCase):

    def setUp(self):

        BookFactory.create_batch(10)

        self.user = UserFactory()
        self.default_passwd = "django01"
        self.user.set_password(self.default_passwd)
        self.user.save()

        self.client = APIClient()

        request_login = self.client.post(
            reverse("users:login"),
            data={"username": self.user.username, "password": self.default_passwd}, format="json")

        self.token = request_login.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

    def test_list_books(self):

        BookFactory(user=self.user)
        request = self.client.get(reverse("books:books_list"))

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.assertEqual(len(request.data), 11)

    def test_delete_book(self):

        alert = BookFactory()
        request = self.client.delete(reverse("books:book_detail", kwargs={"pk": alert.pk}))

        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(request.data, None)

```

