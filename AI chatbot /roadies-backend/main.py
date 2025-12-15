import os
import json
import logging
from typing import List, Optional, Dict, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from woocommerce import API # Kept for structure
import google.generativeai as genai 
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import asyncio # <--- ADDED: Needed for asynchronous sleep

# 1. Setup & Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Corrected the class name from GenerateContentConfig to GenerationConfig
# Use a slightly higher temperature for more natural, friendly language
GEMINI_CONFIG = genai.types.GenerationConfig(temperature=0.7) 

app = FastAPI(title="Roadies AI Chatbot")

# Enable CORS for the frontend widget
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WooCommerce Setup (API not used, but connection defined)
wcapi = API(
    url=os.getenv("WOO_URL"),
    consumer_key=os.getenv("WOO_CONSUMER_KEY"),
    consumer_secret=os.getenv("WOO_CONSUMER_SECRET"),
    version="wc/v3",
    timeout=10
)

# Gemini Setup (Configuration kept but calls are bypassed below)
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    logger.error(f"Gemini Configuration Failed: {e}")

# 2. Updated Data Models (No changes)
class QuickFilter(BaseModel):
    type: Literal["category", "price", "cert"]
    label: str
    query: str

class Product(BaseModel):
    id: int
    name: str
    price: float
    link: str
    image: str
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    category: str
    safety_certifications: List[str] = Field(default_factory=list)
    riding_styles: List[str] = Field(default_factory=list)
    stock_level: int = 10 
    insight: Optional[str] = None

class UserContext(BaseModel):
    bike_type: Optional[str] = None
    riding_style: Optional[str] = None 
    max_budget: Optional[float] = None
    cert_preference: Optional[str] = None 
    shortlist: List[int] = Field(default_factory=list)
    last_bike: Optional[str] = None 
    last_budget: Optional[float] = None
    
class IntentExtraction(BaseModel):
    # Added 'unreachable_error' for explicit signaling when mock search fails
    intent: Literal["product_search", "general_chat", "clarification_needed", "unreachable_error"]
    category: Optional[str] = None
    max_price: Optional[float] = None
    certifications: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    riding_style: Optional[str] = None
    budget_sensitivity: Literal["low", "medium", "high"] = "medium" 

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    persistent_bike: Optional[str] = None
    persistent_budget: Optional[float] = None

class ChatResponse(BaseModel):
    reply: str
    products: List[Product] = Field(default_factory=list)
    suggested_prompts: List[str] = Field(default_factory=list)
    context_updated: bool = False
    shortlist_count: int = 0
    match_confidence: Literal["strong", "medium", "approximate", "low"] = "low"
    quick_filters: List[QuickFilter] = Field(default_factory=list)


