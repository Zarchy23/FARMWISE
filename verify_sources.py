#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import User, Farm, EmissionSource

# Get first user and farm
user = User.objects.first()
if user:
    print(f'User: {user.username}')
    farms = user.farms.all()
    for farm in farms[:1]:
        print(f'  Farm: {farm.name} (ID: {farm.id})')
        sources = EmissionSource.objects.filter(farm=farm)
        print(f'  Sources: {sources.count()}')
        for s in sources[:3]:
            print(f'    - {s.name}: {s.emission_factor} {s.unit}')
