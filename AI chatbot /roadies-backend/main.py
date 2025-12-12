import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from woocommerce import API
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Setup & Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Roadies AI Chatbot")

# Enable CORS for the frontend widget
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WooCommerce Setup
wcapi = API(
    url=os.getenv("WOO_URL"),
    consumer_key=os.getenv("WOO_CONSUMER_KEY"),
    consumer_secret=os.getenv("WOO_CONSUMER_SECRET"),
    version="wc/v3",
    timeout=10
)

# Gemini Setup
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# --- MOCK PRODUCT DATA (For local testing/fallback) ---
MOCK_PRODUCTS = [
    {
        "id": 101,
        "name": "Storm Rider Full Face Helmet (ECE/DOT)",
        "price": "5500.00",
        "link": "#",
        "image": "https://via.placeholder.com/150/e74c3c/ffffff?text=Helmet",
        "category_keyword": ["helmet", "full face"],
        "max_price_limit": 6000
    },
    {
        "id": 102,
        "name": "Ventura Mesh Riding Jacket (Level 2)",
        "price": "7200.00",
        "link": "#",
        "image": "https://via.placeholder.com/150/333333/ffffff?text=Jacket",
        "category_keyword": ["jacket", "mesh"],
        "max_price_limit": 8000
    },
    {
        "id": 103,
        "name": "RoadHawk Touring Gloves (Leather)",
        "price": "2800.00",
        "link": "#",
        "image": "https://via.placeholder.com/150/f39c12/ffffff?text=Gloves",
        "category_keyword": ["glove", "leather"],
        "max_price_limit": 3000
    }
]


# 2. Data Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class Product(BaseModel):
    id: int
    name: str
    price: str
    link: str
    image: str

class ChatResponse(BaseModel):
    reply: str
    products: List[Product] = []

# 3. Helper Functions

def get_woo_products(category_keyword: str = None, max_price: int = None):
    """
    Fetches products from WooCommerce or uses mock data as fallback.
    """
    # ------------------ 1. TRY REAL WOOCOMMERCE API ------------------
    params = {
        "per_page": 5,
        "status": "publish",
        "search": category_keyword if category_keyword else ""
    }
    
    if max_price:
        params["max_price"] = str(max_price)

    try:
        # Check if basic Woo config is present before calling
        if os.getenv("WOO_URL") and os.getenv("WOO_CONSUMER_KEY"):
            response = wcapi.get("products", params=params)
            
            # If successful and products exist, process and return
            if response.status_code == 200 and response.json():
                data = response.json()
                products = []
                for item in data:
                    img_src = item['images'][0]['src'] if item['images'] else "https://via.placeholder.com/150"
                    products.append(Product(
                        id=item['id'],
                        name=item['name'],
                        price=item['price'] or "N/A",
                        link=item['permalink'],
                        image=img_src
                    ))
                logger.info("Successfully fetched products from WooCommerce.")
                return products
            
            # If status is 200 but no products, we still fall back to mock data 
            # or return an empty list if using live data is critical.
            logger.warning("WooCommerce returned empty data or failed search.")

    except Exception as e:
        logger.error(f"WooCommerce API failed, falling back to mock data: {e}")
        # Continue to Mock Data Fallback

    # ------------------ 2. MOCK DATA FALLBACK ------------------
    mock_results = []
    
    # Simple filtering on mock data
    for item in MOCK_PRODUCTS:
        # Filter by keyword
        keyword_match = not category_keyword or any(kw in category_keyword.lower() for kw in item["category_keyword"])
        
        # Filter by price
        price_match = not max_price or float(item["price"]) <= max_price
        
        if keyword_match and price_match:
            mock_results.append(Product(
                id=item['id'],
                name=item['name'],
                price=item['price'],
                link=item['link'],
                image=item['image']
            ))

    logger.info(f"Returning {len(mock_results)} products from mock data.")
    return mock_results

async def analyze_intent(user_message: str):
    """
    Asks Gemini to classify the user's intent and extract search parameters.
    Returns JSON.
    """
    prompt = f"""
    You are the brain of a biking gear store chatbot. Analyze the user query.
    Return ONLY a raw JSON object (no markdown, no backticks) with these keys:
    - "intent": "product_search" or "general_chat"
    - "keyword": (string) main product keyword (e.g., "helmet", "jacket") or null.
    - "max_price": (integer) maximum budget if mentioned, else null.
    
    User Query: "{user_message}"
    """
    try:
        response = model.generate_content(prompt)
        # Clean response to ensure valid JSON
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        logger.error(f"Intent Error: {e}")
        return {"intent": "general_chat"}

async def generate_roadies_reply(user_message: str, product_context: List[Product] = []):
    """
    Generates the final natural language response based on products found (or not).
    """
    
    product_text = ""
    if product_context:
        product_text = "Here is the product data I found in the store:\n"
        for p in product_context:
            product_text += f"- {p.name}: ₹{p.price}\n"
    else:
        product_text = "No specific matching products found in the current inventory."

    system_prompt = f"""
    You are Roadies, an expert biker gear advisor. 
    Tone: Professional, safety-conscious, enthusiastic about biking.
    
    Context:
    {product_text}
    
    User Query: "{user_message}"
    
    Instructions:
    1. Answer the user's question directly.
    2. If products are listed above, recommend them briefly, highlighting safety features (DOT/ISI/ECE) or value.
    3. If no products were found but the user asked for gear, apologize and suggest general advice on what to look for.
    4. Keep it concise (under 3 sentences).
    """
    
    response = model.generate_content(system_prompt)
    return response.text

# 4. Main Endpoint

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_msg = request.message
    
    # Step A: Analyze Intent
    intent_data = await analyze_intent(user_msg)
    logger.info(f"Intent Data: {intent_data}")
    
    products_found = []
    
    # Step B: Fetch Products if needed
    if intent_data.get("intent") == "product_search":
        keyword = intent_data.get("keyword")
        max_price = intent_data.get("max_price")
        products_found = get_woo_products(keyword, max_price)
    
    # Step C: Generate AI Reply
    reply_text = await generate_roadies_reply(user_msg, products_found)
    
    return ChatResponse(reply=reply_text, products=products_found)

# To run: uvicorn main:app --reload