# 3. Product Abstraction Layer and Mock Data
class MockProductProvider(object):
    """Concrete implementation using the rich mock product list."""
    def __init__(self):
        self.mock_products_data = [
            # HELMETS (KEPT)
            { "id": 103, "name": "Carbon Apex Full Face (SNELL)", "price": 18500.00, "link": "#", "image": "https://via.placeholder.com/150/2c3e50?text=Helmet_3", 
              "category": "helmet", "safety_certifications": ["SNELL", "ECE"], "riding_styles": ["sport", "track"],
              "tags": ["full-face", "carbon-fiber", "race"], "description": "Ultimate lightweight race-spec helmet.", "stock_level": 5 },
            { "id": 102, "name": "Viper Modular (DOT/ISI)", "price": 7999.00, "link": "#", "image": "https://via.placeholder.com/150/3498db?text=Helmet_2", 
              "category": "helmet", "safety_certifications": ["DOT", "ISI"], "riding_styles": ["touring", "urban"],
              "tags": ["modular", "visor", "commuter"], "description": "Flexible modular design for city and travel.", "stock_level": 15 },
            { "id": 107, "name": "Classic Bullet Full Face (ISI)", "price": 4900.00, "link": "#", "image": "https://via.placeholder.com/150/e67e22?text=Helmet_7", 
              "category": "helmet", "safety_certifications": ["ISI"], "riding_styles": ["cruiser", "urban"],
              "tags": ["full-face", "budget", "classic"], "description": "Good safety for the budget-conscious classic rider.", "stock_level": 12 },
            # JACKETS (RE-INTRODUCED FOR DYNAMIC REPLY TESTING)
            { "id": 201, "name": "Ventura Mesh Riding Jacket (CE Level 2)", "price": 7200.00, "link": "#", "image": "https://via.placeholder.com/150/333333?text=Jacket_1", 
              "category": "jacket", "safety_certifications": ["CE Level 2"], "riding_styles": ["urban", "touring"],
              "tags": ["mesh", "textile", "summer"], "description": "High airflow jacket for hot weather.", "stock_level": 20 },
            { "id": 202, "name": "Ironclad Leather Tour Jacket", "price": 14500.00, "link": "#", "image": "https://via.placeholder.com/150/000000?text=Jacket_2", 
              "category": "jacket", "safety_certifications": ["CE Level 1"], "riding_styles": ["touring", "cruiser"],
              "tags": ["leather", "water-resistant", "winter"], "description": "Classic look with durable leather protection.", "stock_level": 8 },
            { "id": 204, "name": "Summer Breeze Mesh (Lightweight)", "price": 4500.00, "link": "#", "image": "https://via.placeholder.com/150/7f8c8d?text=Jacket_4", 
              "category": "jacket", "safety_certifications": ["CE Level 1"], "riding_styles": ["urban", "commuter"],
              "tags": ["mesh", "textile", "lightweight", "budget"], "description": "Basic, ultra-light mesh jacket for short commutes.", "stock_level": 30 },
            # GLOVES (KEPT)
            { "id": 305, "name": "Adv-Pro Gore-Tex Gloves", "price": 7500.00, "link": "#", "image": "https://via.placeholder.com/150/1abc9c?text=Gloves_5", 
              "category": "glove", "safety_certifications": ["CE Level 2"], "riding_styles": ["adventure", "touring"],
              "tags": ["gore-tex", "waterproof", "winter"], "description": "Premium waterproof gloves for serious adventure riders.", "stock_level": 6 },
            { "id": 302, "name": "Track Star Race Gloves (Level 2)", "price": 4999.00, "link": "#", "image": "https://via.placeholder.com/150/e74c3c?text=Gloves_2", 
              "category": "glove", "safety_certifications": ["CE Level 2"], "riding_styles": ["sport", "track"],
              "tags": ["leather", "gauntlet", "race"], "description": "Full gauntlet gloves for maximum track protection.", "stock_level": 10 },
        ]
        
    def get_products(self, category_keyword: Optional[str] = None) -> List[Product]:
        """Fetches all products, optionally filtered by a category keyword."""
        results = [Product(**p) for p in self.mock_products_data]
        if category_keyword:
            lower_keyword = category_keyword.lower()
            results = [p for p in results if p.category.lower() == lower_keyword]
        return results

product_provider = MockProductProvider()


# 4. Session Memory Storage and Shortlist Helpers (No changes)
SESSION_MEMORY: Dict[str, UserContext] = {}

def get_user_context(session_id: str) -> UserContext:
    """Retrieves context or initializes a new one."""
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = UserContext()
    return SESSION_MEMORY[session_id]

def update_user_context(session_id: str, new_intent: IntentExtraction) -> bool:
    """Updates the user context with new information from the latest intent."""
    current = get_user_context(session_id)
    updated = False
    
    # Update Riding Style
    if new_intent.riding_style and new_intent.riding_style.lower() != (current.riding_style.lower() if current.riding_style else None):
        current.riding_style = new_intent.riding_style
        updated = True
    
    # Update Max Budget (only if a stricter, lower budget is mentioned)
    if new_intent.max_price and (not current.max_budget or new_intent.max_price < current.max_budget):
        current.max_budget = new_intent.max_price
        updated = True
    
    # Update Cert Preference
    if new_intent.certifications and new_intent.certifications[0].lower() != (current.cert_preference.lower() if current.cert_preference else None):
        current.cert_preference = new_intent.certifications[0]
        updated = True
        
    return updated

def add_to_shortlist(session_id: str, product_id: int):
    context = get_user_context(session_id)
    if product_id not in context.shortlist:
        context.shortlist.append(product_id)

def clear_shortlist(session_id: str):
    context = get_user_context(session_id)
    context.shortlist = []
        
def get_shortlisted_products(session_id: str) -> List[Product]:
    context = get_user_context(session_id)
    shortlisted_ids = context.shortlist
    
    all_products = product_provider.get_products()
    return [p for p in all_products if p.id in shortlisted_ids]


