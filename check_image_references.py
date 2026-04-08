#!/usr/bin/env python
"""
Script to check and fix broken image references
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import ProductListing
from django.conf import settings

# Check all product listings
listings = ProductListing.objects.all()
print(f"Total product listings: {listings.count()}\n")
print("=" * 80)

broken_refs = []
valid_refs = []

for listing in listings:
    if listing.images:
        image_path = listing.images.name
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
        exists = os.path.exists(full_path)
        
        status = "✓ EXISTS" if exists else "✗ BROKEN"
        print(f"\nListing {listing.id}: {listing.product_name}")
        print(f"  Image: {image_path}")
        print(f"  Status: {status}")
        
        if not exists:
            broken_refs.append((listing.id, listing.product_name, image_path))
        else:
            valid_refs.append((listing.id, listing.product_name, image_path))
    else:
        print(f"\nListing {listing.id}: {listing.product_name}")
        print(f"  Image: None")

print("\n" + "=" * 80)
print(f"\nSummary:")
print(f"  Valid references: {len(valid_refs)}")
print(f"  Broken references: {len(broken_refs)}")

if broken_refs:
    print(f"\nBroken image references to fix:")
    for listing_id, product_name, image_path in broken_refs:
        print(f"  - Listing {listing_id} ({product_name}): {image_path}")

# Check actual files in media/marketplace/products
media_root = settings.MEDIA_ROOT
products_dir = os.path.join(media_root, 'marketplace', 'products')

print(f"\n" + "=" * 80)
print(f"\nFiles in {products_dir}:")
if os.path.exists(products_dir):
    for root, dirs, files in os.walk(products_dir):
        level = root.replace(products_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{subindent}{file}')
else:
    print(f"Directory does not exist!")
