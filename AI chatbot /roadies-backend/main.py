import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI
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

# --- EXPANDED MOCK PRODUCT DATA (15 PER CATEGORY) ---
MOCK_PRODUCTS = [
    # --- HELMETS (15 Items) ---
    {"id": 101, "name": "SMK Stellar Full Face (DOT/ECE)", "price": "4900.00", "link": "#", "image": "https://via.placeholder.com/150/e74c3c?text=SMK", "category_keyword": ["helmet", "full face", "smk"], "max_price_limit": 5000},
    {"id": 102, "name": "MT Thunder 4 Modular (ECE 22.06)", "price": "7500.00", "link": "#", "image": "https://via.placeholder.com/150/3498db?text=MT", "category_keyword": ["helmet", "modular", "mt"], "max_price_limit": 8000},
    {"id": 103, "name": "Axor Apex Carbon (DOT/ECE)", "price": "9800.00", "link": "#", "image": "https://via.placeholder.com/150/2c3e50?text=Axor", "category_keyword": ["helmet", "full face", "axor", "carbon"], "max_price_limit": 10000},
    {"id": 104, "name": "SMK Typhoon Flip-Up (ISI)", "price": "6100.00", "link": "#", "image": "https://via.placeholder.com/150/1abc9c?text=SMK", "category_keyword": ["helmet", "modular", "smk"], "max_price_limit": 7000},
    {"id": 105, "name": "MT Hummer Open Face (ISI)", "price": "2999.00", "link": "#", "image": "https://via.placeholder.com/150/f39c12?text=MT", "category_keyword": ["helmet", "open face", "mt"], "max_price_limit": 3000},
    {"id": 106, "name": "Axor Rage Dual Sport (ECE)", "price": "5500.00", "link": "#", "image": "https://via.placeholder.com/150/9b59b6?text=Axor", "category_keyword": ["helmet", "dual sport", "axor"], "max_price_limit": 6000},
    {"id": 107, "name": "SMK Glide Modular (Bluetooth Ready)", "price": "8200.00", "link": "#", "image": "https://via.placeholder.com/150/e67e22?text=SMK", "category_keyword": ["helmet", "modular", "smk"], "max_price_limit": 9000},
    {"id": 108, "name": "MT Revenge 2 Full Face (ECE)", "price": "6800.00", "link": "#", "image": "https://via.placeholder.com/150/7f8c8d?text=MT", "category_keyword": ["helmet", "full face", "mt"], "max_price_limit": 7000},
    {"id": 109, "name": "Axor Apex Full Face (Budget)", "price": "4100.00", "link": "#", "image": "https://via.placeholder.com/150/c0392b?text=Axor", "category_keyword": ["helmet", "full face", "axor"], "max_price_limit": 5000},
    {"id": 110, "name": "SMK Twister Full Face (Pinlock Included)", "price": "5800.00", "link": "#", "image": "https://via.placeholder.com/150/27ae60?text=SMK", "category_keyword": ["helmet", "full face", "smk"], "max_price_limit": 6000},
    {"id": 111, "name": "MT Optimus SV Modular (ECE)", "price": "7100.00", "link": "#", "image": "https://via.placeholder.com/150/34495e?text=MT", "category_keyword": ["helmet", "modular", "mt"], "max_price_limit": 8000},
    {"id": 112, "name": "Axor Jet Open Face (Cruiser)", "price": "2400.00", "link": "#", "image": "https://via.placeholder.com/150/95a5a6?text=Axor", "category_keyword": ["helmet", "open face", "axor"], "max_price_limit": 3000},
    {"id": 113, "name": "SMK Cooper Jet (ISI)", "price": "3100.00", "link": "#", "image": "https://via.placeholder.com/150/d35400?text=SMK", "category_keyword": ["helmet", "open face", "smk"], "max_price_limit": 4000},
    {"id": 114, "name": "MT Blade 2 Full Face (Race Fit)", "price": "5950.00", "link": "#", "image": "https://via.placeholder.com/150/f1c40f?text=MT", "category_keyword": ["helmet", "full face", "mt"], "max_price_limit": 6000},
    {"id": 115, "name": "Axor Venom Dual Visor (ECE)", "price": "6300.00", "link": "#", "image": "https://via.placeholder.com/150/8e44ad?text=Axor", "category_keyword": ["helmet", "full face", "axor"], "max_price_limit": 7000},

    # --- JACKETS (15 Items) ---
    {"id": 201, "name": "DSG Rynox Mesh (CE Level 2)", "price": "8500.00", "link": "#", "image": "https://via.placeholder.com/150/ff5733?text=Rynox", "category_keyword": ["jacket", "mesh", "dsg", "rynox"], "max_price_limit": 9000},
    {"id": 202, "name": "Raida Bolt Leather Jacket", "price": "12999.00", "link": "#", "image": "https://via.placeholder.com/150/000000?text=Raida", "category_keyword": ["jacket", "leather", "raida"], "max_price_limit": 13000},
    {"id": 203, "name": "Solace Urban Touring Textile", "price": "9200.00", "link": "#", "image": "https://via.placeholder.com/150/2980b9?text=Solace", "category_keyword": ["jacket", "textile", "solace"], "max_price_limit": 10000},
    {"id": 204, "name": "DSG Nexus Mesh (Budget)", "price": "5400.00", "link": "#", "image": "https://via.placeholder.com/150/7f8c8d?text=DSG", "category_keyword": ["jacket", "mesh", "dsg"], "max_price_limit": 6000},
    {"id": 205, "name": "Rynox Air GT 4 Textile (All Season)", "price": "11500.00", "link": "#", "image": "https://via.placeholder.com/150/f1c40f?text=Rynox", "category_keyword": ["jacket", "textile", "rynox"], "max_price_limit": 12000},
    {"id": 206, "name": "Raida Breeze Summer Mesh", "price": "6800.00", "link": "#", "image": "https://via.placeholder.com/150/c0392b?text=Raida", "category_keyword": ["jacket", "mesh", "raida"], "max_price_limit": 7000},
    {"id": 207, "name": "Solace Coolmax Textile (Waterproof)", "price": "10500.00", "link": "#", "image": "https://via.placeholder.com/150/e67e22?text=Solace", "category_keyword": ["jacket", "textile", "solace"], "max_price_limit": 11000},
    {"id": 208, "name": "DSG Rynox Rynox Air Mesh", "price": "7900.00", "link": "#", "image": "https://via.placeholder.com/150/16a085?text=Rynox", "category_keyword": ["jacket", "mesh", "dsg", "rynox"], "max_price_limit": 8000},
    {"id": 209, "name": "Raida Touring Adventure Jacket", "price": "15500.00", "link": "#", "image": "https://via.placeholder.com/150/8e44ad?text=Raida", "category_keyword": ["jacket", "textile", "raida", "adventure"], "max_price_limit": 16000},
    {"id": 210, "name": "Solace Fury Leather Race Jacket", "price": "18999.00", "link": "#", "image": "https://via.placeholder.com/150/2ecc71?text=Solace", "category_keyword": ["jacket", "leather", "solace"], "max_price_limit": 20000},
    {"id": 211, "name": "DSG Genesis Leather", "price": "16200.00", "link": "#", "image": "https://via.placeholder.com/150/34495e?text=DSG", "category_keyword": ["jacket", "leather", "dsg"], "max_price_limit": 17000},
    {"id": 212, "name": "Rynox Storm Evo Textile (Winter)", "price": "13800.00", "link": "#", "image": "https://via.placeholder.com/150/95a5a6?text=Rynox", "category_keyword": ["jacket", "textile", "rynox"], "max_price_limit": 14000},
    {"id": 213, "name": "Raida Aero Mesh Jacket", "price": "7100.00", "link": "#", "image": "https://via.placeholder.com/150/d35400?text=Raida", "category_keyword": ["jacket", "mesh", "raida"], "max_price_limit": 8000},
    {"id": 214, "name": "Solace Rain Pro Shell", "price": "4500.00", "link": "#", "image": "https://via.placeholder.com/150/f1c40f?text=Solace", "category_keyword": ["jacket", "textile"], "max_price_limit": 5000},
    {"id": 215, "name": "DSG Rynox Rynox Xterra Adventure", "price": "10200.00", "link": "#", "image": "https://via.placeholder.com/150/8e44ad?text=Rynox", "category_keyword": ["jacket", "textile", "dsg", "rynox"], "max_price_limit": 11000},

    # --- GLOVES (15 Items) ---
    {"id": 301, "name": "Raida Airwave Short Mesh", "price": "1999.00", "link": "#", "image": "https://via.placeholder.com/150/ff5733?text=Raida", "category_keyword": ["glove", "mesh", "textile", "raida", "airwave"], "max_price_limit": 2500},
    {"id": 302, "name": "Rynox Urban X Leather Gloves", "price": "3450.00", "link": "#", "image": "https://via.placeholder.com/150/000000?text=Rynox", "category_keyword": ["glove", "leather", "rynox"], "max_price_limit": 4000},
    {"id": 303, "name": "Solace Storm Full Gauntlet", "price": "4100.00", "link": "#", "image": "https://via.placeholder.com/150/2980b9?text=Solace", "category_keyword": ["glove", "textile", "solace"], "max_price_limit": 5000},
    {"id": 304, "name": "Raida Rover Leather Touring", "price": "2999.00", "link": "#", "image": "https://via.placeholder.com/150/7f8c8d?text=Raida", "category_keyword": ["glove", "leather", "raida"], "max_price_limit": 3500},
    {"id": 305, "name": "Rynox Hooligan Short Gloves", "price": "1800.00", "link": "#", "image": "https://via.placeholder.com/150/f1c40f?text=Rynox", "category_keyword": ["glove", "textile", "rynox"], "max_price_limit": 2000},
    {"id": 306, "name": "Solace Track Race Gloves", "price": "6500.00", "link": "#", "image": "https://via.placeholder.com/150/c0392b?text=Solace", "category_keyword": ["glove", "leather", "solace"], "max_price_limit": 7000},
    {"id": 307, "name": "Raida Trail Enduro Gloves", "price": "1550.00", "link": "#", "image": "https://via.placeholder.com/150/e67e22?text=Raida", "category_keyword": ["glove", "textile", "raida"], "max_price_limit": 2000},
    {"id": 308, "name": "Rynox Kombat EVO (Winter)", "price": "4999.00", "link": "#", "image": "https://via.placeholder.com/150/16a085?text=Rynox", "category_keyword": ["glove", "textile", "rynox"], "max_price_limit": 5500},
    {"id": 309, "name": "Solace Airtech V2 Mesh", "price": "2200.00", "link": "#", "image": "https://via.placeholder.com/150/8e44ad?text=Solace", "category_keyword": ["glove", "mesh", "solace"], "max_price_limit": 2500},
    {"id": 310, "name": "Raida Tornado Pro Race Gloves", "price": "5100.00", "link": "#", "image": "https://via.placeholder.com/150/2ecc71?text=Raida", "category_keyword": ["glove", "leather", "raida"], "max_price_limit": 6000},
    {"id": 311, "name": "Rynox Breeze Short Cuff", "price": "2600.00", "link": "#", "image": "https://via.placeholder.com/150/34495e?text=Rynox", "category_keyword": ["glove", "textile", "rynox"], "max_price_limit": 3000},
    {"id": 312, "name": "Solace Urban Short Leather", "price": "3999.00", "link": "#", "image": "https://via.placeholder.com/150/95a5a6?text=Solace", "category_keyword": ["glove", "leather", "solace"], "max_price_limit": 4500},
    {"id": 313, "name": "Raida Blaze Full Gauntlet", "price": "4500.00", "link": "#", "image": "https://via.placeholder.com/150/d35400?text=Raida", "category_keyword": ["glove", "leather", "raida"], "max_price_limit": 5000},
    {"id": 314, "name": "Rynox Stealth Waterproof", "price": "3100.00", "link": "#", "image": "https://via.placeholder.com/150/f1c40f?text=Rynox", "category_keyword": ["glove", "textile", "rynox"], "max_price_limit": 3500},
    {"id": 315, "name": "Solace Off-Road Grip", "price": "1650.00", "link": "#", "image": "https://via.placeholder.com/150/8e44ad?text=Solace", "category_keyword": ["glove", "textile", "solace"], "max_price_limit": 2000},
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
        if os.getenv("WOO_URL") and os.getenv("WOO_CONSUMER_KEY"):
            response = wcapi.get("products", params=params)
            
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
                # We limit the results from live API too for good UI practice
                return products[:5]
            
            logger.warning("WooCommerce returned empty data or failed search.")

    except Exception as e:
        logger.error(f"WooCommerce API failed, falling back to mock data: {e}")
        # Continue to Mock Data Fallback

    # ------------------ 2. MOCK DATA FALLBACK ------------------
    mock_results = []
    
    # Simple filtering on mock data
    # Ensure keyword is lower case for matching
    lower_keyword = category_keyword.lower() if category_keyword else None
    
    for item in MOCK_PRODUCTS:
        # Filter by keyword: checks if the requested keyword is found within any of the item's category_keywords
        keyword_match = not lower_keyword or any(lower_keyword in kw for kw in item["category_keyword"])
        
        # Filter by price: converts the item price to float for comparison
        # Use item['price'] as the source since 'max_price_limit' is only for internal mock reference
        price_match = not max_price or float(item["price"]) <= max_price
        
        if keyword_match and price_match:
            mock_results.append(Product(
                id=item['id'],
                name=item['name'],
                price=item['price'],
                link=item['link'],
                image=item['image']
            ))

    # Limit mock results to a maximum of 5 for display
    final_mock_results = mock_results[:5]
    logger.info(f"Returning {len(final_mock_results)} products from mock data.")
    return final_mock_results

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
    2. If products are listed above, recommend them briefly, highlighting safety features (DOT/ISI/ECE/CE Levels) or value.
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