# 5. Intent Analysis (Structured Output) - **Bypassed with Refined Logic**
async def analyze_intent(user_message: str, current_context: UserContext) -> IntentExtraction:
    """TEMPORARY BYPASS: Returns a smart mock intent to save API calls."""
    logger.warning("BYPASS: Returning mock intent data. (Refined for greetings)")
    lower_msg = user_message.lower()
    
    # Check for keywords indicating a generic greeting/chat
    if lower_msg in ["hi", "hello", "hey", "sup", "what's up", "bro"]:
        return IntentExtraction(intent="general_chat")
    
    category = None
    
    # Simple check for the type of query (product search)
    if "jacket" in lower_msg:
        category = "jacket"
    elif "glove" in lower_msg:
        category = "glove"
    elif "helmet" in lower_msg or "full face" in lower_msg or "modular" in lower_msg:
        category = "helmet"
    
    if category:
        # Return a product search intent
        return IntentExtraction(
            intent="product_search",
            category=category,
            max_price=8000.0 if "cheap" in lower_msg or "budget" in lower_msg or "7000" in lower_msg else 15000.0 if "15000" in lower_msg else None,
            riding_style="urban" if "city" in lower_msg or "commute" in lower_msg else "touring",
            certifications=["ECE"] if "ece" in lower_msg else []
        )
    else:
        # If no product keyword, treat it as general chat
        return IntentExtraction(intent="general_chat")


# 6. Scoring, Ranking, and Confidence (No changes)
def get_match_confidence(score: float) -> str:
    """Maps the product score to a confidence tag."""
    if score >= 20.0:
        return "strong"
    if score >= 10.0:
        return "medium"
    if score >= 5.0:
        return "approximate"
    return "low"

def score_product(product: Product, intent: IntentExtraction, context: UserContext) -> float:
    score = 0.0
    
    # 1. Category Match (Crucial)
    if intent.category and product.category.lower() == intent.category.lower():
        score += 10.0
    
    # 2. Budget Fit (Intent or Context)
    user_budget = intent.max_price or context.max_budget or float('inf')
    if product.price <= user_budget:
        score += 5.0
        if user_budget != float('inf') and product.price >= user_budget * 0.8:
            score += 2.0
    else:
        score -= 15.0 
        if intent.budget_sensitivity == "low" and product.price <= user_budget * 1.2:
             score += 5.0 

    # 3. Safety Certifications Match
    required_certs = set([c.lower() for c in intent.certifications] or [context.cert_preference.lower()] if context.cert_preference else [])
    if required_certs:
        product_certs = set([c.lower() for c in product.safety_certifications])
        if required_certs.intersection(product_certs):
            score += 8.0
        
    # 4. Feature and Style Match
    required_features = set([f.lower() for f in intent.features])
    product_tags = set([t.lower() for t in product.tags])
    match_count = len(required_features.intersection(product_tags))
    score += match_count * 2.0
    
    style = intent.riding_style or context.riding_style
    if style and style.lower() in [s.lower() for s in product.riding_styles]:
        score += 4.0
        
    # 5. Stock Level Penalty (Discourage low stock items)
    if product.stock_level < 3:
        score -= 5.0
    elif product.stock_level > 20:
        score += 1.0

    return score


def get_top_ranked_products(intent: IntentExtraction, context: UserContext, num_results: int = 3) -> List[Product]:
    
    # 1. Initial Filtering
    category = intent.category or "all"
    all_products = product_provider.get_products(category)
    
    # 2. Score all products
    scored_products = [
        (product, score_product(product, intent, context))
        for product in all_products
    ]
    
    # 3. Filter and sort
    scored_products = [item for item in scored_products if item[1] > 5.0]
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    # Return only the Product objects
    return [p[0] for p in scored_products[:num_results]]


# 7. AI Reply Generation (Tone & Micro-acknowledgements) - **Bypassed**

async def generate_product_insight(product: Product) -> str:
    """TEMPORARY BYPASS: Returns a fixed mock insight."""
    # Note: This is now only called if a product search was successfully triggered
    return f"Excellent choice for {product.riding_styles[0]}!"

async def generate_roadies_clarification(user_message: str, context: UserContext, intent: IntentExtraction):
    """TEMPORARY BYPASS: Returns a fixed clarification reply."""
    logger.warning("BYPASS: Returning mock clarification text.")
    return "Hold up, rider! That search was a little tricky. Can you specify if you need a helmet, jacket, or gloves first?"


