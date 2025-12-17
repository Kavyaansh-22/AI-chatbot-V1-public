import os
import json
import logging
import re
import random
from typing import List, Optional, Dict, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from woocommerce import API 
from dotenv import load_dotenv
import asyncio

# 1. Setup & Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Roadies AI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Data Models
class Product(BaseModel):
    id: int
    name: str
    price: float
    brand: str
    link: str
    image: str
    category: str
    safety_certifications: List[str] = Field(default_factory=list)
    riding_styles: List[str] = Field(default_factory=list)
    stock_level: int = 10 
    insight: Optional[str] = None
    safety_score: Optional[int] = None 

class UserContext(BaseModel):
    last_bike: Optional[str] = None
    max_budget: Optional[float] = None
    shortlist: List[int] = Field(default_factory=list)

class IntentExtraction(BaseModel):
    intent: Literal["product_search", "general_chat", "unreachable_error", "shortlist_op", "compare"]
    category: Optional[str] = None
    brand: Optional[str] = None
    max_price: Optional[float] = None
    extracted_bike: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    persistent_bike: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    products: List[Product] = Field(default_factory=list)
    suggested_prompts: List[str] = Field(default_factory=list)
    shortlist_count: int = 0
    match_confidence: Literal["strong", "medium", "approximate", "low"] = "low"

# 3. Dynamic Response Bank
class ResponseBank:
    # Opening lines based on bike/category
    OPENERS = [
        "I've handpicked these {cat} options for your {bike}.",
        "Check out these top-rated {cat} picks for your {bike}!",
        "Based on your {bike}, here are the best {cat} choices I found.",
        "Here's some solid {cat} that fits your {bike} perfectly.",
        "Looking at your {bike}, these {cat} options offer the best balance of style and protection."
    ]

    # Closing lines to replace "I prioritized items with high safety rating"
    CLOSERS_SPORT = [
        "I focused on gear with high-speed aerodynamics and impact protection.",
        "These were chosen specifically for the aggressive stance of your bike.",
        "Safety at high lean angles was my main priority here.",
        "I picked these for their superior track-inspired safety standards."
    ]
    
    CLOSERS_GENERAL = [
        "I've made sure these meet the latest safety certifications for your peace of mind.",
        "These picks prioritize maximum protection without compromising on comfort.",
        "I've filtered these to ensure you're getting the best impact resistance available.",
        "Protection is key, so I've highlighted the most rugged options here.",
        "These items have some of the highest safety ratings in our current inventory."
    ]

    @classmethod
    def get_reply(cls, category: str, bike: str, is_sport: bool) -> str:
        opener = random.choice(cls.OPENERS).format(cat=category, bike=bike)
        closers = cls.CLOSERS_SPORT if is_sport else cls.CLOSERS_GENERAL
        return f"{opener} {random.choice(closers)}"

# 4. Helpers & Ranking (Logic Maintained)
def calculate_safety_score(product: Product) -> int:
    score = 5 
    certs = [c.lower() for c in product.safety_certifications]
    if "ece 22.06" in certs: score += 4
    elif "ece" in certs: score += 3
    if "ce level 2" in certs: score += 4
    elif "ce level 1" in certs: score += 2
    if "snell" in certs: score += 5
    return min(score, 10)

def get_user_context(session_id: str) -> UserContext:
    if session_id not in SESSION_MEMORY: SESSION_MEMORY[session_id] = UserContext()
    return SESSION_MEMORY[session_id]

async def analyze_intent(user_message: str) -> IntentExtraction:
    msg = user_message.lower()
    bike_match = re.search(r'(?:for|my|ride|on)\s+([a-z0-9]+\s+[a-z0-9]+\s*[a-z0-9]*)', msg)
    extracted_bike = bike_match.group(1).strip() if bike_match else None

    if "compare" in msg: return IntentExtraction(intent="compare")
    if "shortlist" in msg: return IntentExtraction(intent="shortlist_op")

    category = None
    if "jacket" in msg: category = "jacket"
    elif "glove" in msg: category = "gloves"
    elif "helmet" in msg: category = "helmet"
    elif "boot" in msg or "shoe" in msg: category = "boots"
    
    if category or extracted_bike or "gear" in msg:
        return IntentExtraction(intent="product_search", category=category, extracted_bike=extracted_bike)
    
    return IntentExtraction(intent="general_chat")

def get_style_from_bike(bike_name: str) -> str:
    bike = bike_name.lower()
    if any(x in bike for x in ["rc", "ninja", "r15", "sport", "duke", "rr", "rs457", "aprilia", "triumph"]): return "sport"
    return "touring"

