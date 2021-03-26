## Django Rest Framework

### HATEOAS Serializer
```python
from rest_framework import serializers
from cars import models

class CarHATEOASerializer(serializers.ModelSerializer):
    brand = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
     )
    model = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
     )
    links = serializers.SerializerMethodField()

    class Meta:
        model = models.Car
        fields = ('id', 'brand', 'model', 'version', 'min_sale_value', 'links')

    def get_links(self, obj):
        data = []

        request = self.context['request']

        data.append(
            {
                "type": "GET",
                "rel": "self",
                "uri": request.build_absolute_uri(
                    reverse("api:cars:cars-detail", kwargs={'pk': obj.id}))
            }
        )

        if request.user.is_authenticated:

            if request.user.is_store_manager or request.user.is_superuser:
                data += [
                    {
                        "type": "PUT",
                        "rel": "carro_atualizacao",
                        "uri": request.build_absolute_uri(reverse("api:cars:cars-detail", kwargs={'pk': obj.id}))
                    },
                    {
                        "type": "DELETE",
                        "rel": "carro_exclusao",
                        "uri": request.build_absolute_uri(reverse("api:cars:cars-detail", kwargs={'pk': obj.id}))
                    }
                ]

        return data
```

### Custom LoginSerializer from Third-Party App

```python
# serializers.py
class LoginSerializer(serializers.Serializer):

    """
        LoginSerializer from django-rest-auth
        https://github.com/Tivix/django-rest-auth/blob/624ad01afbc86fa15b4e652406f3bdcd01f36e00/rest_auth/serializers.py#L19
    """

    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'}
    )

    def _validate_email(self, email, password):
        user = None

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

        else:
            msg = _('Deve incluir "email" e "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username(self, username, password):
        user = None

        if username and password:
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)
        else:
            msg = _('Deve incluir "username" e "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username_email(self, username, email, password):
        user = None

        if email and password:
            user = authenticate(email=email, password=password)
        elif username and password:
            user = authenticate(username=username, password=password)
        else:
            msg = _('Deve incluir "username" ou "email" e "password".')
            raise exceptions.ValidationError(msg)

        return user

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        # Authentication through email
        if settings.AUTHENTICATION_METHOD == 'email':
            user = self._validate_email(email, password)

        # Authentication through username
        elif settings.AUTHENTICATION_METHOD == 'username':
            user = self._validate_username(username, password)

        # Authentication through either username or email
        elif settings.AUTHENTICATION_METHOD == 'username_email':
            user = self._validate_username_email(username, email, password)

        else:
            # Authentication without using setting authentication method
            if email:
                try:
                    username = User.objects.get(email__iexact=email).get_username()  # noqaES51
                except User.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, '', password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _('O usuário não foi ativado.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Impossível fazer login com as credenciais fornecidas.')
            raise exceptions.ValidationError(msg)

        attrs['user'] = user
        return attrs


# views.py
from django.contrib.auth import login
from knox.views import LoginView as KnoxLoginView
from rest_framework import permissions
from .serializers import AuthTokenSerializer


class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        # serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginView, self).post(request, format=None)
```