async def generate_roadies_reply(user_message: str, products: List[Product], context: UserContext, intent: IntentExtraction):
    """TEMPORARY BYPASS: Returns a dynamic reply based on search results, category, and context."""
    logger.warning("BYPASS: Returning dynamic mock reply text based on product list.")

    if intent.intent == "unreachable_error":
        # THIS IS THE NEW ERROR MESSAGE
        return "I apologize, but Roadies is currently performing maintenance and the database is unreachable. Please try again in a few moments."
    
    elif products:
        top_product = products[0]
        category = top_product.category
        
        # 1. Start with an acknowledgment
        reply = f"Awesome find! I checked our inventory for the best {category} gear, and here's what we got. "
        
        # 2. Reference the top recommendation dynamically
        reply += f"Our top pick is the **{top_product.name}** at ₹{top_product.price:.0f}. "
        
        # 3. Add context-specific flair
        if "sport" in top_product.riding_styles or "track" in top_product.riding_styles:
            reply += "This one is pure speed—built for maximum track performance. "
        elif "touring" in top_product.riding_styles or "adventure" in top_product.riding_styles:
            reply += "This is a distance rider's dream, offering serious comfort and protection for long haul rides. "
        else: # urban/commuter
            reply += "Perfect for the daily grind, offering great protection without the bulk. "

        # 4. Mention a key feature or certification
        if top_product.safety_certifications:
             reply += f"It comes with **{top_product.safety_certifications[0]}** certification, so you know the safety is locked in. Check out the full list below!"
        elif top_product.tags:
             reply += f"It's a popular choice for its **{top_product.tags[0].replace('-', ' ')}** features. Check out the full list below!"
        else:
             reply += "See the additional options tailored to your needs below!"
        
        return reply
        
    elif intent.intent == "general_chat":
        return "Hey there, road warrior! Welcome to Roadies. What gear are you looking to crush the road with today—helmets, jackets, or gloves?"
        
    else:
        # Fallback if product search yielded no result but intent wasn't set to unreachable_error
        return f"Hold up, rider! I couldn't find a perfect match for that combination. Try searching for a different price range or safety certification."


# 8. Smart Follow-up Prompts & Quick Filters (Updated to clear prompts on error)

def get_quick_filters(intent: IntentExtraction) -> List[QuickFilter]:
    if intent.intent == "unreachable_error":
        return [] # No quick filters on error
        
    filters = []
    
    filters.append(QuickFilter(type="category", label="Helmets", query="Show me full-face helmets"))
    filters.append(QuickFilter(type="category", label="Jackets", query="What are the best riding jackets"))
    filters.append(QuickFilter(type="category", label="Gloves", query="Recommend touring gloves"))

    if intent.category:
        category = intent.category.capitalize()
        filters.append(QuickFilter(type="price", label=f"{category} under ₹7k", query=f"Show me {category} under 7000"))
    
    if intent.category in ["helmet", "jacket"]:
        filters.append(QuickFilter(type="cert", label="ECE Certified", query="Show me ECE certified gear"))
        
    return filters

def get_dynamic_prompts(intent: IntentExtraction, products: List[Product] = [], shortlist_count: int = 0) -> List[str]:
    if intent.intent == "unreachable_error":
        return [] # No suggested prompts on error

    prompts = []
    
    # A. Product-Specific Follow-ups
    if products:
        top_product_name = products[0].name
        
        prompts.append(f"Add '{top_product_name}' to my shortlist.")
        
        if len(products) > 1:
            prompts.append(f"Compare the '{products[0].name}' with the '{products[1].name}'") 
            
        prompts.append(f"Show similar {products[0].category} options")
    
    # B. Shortlist Prompts
    if shortlist_count > 0:
        prompts.append(f"View my shortlist ({shortlist_count})")
        if shortlist_count > 1:
            prompts.append("Clear my shortlist")
    
    # C. Clarification/General Fallbacks
    elif intent.intent == "clarification_needed":
        return ["My max budget is 10000", "I ride a sportbike", "Show me cheaper options"]
    
    elif not prompts:
        return ["Find helmets under ₹6 000", "Show jackets for touring", "Explain DOT vs ECE"]
        
    return prompts