def get_dynamic_prompts(intent: IntentExtraction, shortlist_count: int) -> List[str]:
    prompts = []
    if shortlist_count > 1: prompts.append("Compare items")
    current_cat = intent.category.lower() if intent.category else ""
    if current_cat != "helmet": prompts.append("Show me helmets")
    if current_cat != "boots": prompts.append("Show me riding boots")
    if current_cat != "jacket": prompts.append("Best riding jackets")
    return prompts[:3]

# 5. Data & Logic
class MockProductProvider:
    def __init__(self):
        img = "https://via.placeholder.com/150/00BFA5?text="
        self.mock_products_data = [
            { "id": 1, "brand": "Axor", "name": "Axor Apex Forged Carbon", "price": 11996, "category": "helmet", "safety_certifications": ["ECE 22.06", "DOT"], "riding_styles": ["sport"], "image": f"{img}Axor+Apex", "link": "#" },
            { "id": 11, "brand": "AGV", "name": "AGV K1 S Rossi", "price": 28000, "category": "helmet", "safety_certifications": ["ECE 22.06"], "riding_styles": ["sport"], "image": f"{img}AGV+K1S", "link": "#" },
            { "id": 50, "brand": "Raida", "name": "Raida Tourer Boots", "price": 8500, "category": "boots", "safety_certifications": ["CE Level 2"], "riding_styles": ["touring", "adventure"], "image": f"{img}Raida+Boots", "link": "#" },
            { "id": 51, "brand": "Sidi", "name": "Sidi Rex Racing Boots", "price": 38000, "category": "boots", "safety_certifications": ["CE Level 2", "TPU sliders"], "riding_styles": ["sport"], "image": f"{img}Sidi+Rex", "link": "#" },
            { "id": 21, "brand": "DSG", "name": "DSG Race Pro Sport Jacket", "price": 16500, "category": "jacket", "safety_certifications": ["CE Level 2 Protectors"], "riding_styles": ["sport"], "image": f"{img}DSG+Race", "link": "#" },
        ]
    def get_products(self): return [Product(**p) for p in self.mock_products_data]

product_provider = MockProductProvider()
SESSION_MEMORY: Dict[str, UserContext] = {}

def get_top_ranked_products(intent: IntentExtraction, context: UserContext):
    all_products = product_provider.get_products()
    filtered = []
    bike_to_use = intent.extracted_bike or context.last_bike
    target_style = get_style_from_bike(bike_to_use) if bike_to_use else None
    for p in all_products:
        if intent.category and p.category != intent.category: continue
        score = 10.0
        p.safety_score = calculate_safety_score(p)
        if target_style and target_style in p.riding_styles:
            score += 20.0
            p.insight = f"High performance {p.category} matched to your {bike_to_use}."
        else:
            p.insight = f"Reliable {p.category} with {', '.join(p.safety_certifications)}."
        filtered.append((p, score))
    filtered.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in filtered[:3]]

# 6. Main Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_msg = request.message.strip()
    context = get_user_context(session_id)
    intent_data = await analyze_intent(user_msg)
    
    if intent_data.extracted_bike: context.last_bike = intent_data.extracted_bike

    products_found = []
    reply = ""

    if intent_data.intent == "product_search":
        products_found = get_top_ranked_products(intent_data, context)
        bike_name = context.last_bike if context.last_bike else "your ride"
        is_sport = get_style_from_bike(bike_name) == "sport"
        
        if products_found:
            cat_label = intent_data.category if intent_data.category else "riding gear"
            # Use the Random Response Generator
            reply = ResponseBank.get_reply(cat_label, bike_name, is_sport)
        else:
            reply = f"I couldn't find any {intent_data.category or 'gear'} in stock right now. Try another category?"

    elif intent_data.intent == "compare":
        all_p = product_provider.get_products()
        products_found = [p for p in all_p if p.id in context.shortlist]
        reply = "Here's how your shortlisted items stack up in terms of safety."

    else:
        reply = "Welcome to Roadies! I'm here to help you gear up. What are you looking for today?"

    shortlist_count = len(context.shortlist)
    dynamic_prompts = get_dynamic_prompts(intent_data, shortlist_count)

    await asyncio.sleep(2)
    return ChatResponse(
        reply=reply,
        products=products_found,
        shortlist_count=shortlist_count,
        match_confidence="strong" if products_found else "low",
        suggested_prompts=dynamic_prompts
    )
