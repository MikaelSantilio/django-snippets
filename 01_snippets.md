## Snippets 01


### Imports

```python
from django.conf import settings

```

### SubQuery Django ORM

```python
from django.db.models import OuterRef, Subquery
from library.models import Book


Book.objects.all().update(
            genre=Subquery(Book.objects.filter(pk=OuterRef('pk')).values('author__genre')[:1])
        )

# OR

Book.objects.all().update(genre=Subquery(Book.objects.get(pk=OuterRef('pk')).author.genre))

```

### Signals Superuser

```python
from django.db import models
from django.contrib.auth.models import AbstractUser

from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):

    name = models.CharField("Nome completo", max_length=255)
    email = models.EmailField("Endereço de email", unique=True, max_length=255)
    is_active = models.BooleanField("Ativo", default=False)

    REQUIRED_FIELDS = ["name", "email"]


@receiver(post_save, sender=User)
def active_superuser(sender, instance, **kwargs):
    post_save.disconnect(active_superuser, sender=sender)

    if instance.is_superuser:
        instance.is_active = True
        instance.save()

    post_save.connect(active_superuser, sender=sender)


post_save.connect(active_superuser, sender=User)
```


### FilteredListView

```python
# Font: https://www.caktusgroup.com/blog/2018/10/18/filtering-and-pagination-django/

class FilteredListView(ListView):
    filterset_class = None

    def get_queryset(self):
        # Get the queryset however you usually would.  For example:
        queryset = super().get_queryset()
        # Then use the query parameters and the queryset to
        # instantiate a filterset and save it as an attribute
        # on the view instance for later.
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        # Return the filtered queryset
        return self.filterset.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the filterset to the template - it provides the form.
        context['filterset'] = self.filterset
        return context

# Usage
class BookListView(FilteredListView):
    model = Book
    filterset_class = BookFilterset
    paginate_by = 5
    template_name = 'books/my_books.html'
```

```html

<h1>Books</h1>
  <form action="" method="get">
    {{ filterset.form.as_p }}
    <input type="submit" />
  </form>

<ul>
    {% for object in object_list %}
        <li>{{ object }}</li>
    {% endfor %}
</ul>

<div class="pagination">
    <span class="step-links">
        {% if page_obj.has_previous %}
            <a href="?page=1">&laquo; first</a>
            <a href="?page={{ page_obj.previous_page_number }}">previous</a>
        {% endif %}

        <span class="current">
            Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}.
        </span>

        {% if page_obj.has_next %}
            <!-- https://stackoverflow.com/questions/52007038/pagination-using-listview-and-a-dynamic-filtered-queryset -->
            <a href="?{{ request.GET.urlencode }}&page={{ page_obj.next_page_number }}">next</a>
            <a href="?{{ request.GET.urlencode }}&page={{ page_obj.paginator.num_pages }}">last &raquo;</a>
        {% endif %}
    </span>
</div>
```

### Formatar Data de Postagem

```python
def gerar_data_postagem(self):
        diff = datetime.now(utc) - self.criacao.replace(tzinfo=utc)
        return formatar_data_postagem(diff, self.criacao)

def formatar_data_postagem(timedelta, datetime_criacao):

    calendario = {
            '01': 'Janeiro',
            '02': 'Fevereiro',
            '03': 'Março',
            '04': 'Abril',
            '05': 'Maio',
            '06': 'Junho',
            '07': 'Julho',
            '08': 'Agosto',
            '09': 'Setembro',
            '10': 'Outubro',
            '11': 'Novembro',
            '12': 'Dezembro',
    }

    if timedelta.days == 0 and timedelta.seconds / 3600 < 1:
        return f'Há {timedelta.seconds / 60} minutos'
    elif timedelta.days == 0 and timedelta.seconds / 3600 <= 12:
        return f'Há {timedelta.seconds / 3600} horas'
    else:
        dia, mes, ano = datetime_criacao.strftime('%d-%m-%Y').split('-')
        return f'{dia} de {calendario[mes]} de {ano}'
```