# 9. Main Endpoint (Refactored for robustness and clear flow)
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_msg = request.message.strip()
    
    # 1. Initialization
    user_context = get_user_context(session_id)
    if request.persistent_bike and not user_context.last_bike:
        user_context.last_bike = request.persistent_bike
    if request.persistent_budget and not user_context.last_budget:
        user_context.last_budget = request.persistent_budget
    
    products_found: List[Product] = []
    reply_text: str = ""
    context_was_updated: bool = False
    top_score = 0.0

    try:
        # --- A. Intent Analysis & Initial Product Search ---
        # **This is now the bypassed version**
        intent_data = await analyze_intent(user_msg, user_context)

        if intent_data.intent == "product_search":
            products_found_base = get_top_ranked_products(intent_data, user_context, num_results=3)
            
            if products_found_base:
                # 1. Score & Context Update
                top_score = score_product(products_found_base[0], intent_data, user_context)
                context_was_updated = update_user_context(session_id, intent_data)
                
                # 2. Generate Insights 
                for p in products_found_base:
                    # **This is now the bypassed version**
                    p.insight = await generate_product_insight(p)
                products_found = products_found_base
            else:
                # ----------------------------------------------------
                # NEW LOGIC: If a product search fails to find anything,
                # we set the intent to 'unreachable_error' to trigger 
                # the specific error message and suppress all product suggestions.
                # ----------------------------------------------------
                intent_data.intent = "unreachable_error" 
        
        # --- B. Command Handling (Check after search, allows commands on results) ---
        lower_msg = user_msg.lower()
        shortlist_count = len(user_context.shortlist)
        
        if "add to my shortlist" in lower_msg and products_found:
            product_id_to_add = products_found[0].id
            add_to_shortlist(session_id, product_id_to_add)
            shortlist_count = len(user_context.shortlist)
            reply_text = f"Got it, rider! Added '{products_found[0].name}' to your pit crew list. You've got {shortlist_count} items now."
            # Immediately return command response
            await asyncio.sleep(2.5) # <--- ADDED DELAY
            return ChatResponse(reply=reply_text, suggested_prompts=get_dynamic_prompts(IntentExtraction(intent="general_chat"), shortlist_count=shortlist_count), shortlist_count=shortlist_count)
        
        if "view my shortlist" in lower_msg or "show my shortlist" in lower_msg:
            shortlist = get_shortlisted_products(session_id)
            if shortlist:
                reply_text = f"Here’s your pit crew list of {len(shortlist)} items! Let’s find the winner."
                await asyncio.sleep(2.5) # <--- ADDED DELAY
                return ChatResponse(reply=reply_text, products=shortlist, suggested_prompts=get_dynamic_prompts(IntentExtraction(intent="general_chat"), shortlist_count=len(shortlist)), shortlist_count=len(shortlist))
            else:
                reply_text = "Your shortlist is empty, mate. Let's find some killer gear!"
                await asyncio.sleep(2.5) # <--- ADDED DELAY
                return ChatResponse(reply=reply_text, suggested_prompts=get_dynamic_prompts(IntentExtraction(intent="general_chat")))

        if "clear my shortlist" in lower_msg:
            clear_shortlist(session_id)
            reply_text = "Shortlist cleared! Starting fresh on the road to new gear."
            await asyncio.sleep(2.5) # <--- ADDED DELAY
            return ChatResponse(reply=reply_text, suggested_prompts=get_dynamic_prompts(IntentExtraction(intent="general_chat")), shortlist_count=0)
            
        # --- C. Reply Generation (Only if no command was executed) ---
        if not reply_text:
            if intent_data.intent == "clarification_needed":
                # **This is now the bypassed version**
                reply_text = await generate_roadies_clarification(user_msg, user_context, intent_data)
                
            elif intent_data.intent == "general_chat" or intent_data.intent == "product_search" or intent_data.intent == "unreachable_error":
                # The generate_roadies_reply function now handles the 'unreachable_error'
                reply_text = await generate_roadies_reply(user_msg, products_found, user_context, intent_data)

    except Exception as e:
        logger.error(f"FATAL ERROR in chat_endpoint: {e}")
        # Return a clean 500 error to the client if the server crashes
        raise HTTPException(
            status_code=500,
            detail="Server experienced an unrecoverable error. Check backend logs."
        )

    # --- D. Final Assembly ---
    shortlist_count = len(user_context.shortlist)
    dynamic_prompts = get_dynamic_prompts(intent_data, products_found, shortlist_count)
    quick_filters = get_quick_filters(intent_data)
    
    # --- E. Introduce artificial lag for more natural response ---
    await asyncio.sleep(2.5) # <--- ADDED DELAY

    # F. Return the response
    return ChatResponse(
        reply=reply_text, 
        products=products_found, 
        suggested_prompts=dynamic_prompts,
        context_updated=context_was_updated,
        shortlist_count=shortlist_count,
        match_confidence=get_match_confidence(top_score),
        quick_filters=quick_filters
    )
