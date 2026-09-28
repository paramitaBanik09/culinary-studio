# Copyright 2026 Google LLC
# Function tools for Culinary Studio agent with Firestore, GCS, and ADK Artifact integration

import base64
import json
import os
import time
import urllib.parse
import urllib.request
from typing import List, Optional
from google import genai
from google.genai import types
from google.cloud import firestore, storage
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-01-6413c4a6c2e0"
COLLECTION_NAME = "menu_items"
BUCKET_NAME = "culinary-studio-media-6413c4"

db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

def list_menu_items(category: Optional[str] = None) -> str:
    """Lists menu items from the restaurant's catalog in Firestore.
    
    Args:
        category: Optional filter by category (e.g., 'Beverages', 'Mains', 'Bowls', 'Breakfast & Brunch').
        
    Returns:
        JSON string containing matching menu items with details.
    """
    try:
        query_ref = db.collection(COLLECTION_NAME)
        if category and category.strip():
            query_ref = query_ref.where("category", "==", category.strip())
            
        docs = query_ref.stream()
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            items.append(item_data)
            
        if not items:
            return json.dumps({"status": "empty", "message": f"No menu items found in category '{category}'" if category else "No menu items found."})
            
        return json.dumps({"status": "success", "count": len(items), "items": items}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def add_menu_item(
    name: str,
    category: str,
    description: str,
    cost_price: float,
    selling_price: float,
    dietary_tags: Optional[List[str]] = None
) -> str:
    """Adds a new menu item to the restaurant catalog in Firestore.
    
    Args:
        name: Name of the dish or beverage.
        category: Category (e.g., 'Beverages', 'Mains', 'Desserts', 'Breakfast & Brunch').
        description: Description of the dish and ingredients.
        cost_price: Cost to prepare/produce the item (in USD).
        selling_price: Recommended menu selling price (in USD).
        dietary_tags: List of tags like ['vegan', 'gluten-free', 'dairy-free'].
        
    Returns:
        JSON string confirming item creation with item ID and calculated margin %.
    """
    try:
        margin_percent = round(((selling_price - cost_price) / selling_price) * 100, 2) if selling_price > 0 else 0.0
        doc_ref = db.collection(COLLECTION_NAME).document()
        
        item_data = {
            "id": doc_ref.id,
            "name": name,
            "category": category,
            "description": description,
            "cost_price": float(cost_price),
            "selling_price": float(selling_price),
            "margin_percent": margin_percent,
            "dietary_tags": dietary_tags or [],
        }
        
        doc_ref.set(item_data)
        return json.dumps({
            "status": "success",
            "message": f"Successfully added '{name}' to menu catalog.",
            "item": item_data
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def calculate_plate_cost(cost_price: float, selling_price: float) -> str:
    """Calculates food cost percentage, gross profit, and margin for a dish.
    
    Args:
        cost_price: Cost to prepare/produce the dish (in USD).
        selling_price: Selling price on the menu (in USD).
        
    Returns:
        JSON string with calculated metrics and financial advice.
    """
    if selling_price <= 0:
        return json.dumps({"status": "error", "message": "Selling price must be greater than 0."})
        
    profit = selling_price - cost_price
    margin_pct = round((profit / selling_price) * 100, 2)
    cost_pct = round((cost_price / selling_price) * 100, 2)
    
    recommendation = "Healthy margin (above 70%)" if margin_pct >= 70 else "Low margin (target > 70% for standard cafe profitability)"
    
    return json.dumps({
        "status": "success",
        "cost_price": cost_price,
        "selling_price": selling_price,
        "gross_profit_per_item": round(profit, 2),
        "food_cost_percentage": cost_pct,
        "margin_percentage": margin_pct,
        "recommendation": recommendation
    }, indent=2)

def generate_dish_image(
    item_name: str,
    tool_context: ToolContext,
    visual_style: Optional[str] = None
) -> str:
    """Generates an image for a menu item using gemini-3.1-flash-lite-image in the global region.
    
    Saves the image as an artifact in ADK tool_context and uploads it to Cloud Storage, returning the public HTTPS URL.
    
    Args:
        item_name: Name or description of the menu item (e.g., 'Oat Milk Iced Matcha Latte').
        tool_context: ADK ToolContext automatically injected by the agent runtime.
        visual_style: Optional visual style instructions (e.g., 'rustic wooden table', 'gourmet plating').
        
    Returns:
        JSON string containing the public HTTPS URL of the uploaded image and saved artifact details.
    """
    try:
        style_prompt = visual_style or "professional food photography, appetizing presentation, soft cafe lighting, high resolution"
        full_prompt = f"Professional food photo of {item_name}. Style: {style_prompt}"
        
        # Generate image using gemini-3.1-flash-lite-image in the global region
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=full_prompt,
        )
        
        image_bytes = None
        mime_type = "image/jpeg"
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break
            if image_bytes:
                break
                
        if not image_bytes:
            return json.dumps({"status": "error", "message": "Failed to generate image bytes from model response."})
            
        timestamp = int(time.time())
        clean_name = item_name.lower().replace(" ", "_").replace("/", "_")
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"{clean_name}_{timestamp}.{ext}"
        
        # 1. Save artifact in Playground's Artifacts panel using tool_context.save_artifact
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)
        
        # 2. Upload same image bytes to public Cloud Storage bucket (hardcoded string)
        blob_name = f"dishes/{filename}"
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        
        # Optional: Sync URL back to Firestore if document matches item_name
        docs = list(db.collection(COLLECTION_NAME).stream())
        for d in docs:
            data = d.to_dict()
            if data.get("name", "").lower() == item_name.lower() or item_name.lower() in data.get("name", "").lower():
                d.reference.update({"image_url": public_url, "updated_at": timestamp})
                break

        return json.dumps({
            "status": "success",
            "message": f"Successfully generated image for '{item_name}'.",
            "public_url": public_url,
            "artifact_filename": filename
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def generate_dish_video(
    item_name: str,
    tool_context: ToolContext,
    motion_style: Optional[str] = None
) -> str:
    """Generates a short video showcase for a menu item using Google's gemini-omni-flash-preview model in the global region.
    
    Saves the video as an artifact in ADK tool_context and uploads it to Cloud Storage, returning the public HTTPS URL.
    
    Args:
        item_name: Name or description of the dish or beverage (e.g., 'Artisanal Berry Cheesecake', 'Pour-over Single Origin Coffee').
        tool_context: ADK ToolContext automatically injected by the agent runtime.
        motion_style: Optional motion style description (e.g., 'slow motion slice', 'steam rising', 'syrup drizzle').
        
    Returns:
        JSON string containing the public HTTPS URL of the uploaded video and saved artifact details.
    """
    try:
        style_prompt = motion_style or "cinematic culinary presentation, smooth motion, mouthwatering detail, warm studio lighting"
        full_prompt = f"Generate a short video showing {item_name}. Motion style: {style_prompt}"
        
        # Generate video using gemini-omni-flash-preview via Interactions API in the global region
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=full_prompt,
        )
        
        vid = getattr(interaction, "output_video", None)
        if not vid or not getattr(vid, "data", None):
            return json.dumps({"status": "error", "message": "Failed to generate video output from model response."})
            
        mime_type = getattr(vid, "mime_type", "video/mp4") or "video/mp4"
        raw_data = vid.data
        if isinstance(raw_data, str):
            video_bytes = base64.b64decode(raw_data)
        else:
            video_bytes = raw_data
            
        timestamp = int(time.time())
        clean_name = item_name.lower().replace(" ", "_").replace("/", "_")
        filename = f"{clean_name}_{timestamp}.mp4"
        
        # 1. Save artifact in Playground's Artifacts panel using tool_context.save_artifact
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)
        
        # 2. Upload same video bytes to public Cloud Storage bucket (hardcoded string)
        blob_name = f"videos/{filename}"
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully generated video showcase for '{item_name}'.",
            "public_url": public_url,
            "artifact_filename": filename
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def search_recipe_inspiration(query: str) -> str:
    """Searches a public culinary database (TheMealDB) for authentic recipe inspiration, ingredients, and preparation ideas.
    
    Args:
        query: Search term for dish or ingredient (e.g., 'pasta', 'tacos', 'salad', 'salmon').
        
    Returns:
        JSON string containing matching recipes with ingredient lists, cuisine origin, and instructions.
    """
    try:
        api_key = os.environ.get("MEALDB_API_KEY", "1")  # Free public API key default is '1'
        encoded_query = urllib.parse.quote(query.strip())
        url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "CulinaryStudioAgent/1.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        meals = data.get("meals")
        if not meals:
            return json.dumps({"status": "empty", "message": f"No culinary recipes found for query '{query}'."})
            
        results = []
        for meal in meals[:3]:  # Top 3 results
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                meas = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ingredients.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())
                    
            results.append({
                "id": meal.get("idMeal"),
                "name": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "cuisine_area": meal.get("strArea"),
                "ingredients": ingredients,
                "instructions": (meal.get("strInstructions") or "")[:300] + "...",
                "thumbnail": meal.get("strMealThumb")
            })
            
        return json.dumps({
            "status": "success",
            "count": len(results),
            "recipes": results
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
