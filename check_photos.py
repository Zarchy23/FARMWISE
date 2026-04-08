#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import Animal, CropSeason

# Clear empty/invalid photo fields
print("Clearing any invalid photo fields...")
Animal.objects.filter(photo='').delete()
CropSeason.objects.filter(photo='').delete()

# Update any animals with non-file photo values  
updated = Animal.objects.exclude(photo='').update(photo='')
print(f"Cleared {updated} animals")

updated_crops = CropSeason.objects.exclude(photo='').update(photo='')
print(f"Cleared {updated_crops} crops")

print("\nPhoto fields after cleanup:")
animals = Animal.objects.filter(photo__isnull=False).exclude(photo='')
print(f"Animals with photos: {animals.count()}")
crops = CropSeason.objects.filter(photo__isnull=False).exclude(photo='')
print(f"Crops with photos: {crops.count()}")
