import os
import ast

from django.conf import settings
from core.models import State, City

with open(os.path.join(settings.BASE_DIR,  'estados.txt'), 'r') as file:
    data = file.read().replace('\n', '')
    estados = ast.literal_eval(data)


with open(os.path.join(settings.BASE_DIR,  'cidades.txt'), 'r') as file:
    data = file.read().replace('\n', '')
    cidades = ast.literal_eval(data)


def state_bulk_create(states, State):
    instances = [
        State(
            id=state[0],
            name=state[1],
            uf=state[2]
        ) for state in states
    ]

    State.objects.bulk_create(instances)
    print(f"Quantidade de Estados no BD: {State.objects.count()}")


def city_bulk_create(cities, City, State):
    states = {state.id: state for state in State.objects.all()}

    instances = [
        City(id=city[0], name=city[1], state=states[city[2]]) 
        for city in cities
    ]

    City.objects.bulk_create(instances)
    print(f"Quantidade de Cidades no BD: {City.objects.count()}")


state_bulk_create(estados, State)
city_bulk_create(cidades, City, State)