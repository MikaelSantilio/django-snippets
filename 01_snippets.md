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
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def active_superuser(sender, instance, **kwargs):
    post_save.disconnect(active_superuser, sender=sender)

    if instance.is_superuser:
        instance.is_active = True
        instance.save()

    post_save.connect(active_superuser, sender=sender)


post_save.connect(active_superuser, sender=User)
```
