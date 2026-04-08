#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import Animal, CropSeason

print("Current photo fields in database:")
print("\nAnimals:")
for animal in Animal.objects.all():
    if animal.photo:
        print(f"  Animal {animal.id}: '{animal.photo}'")

print("\nCrops:")
for crop in CropSeason.objects.all():
    if crop.photo:
        print(f"  Crop {crop.id}: '{crop.photo}'")

print("\n" + "="*50)
print("Clearing all photo fields...")
Animal.objects.all().update(photo='')
CropSeason.objects.all().update(photo='')
print("Done! All photo fields have been cleared.")

print("\nVerified - remaining photos:")
animals_with_photos = Animal.objects.exclude(photo='').count()
crops_with_photos = CropSeason.objects.exclude(photo='').count()
print(f"Animals with photos: {animals_with_photos}")
print(f"Crops with photos: {crops_with_photos}")
