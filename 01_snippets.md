## Snippets 01

### SubQuery Django ORM


```python
from django.db.models import OuterRef, Subquery
from library.models import Book


Book.objects.all().update(
            genre=Subquery(Book.objects.filter(pk=OuterRef('pk')).values('author__genre')[:1])
        )

```