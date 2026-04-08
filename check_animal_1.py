#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import Animal

# Check animal 1 specifically
animal = Animal.objects.get(id=1)
print(f"Animal ID 1:")
print(f"  tag_number: {animal.tag_number}")
print(f"  photo field value: {repr(animal.photo)}")
print(f"  photo field bool: {bool(animal.photo)}")
print(f"  photo field str: '{str(animal.photo)}'")

# Check if there are any non-empty photo values
animals_with_photos = Animal.objects.exclude(photo='').exclude(photo__isnull=True)
print(f"\nAnimals with non-empty photo: {animals_with_photos.count()}")
for a in animals_with_photos:
    print(f"  Animal {a.id}: photo='{a.photo}'")
