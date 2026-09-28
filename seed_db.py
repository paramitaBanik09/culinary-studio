# Copyright 2026 Google LLC
# Seed script for Culinary Studio Firestore database

import sys
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-6413c4a6c2e0"
COLLECTION_NAME = "menu_items"

db = firestore.Client(project=PROJECT_ID)

INITIAL_MENU_ITEMS = [
    {
        "id": "item-001",
        "name": "Oat Milk Iced Matcha Latte",
        "category": "Beverages",
        "description": "Ceremonial grade Uji matcha whisked with organic oat milk and raw agave syrup.",
        "cost_price": 1.20,
        "selling_price": 6.50,
        "margin_percent": 81.54,
        "dietary_tags": ["vegan", "dairy-free", "iced"],
    },
    {
        "id": "item-002",
        "name": "Artisanal Avocado Sourdough Toast",
        "category": "Breakfast & Brunch",
        "description": "Smashed Hass avocado, heirloom cherry tomatoes, microgreens, and chili flakes on slow-fermented sourdough.",
        "cost_price": 2.80,
        "selling_price": 12.00,
        "margin_percent": 76.67,
        "dietary_tags": ["vegetarian", "vegan-option"],
    },
    {
        "id": "item-003",
        "name": "Truffle Wild Mushroom Panini",
        "category": "Mains",
        "description": "Sauteed wild mushrooms, white truffle oil, melted fontina cheese, and arugula on pressed ciabatta.",
        "cost_price": 3.90,
        "selling_price": 15.50,
        "margin_percent": 74.84,
        "dietary_tags": ["vegetarian", "gourmet"],
    },
    {
        "id": "item-004",
        "name": "Açai Power Superfood Bowl",
        "category": "Bowls",
        "description": "Organic açai smoothie base topped with house-made granola, chia seeds, fresh berries, and almond butter drizzle.",
        "cost_price": 2.50,
        "selling_price": 11.50,
        "margin_percent": 78.26,
        "dietary_tags": ["vegan", "gluten-free", "superfood"],
    },
]

def seed_database():
    print(f"Seeding collection '{COLLECTION_NAME}' in project '{PROJECT_ID}'...")
    collection_ref = db.collection(COLLECTION_NAME)
    
    for item in INITIAL_MENU_ITEMS:
        doc_ref = collection_ref.document(item["id"])
        doc_ref.set(item)
        print(f"✓ Seeded item: {item['name']} (ID: {item['id']})")

    print("Firestore seeding complete!")

if __name__ == "__main__":
    seed_database()
