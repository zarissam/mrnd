from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from openai import OpenAI

# Load environment variables
load_dotenv()

# FastAPI App
app = FastAPI()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["merinid_db"]  # Database name
products_collection = db["products"]  # Collection name

# DeepSeek API Setup
#AI_API_URL = "https://api.deepseek.com/v1/chat/completions"
client = OpenAI(api_key = os.getenv("AI_API_KEY"))

# Load system prompt
with open("systemprompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# --- Models ---
class ManyChatRequest(BaseModel):
    last_input_text: str
    cart_json: list = []

# --- Helper Functions ---

async def search_products_by_keyword(keyword: str):
    query = {
        "$or": [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"body_html": {"$regex": keyword, "$options": "i"}}
        ]
    }
    cursor = products_collection.find(query)
    products = []
    async for product in cursor:
        products.append({
            "id": product["id"],
            "title": product["title"],
            "price": product["variants"][0]["price"],
            "image_url": product.get("image", {}).get("src")
        })
    return products

async def get_product_variants(product_id: int):
    product = await products_collection.find_one({"id": product_id})
    return product.get("variants", []) if product else []

def update_cart(cart, variant_id, quantity=1):
    for item in cart:
        if item["id"] == variant_id:
            item["quantity"] += quantity
            return cart
    cart.append({"id": variant_id, "quantity": quantity})
    return cart

def generate_checkout_link(cart):
    if not cart:
        return None
    parts = [f"{item['id']}:{item['quantity']}" for item in cart]
    return f"https://merinid.com/cart/" + ",".join(parts)

async def call_openai(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7   #, max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print("OpenAI Error:", e)
        return "Sorry, the AI is unavailable at the moment."

# --- Routes ---

@app.post("/webhook")
async def webhook(body: ManyChatRequest):
    user_message = body.last_input_text
    cart = body.cart_json or []

    try:
        ai_reply = await call_openai(user_message)
    except Exception as e:
        print("AI API Error:", e)
        ai_reply = "Sorry, there was a technical issue. Please try again later."

    return {
        "text": ai_reply,
        "cart_json": cart
    }

@app.get("/search")
async def search_products(keyword: str):
    products = await search_products_by_keyword(keyword)
    return products

@app.get("/variants/{product_id}")
async def product_variants(product_id: int):
    variants = await get_product_variants(product_id)
    return variants

@app.post("/add-to-cart")
async def add_to_cart(body: dict):
    cart = body.get("cart_json", [])
    variant_id = body.get("variant_id")
    quantity = body.get("quantity", 1)

    updated_cart = update_cart(cart, variant_id, quantity)
    checkout_link = generate_checkout_link(updated_cart)

    return {
        "cart_json": updated_cart,
        "checkout_link": checkout_link
    }
