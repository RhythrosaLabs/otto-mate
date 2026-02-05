"""
Printify Integration Tools
==========================

Tools for managing products on Printify.
Printify automatically syncs to connected Shopify stores - no manual sync needed.
"""

import logging
import aiohttp
from typing import Optional, Dict, Any, List
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# COMPREHENSIVE PRINTIFY PRODUCT CATALOG
# ═══════════════════════════════════════════════════════════════════
# Maps product type keywords to blueprint_id and print_provider_id
# This enables Otto to create any product type by name

PRINTIFY_PRODUCT_CATALOG = {
    # ── T-Shirts & Tops ──
    "t-shirt": {"blueprint_id": 6, "print_provider_id": 99, "name": "Unisex Heavy Cotton Tee"},
    "tshirt": {"blueprint_id": 6, "print_provider_id": 99, "name": "Unisex Heavy Cotton Tee"},
    "tee": {"blueprint_id": 6, "print_provider_id": 99, "name": "Unisex Heavy Cotton Tee"},
    "shirt": {"blueprint_id": 6, "print_provider_id": 99, "name": "Unisex Heavy Cotton Tee"},
    "softstyle": {"blueprint_id": 145, "print_provider_id": 99, "name": "Unisex Softstyle T-Shirt"},
    "tank top": {"blueprint_id": 42, "print_provider_id": 99, "name": "Unisex Tank Top"},
    "tank": {"blueprint_id": 42, "print_provider_id": 99, "name": "Unisex Tank Top"},
    "long sleeve": {"blueprint_id": 10, "print_provider_id": 99, "name": "Unisex Long Sleeve Tee"},
    "longsleeve": {"blueprint_id": 10, "print_provider_id": 99, "name": "Unisex Long Sleeve Tee"},
    "crop top": {"blueprint_id": 308, "print_provider_id": 99, "name": "Women's Crop Top"},
    "v-neck": {"blueprint_id": 161, "print_provider_id": 99, "name": "Unisex V-Neck Tee"},
    "vneck": {"blueprint_id": 161, "print_provider_id": 99, "name": "Unisex V-Neck Tee"},
    
    # ── Hoodies & Sweatshirts ──
    "hoodie": {"blueprint_id": 380, "print_provider_id": 99, "name": "Unisex Hoodie"},
    "sweatshirt": {"blueprint_id": 77, "print_provider_id": 99, "name": "Unisex Sweatshirt"},
    "crewneck": {"blueprint_id": 77, "print_provider_id": 99, "name": "Unisex Crewneck Sweatshirt"},
    "zip hoodie": {"blueprint_id": 381, "print_provider_id": 99, "name": "Unisex Zip Hoodie"},
    
    # ── Mugs & Drinkware ──
    "mug": {"blueprint_id": 12, "print_provider_id": 28, "name": "White Ceramic Mug 11oz"},
    "coffee mug": {"blueprint_id": 12, "print_provider_id": 28, "name": "White Ceramic Mug 11oz"},
    "mug 15oz": {"blueprint_id": 440, "print_provider_id": 28, "name": "White Ceramic Mug 15oz"},
    "black mug": {"blueprint_id": 443, "print_provider_id": 28, "name": "Black Ceramic Mug 11oz"},
    "travel mug": {"blueprint_id": 471, "print_provider_id": 56, "name": "Stainless Steel Travel Mug"},
    "tumbler": {"blueprint_id": 496, "print_provider_id": 56, "name": "Stainless Steel Tumbler 20oz"},
    "water bottle": {"blueprint_id": 506, "print_provider_id": 56, "name": "Stainless Steel Water Bottle"},
    
    # ── Phone Cases ──
    "phone case": {"blueprint_id": 26, "print_provider_id": 27, "name": "iPhone Tough Case"},
    "iphone case": {"blueprint_id": 26, "print_provider_id": 27, "name": "iPhone Tough Case"},
    "samsung case": {"blueprint_id": 31, "print_provider_id": 27, "name": "Samsung Galaxy Case"},
    "phone case slim": {"blueprint_id": 27, "print_provider_id": 27, "name": "iPhone Slim Case"},
    "clear phone case": {"blueprint_id": 28, "print_provider_id": 27, "name": "iPhone Clear Case"},
    
    # ── Home & Living ──
    "pillow": {"blueprint_id": 65, "print_provider_id": 56, "name": "Throw Pillow"},
    "throw pillow": {"blueprint_id": 65, "print_provider_id": 56, "name": "Throw Pillow"},
    "blanket": {"blueprint_id": 505, "print_provider_id": 56, "name": "Fleece Blanket"},
    "fleece blanket": {"blueprint_id": 505, "print_provider_id": 56, "name": "Fleece Blanket"},
    "shower curtain": {"blueprint_id": 476, "print_provider_id": 56, "name": "Shower Curtain"},
    "doormat": {"blueprint_id": 538, "print_provider_id": 56, "name": "Welcome Doormat"},
    "mousepad": {"blueprint_id": 389, "print_provider_id": 56, "name": "Mouse Pad"},
    "mouse pad": {"blueprint_id": 389, "print_provider_id": 56, "name": "Mouse Pad"},
    "coaster": {"blueprint_id": 548, "print_provider_id": 56, "name": "Coaster Set"},
    "clock": {"blueprint_id": 462, "print_provider_id": 56, "name": "Wall Clock"},
    "wall clock": {"blueprint_id": 462, "print_provider_id": 56, "name": "Wall Clock"},
    "acrylic clock": {"blueprint_id": 462, "print_provider_id": 56, "name": "Wall Clock"},
    "cutting board": {"blueprint_id": 492, "print_provider_id": 56, "name": "Cutting Board"},
    "towel": {"blueprint_id": 507, "print_provider_id": 56, "name": "Beach Towel"},
    "beach towel": {"blueprint_id": 507, "print_provider_id": 56, "name": "Beach Towel"},
    
    # ── Wall Art & Posters ──
    "canvas": {"blueprint_id": 384, "print_provider_id": 56, "name": "Canvas Print"},
    "canvas print": {"blueprint_id": 384, "print_provider_id": 56, "name": "Canvas Print"},
    "poster": {"blueprint_id": 38, "print_provider_id": 56, "name": "Premium Poster"},
    "framed poster": {"blueprint_id": 394, "print_provider_id": 56, "name": "Framed Poster"},
    "framed art": {"blueprint_id": 394, "print_provider_id": 56, "name": "Framed Poster"},
    "framed print": {"blueprint_id": 394, "print_provider_id": 56, "name": "Framed Poster"},
    "framed canvas": {"blueprint_id": 384, "print_provider_id": 56, "name": "Canvas Print"},
    "wall art": {"blueprint_id": 384, "print_provider_id": 56, "name": "Canvas Print"},
    "art print": {"blueprint_id": 38, "print_provider_id": 56, "name": "Premium Poster"},
    "metal print": {"blueprint_id": 403, "print_provider_id": 56, "name": "Metal Print"},
    "acrylic print": {"blueprint_id": 401, "print_provider_id": 56, "name": "Acrylic Print"},
    "wood print": {"blueprint_id": 408, "print_provider_id": 56, "name": "Wood Print"},
    
    # ── Bags & Accessories ──
    # NOTE: Compound terms MUST come first to avoid partial matching issues
    "canvas tote bag": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Canvas Tote Bag"},
    "canvas tote": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Canvas Tote Bag"},
    "cotton tote bag": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Canvas Tote Bag"},
    "cotton tote": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Canvas Tote Bag"},
    "shopping tote": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Canvas Tote Bag"},
    "reusable bag": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Canvas Tote Bag"},
    "tote bag": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Tote Bag"},
    "tote": {"blueprint_id": 36, "print_provider_id": 99, "name": "Cotton Tote Bag"},
    "backpack": {"blueprint_id": 490, "print_provider_id": 56, "name": "Backpack"},
    "fanny pack": {"blueprint_id": 500, "print_provider_id": 56, "name": "Fanny Pack"},
    "crossbody bag": {"blueprint_id": 502, "print_provider_id": 56, "name": "Crossbody Bag"},
    "drawstring bag": {"blueprint_id": 503, "print_provider_id": 56, "name": "Drawstring Bag"},
    
    # ── Stationery & Office ──
    "notebook": {"blueprint_id": 470, "print_provider_id": 56, "name": "Spiral Notebook"},
    "journal": {"blueprint_id": 630, "print_provider_id": 56, "name": "Hardcover Journal"},
    "hardcover journal": {"blueprint_id": 630, "print_provider_id": 56, "name": "Hardcover Journal"},
    "spiral notebook": {"blueprint_id": 470, "print_provider_id": 56, "name": "Spiral Notebook"},
    "sticker": {"blueprint_id": 545, "print_provider_id": 56, "name": "Kiss-Cut Stickers"},
    "stickers": {"blueprint_id": 545, "print_provider_id": 56, "name": "Kiss-Cut Stickers"},
    "magnet": {"blueprint_id": 556, "print_provider_id": 56, "name": "Refrigerator Magnet"},
    "greeting card": {"blueprint_id": 478, "print_provider_id": 56, "name": "Greeting Card"},
    "postcard": {"blueprint_id": 479, "print_provider_id": 56, "name": "Postcard"},
    
    # ── Apparel Accessories ──
    "hat": {"blueprint_id": 373, "print_provider_id": 44, "name": "Dad Hat"},
    "cap": {"blueprint_id": 373, "print_provider_id": 44, "name": "Dad Hat"},
    "dad hat": {"blueprint_id": 373, "print_provider_id": 44, "name": "Dad Hat"},
    "beanie": {"blueprint_id": 452, "print_provider_id": 44, "name": "Knit Beanie"},
    "knit beanie": {"blueprint_id": 452, "print_provider_id": 44, "name": "Knit Beanie"},
    "winter hat": {"blueprint_id": 452, "print_provider_id": 44, "name": "Knit Beanie"},
    "socks": {"blueprint_id": 488, "print_provider_id": 56, "name": "Crew Socks"},
    "crew socks": {"blueprint_id": 488, "print_provider_id": 56, "name": "Crew Socks"},
    "flip flops": {"blueprint_id": 510, "print_provider_id": 56, "name": "Flip Flops"},
    "apron": {"blueprint_id": 474, "print_provider_id": 56, "name": "Kitchen Apron"},
    "kitchen apron": {"blueprint_id": 474, "print_provider_id": 56, "name": "Kitchen Apron"},
    "face mask": {"blueprint_id": 532, "print_provider_id": 99, "name": "Face Mask"},
    "leggings": {"blueprint_id": 459, "print_provider_id": 56, "name": "Leggings"},
    "yoga leggings": {"blueprint_id": 459, "print_provider_id": 56, "name": "Leggings"},
    
    # ── Novelty & Gifts ──
    "puzzle": {"blueprint_id": 520, "print_provider_id": 56, "name": "Jigsaw Puzzle"},
    "jigsaw puzzle": {"blueprint_id": 520, "print_provider_id": 56, "name": "Jigsaw Puzzle"},
    "ornament": {"blueprint_id": 554, "print_provider_id": 56, "name": "Christmas Ornament"},
    "christmas ornament": {"blueprint_id": 554, "print_provider_id": 56, "name": "Christmas Ornament"},
    "playing cards": {"blueprint_id": 560, "print_provider_id": 56, "name": "Playing Cards"},
    "cards": {"blueprint_id": 560, "print_provider_id": 56, "name": "Playing Cards"},
    "flag": {"blueprint_id": 534, "print_provider_id": 56, "name": "Garden Flag"},
    "garden flag": {"blueprint_id": 534, "print_provider_id": 56, "name": "Garden Flag"},
    "yard flag": {"blueprint_id": 534, "print_provider_id": 56, "name": "Garden Flag"},
    
    # ── Pet Products ──
    "pet bandana": {"blueprint_id": 540, "print_provider_id": 56, "name": "Pet Bandana"},
    "dog bandana": {"blueprint_id": 540, "print_provider_id": 56, "name": "Pet Bandana"},
    "pet bowl": {"blueprint_id": 544, "print_provider_id": 56, "name": "Pet Bowl"},
    "dog bowl": {"blueprint_id": 544, "print_provider_id": 56, "name": "Pet Bowl"},
    
    # ── Kids & Baby ──
    "baby onesie": {"blueprint_id": 168, "print_provider_id": 99, "name": "Baby Onesie"},
    "onesie": {"blueprint_id": 168, "print_provider_id": 99, "name": "Baby Onesie"},
    "kids t-shirt": {"blueprint_id": 314, "print_provider_id": 99, "name": "Kids T-Shirt"},
    "kids tee": {"blueprint_id": 314, "print_provider_id": 99, "name": "Kids T-Shirt"},
    "baby bib": {"blueprint_id": 170, "print_provider_id": 99, "name": "Baby Bib"},
}

# ═══════════════════════════════════════════════════════════════════
# SMART PRODUCT DETECTION - Synonyms and Natural Language Patterns
# ═══════════════════════════════════════════════════════════════════

# Map common words/phrases to canonical product types
PRODUCT_SYNONYMS = {
    # Drinkware synonyms
    "cup": "mug",
    "coffee cup": "mug",
    "tea cup": "mug",
    "drink": "mug",
    "beverage": "mug",
    "11oz": "mug",
    "15oz": "mug 15oz",
    "thermos": "travel mug",
    "insulated": "tumbler",
    "bottle": "water bottle",
    
    # Apparel synonyms
    "top": "t-shirt",
    "clothing": "t-shirt",
    "apparel": "t-shirt",
    "clothes": "t-shirt",
    "wear": "t-shirt",
    "garment": "t-shirt",
    "outfit": "t-shirt",
    "sweater": "sweatshirt",
    "pullover": "hoodie",
    "jumper": "hoodie",
    "sleeveless": "tank top",
    "muscle": "tank top",
    
    # Bags synonyms - ONLY specific matches, not generic "bag"
    "shopping bag": "tote bag",
    "grocery bag": "tote bag",
    "eco bag": "tote bag",
    "market bag": "tote bag",
    "purse": "tote bag",
    "bookbag": "backpack",
    "rucksack": "backpack",
    "gym bag": "drawstring bag",
    "sports bag": "drawstring bag",
    
    # Home synonyms
    "cushion": "pillow",
    "throw": "blanket",
    "quilt": "blanket",
    "art print": "framed poster",
    "wall art": "canvas",
    "wall print": "poster",
    "picture": "canvas",
    "framed": "framed poster",
    "framed art": "framed poster",
    "frame": "framed poster",
    "fine art": "canvas",
    "gallery art": "canvas",
    "painting": "canvas",
    "artwork": "canvas",
    "decoration": "canvas",
    "decor": "canvas",
    "mat": "mousepad",
    "desk pad": "mousepad",
    "rug": "doormat",
    "welcome mat": "doormat",
    
    # Stationery synonyms  
    "notepad": "notebook",
    "diary": "journal",
    "planner": "journal",
    "label": "sticker",
    "decal": "sticker",
    "birthday card": "greeting card",
    "thank you card": "greeting card",
    "holiday card": "greeting card",
    "fridge magnet": "magnet",
    "refrigerator magnet": "magnet",
    
    # Phone synonyms - specific, not generic "case" or "cover"
    "iphone": "iphone case",
    "samsung": "samsung case",
    "galaxy": "samsung case",
    "android case": "samsung case",
    "mobile case": "phone case",
    "cell phone case": "phone case",
    "smartphone case": "phone case",
    
    # Accessories synonyms
    "baseball cap": "cap",
    "snapback": "cap",
    "trucker hat": "cap",
    "winter hat": "beanie",
    "knit hat": "beanie",
    "sock": "socks",
    "footwear": "socks",
    "sandal": "flip flops",
    "thong": "flip flops",
    "cooking apron": "apron",
    "kitchen apron": "apron",
    "chef apron": "apron",
    
    # Pet synonyms - specific, not generic "dog" or "pet"
    "dog bandana": "pet bandana",
    "cat bandana": "pet bandana",
    "pet scarf": "pet bandana",
    "puppy bandana": "pet bandana",
    "kitten bandana": "pet bandana",
    "dog accessory": "pet bandana",
    "pet accessory": "pet bandana",
    "food bowl": "pet bowl",
    "water dish": "pet bowl",
    "dog bowl": "pet bowl",
    "cat bowl": "pet bowl",
    
    # Baby synonyms (compound terms first for priority matching)
    "baby clothes": "baby onesie",
    "baby outfit": "baby onesie",
    "baby shirt": "baby onesie",
    "baby wear": "baby onesie",
    "baby clothing": "baby onesie",
    "infant clothes": "baby onesie",
    "infant outfit": "baby onesie",
    "newborn clothes": "baby onesie",
    "newborn outfit": "baby onesie",
    "baby gift": "baby onesie",
    "baby shower": "baby onesie",
    "baby present": "baby onesie",
    "for baby": "baby onesie",
    "for my baby": "baby onesie",
    "for the baby": "baby onesie",
    "baby": "baby onesie",
    "infant": "baby onesie",
    "newborn": "baby onesie",
    "bodysuit": "baby onesie",
    "romper": "baby onesie",
    "onesie": "baby onesie",
    "bib": "baby bib",
    "kid clothes": "kids t-shirt",
    "kid shirt": "kids t-shirt",
    "kids clothes": "kids t-shirt",
    "kids clothing": "kids t-shirt",
    "children clothes": "kids t-shirt",
    "children clothing": "kids t-shirt",
    "toddler clothes": "kids t-shirt",
    "toddler shirt": "kids t-shirt",
    "for kids": "kids t-shirt",
    "for my kid": "kids t-shirt",
    "for children": "kids t-shirt",
    "kid": "kids t-shirt",
    "child": "kids t-shirt",
    "children": "kids t-shirt",
    "toddler": "kids t-shirt",
    
    # Gift/occasion context
    "gift": "mug",
    "present": "mug",
    "birthday": "mug",
    "christmas": "sweatshirt",
    "holiday": "sweatshirt",
    "valentines": "mug",
    "mothers day": "mug",
    "fathers day": "mug",
    "graduation": "t-shirt",
    "wedding": "canvas",
    "anniversary": "canvas",
    
    # Use-case context
    "for drinking": "mug",
    "to drink from": "mug",
    "for coffee": "mug",
    "for tea": "mug",
    "for water": "water bottle",
    "to wear": "t-shirt",
    "something to wear": "t-shirt",
    "for the wall": "canvas",
    "on my wall": "canvas",
    "hang up": "canvas",
    "for my phone": "phone case",
    "protect my phone": "phone case",
    "for the couch": "pillow",
    "for the sofa": "pillow",
    "for the bed": "blanket",
    "to sleep with": "blanket",
    "for the floor": "doormat",
    "at the door": "doormat",
    "for my head": "cap",
    "on my head": "cap",
    "for my feet": "socks",
    "on my feet": "socks",
    "for work": "apron",
    "in the kitchen": "apron",
    "for cooking": "apron",
    "for writing": "notebook",
    "to write in": "notebook",
    "take notes": "notebook",
}

# Common misspellings and typos
COMMON_MISSPELLINGS = {
    "tshirt": "t-shirt",
    "t shirt": "t-shirt",
    "teeshirt": "t-shirt",
    "tee shirt": "t-shirt",
    "hoody": "hoodie",
    "hoody": "hoodie",
    "hoddie": "hoodie",
    "sweatshrit": "sweatshirt",
    "swetshirt": "sweatshirt",
    "sweathsirt": "sweatshirt",
    "mugg": "mug",
    "coffe mug": "mug",
    "cofee mug": "mug",
    "pillow case": "pillow",
    "pillowcase": "pillow",
    "canvass": "canvas",
    "canvus": "canvas",
    "postre": "poster",
    "postar": "poster",
    "phoncase": "phone case",
    "phonecase": "phone case",
    "iphone case": "iphone case",
    "i phone case": "iphone case",
    "beenie": "beanie",
    "beannie": "beanie",
    "tumblar": "tumbler",
    "tumblr": "tumbler",
    "backpak": "backpack",
    "backpack": "backpack",
    "totebag": "tote bag",
    "tote": "tote bag",
    "onsie": "baby onesie",
    "onesies": "baby onesie",
    "babby": "baby onesie",
    "stiker": "sticker",
    "sticer": "sticker",
    "magnit": "magnet",
    "magnett": "magnet",
    "blankit": "blanket",
    "blankett": "blanket",
}

# Natural language patterns that indicate product type requests
PRODUCT_PATTERNS = [
    # "put it on a X" patterns
    (r"put\s+(?:it|this|that|the\s+design|my\s+design)?\s*on\s*(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please)", 1),
    # "create a X" patterns
    (r"create\s+(?:a|an|the)?\s*(.+?)\s+(?:with|using|from|for)", 1),
    (r"create\s+(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please)", 1),
    # "make a X" patterns
    (r"make\s+(?:a|an|the)?\s*(.+?)\s+(?:with|using|from|for)", 1),
    (r"make\s+(?:me\s+)?(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please)", 1),
    # "design for X" patterns
    (r"design\s+for\s+(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please)", 1),
    # "X with this design" patterns
    (r"^(.+?)\s+with\s+(?:this|the|my)\s+design", 1),
    # "add to X" patterns
    (r"add\s+(?:it|this|that)?\s*to\s+(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please)", 1),
    # "print on X" patterns
    (r"print\s+(?:it|this|that)?\s*on\s+(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please)", 1),
    # "I want a X" patterns
    (r"i\s+want\s+(?:a|an|the|this\s+on\s+a)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please|\s+with)", 1),
    # "I need a X" patterns
    (r"i\s+need\s+(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please|\s+with)", 1),
    # "give me a X" patterns
    (r"give\s+me\s+(?:a|an|the)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please|\s+with)", 1),
    # "can you make X" patterns
    (r"can\s+you\s+(?:make|create|design)\s+(?:a|an|the|me\s+a)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please|\s+with|\?)", 1),
    # "sell X" or "selling X" patterns
    (r"sell(?:ing)?\s+(?:a|an|the|some)?\s*(.+?)(?:\s+and|\s*$|\s*,|\s+please|\s+with)", 1),
    # "X product" patterns
    (r"(\w+(?:\s+\w+)?)\s+product(?:s)?(?:\s+and|\s*$|\s*,)", 1),
    # Just the product at start of sentence
    (r"^(?:a|an|the)?\s*(\w+(?:\s+\w+)?)\s*$", 1),
]

# Context keywords that suggest product categories
CONTEXT_KEYWORDS = {
    "drinkware": ["drink", "sip", "coffee", "tea", "beverage", "hot", "cold", "thirsty", "morning"],
    "apparel": ["wear", "dressed", "outfit", "fashion", "style", "comfortable", "casual", "formal"],
    "home": ["home", "house", "room", "living", "bedroom", "couch", "sofa", "decor", "decoration"],
    "wall": ["wall", "hang", "display", "frame", "art", "picture", "gallery"],
    "phone": ["phone", "mobile", "cell", "device", "protect", "case", "drop"],
    "pet": ["dog", "cat", "pet", "puppy", "kitten", "animal", "fur", "paw"],
    "baby": ["baby", "infant", "newborn", "child", "kid", "toddler", "nursery"],
    "outdoor": ["outdoor", "outside", "hiking", "camping", "adventure", "travel"],
    "office": ["office", "work", "desk", "professional", "business", "meeting"],
}

# Default products for each context
CONTEXT_DEFAULTS = {
    "drinkware": "mug",
    "apparel": "t-shirt",
    "home": "pillow",
    "wall": "canvas",
    "phone": "phone case",
    "pet": "pet bandana",
    "baby": "baby onesie",
    "outdoor": "water bottle",
    "office": "mug",
}

import re

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def normalize_plural(word: str) -> str:
    """Convert plurals to singular form."""
    if not word:
        return word
    
    # Common irregular plurals
    irregulars = {
        "children": "child",
        "mice": "mouse",
        "geese": "goose",
        "teeth": "tooth",
        "feet": "foot",
    }
    if word in irregulars:
        return irregulars[word]
    
    # Standard rules
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"  # puppies → puppy
    if word.endswith("es") and len(word) > 3:
        if word.endswith("sses") or word.endswith("shes") or word.endswith("ches") or word.endswith("xes"):
            return word[:-2]  # glasses → glass, dishes → dish
        return word[:-1]  # cases → case
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        return word[:-1]  # mugs → mug
    
    return word


def detect_context(text: str) -> Optional[str]:
    """Detect the context/category from text using keyword matching."""
    text_lower = text.lower()
    
    best_match = None
    best_count = 0
    
    for context, keywords in CONTEXT_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_match = context
    
    return best_match if best_count > 0 else None


def extract_product_from_text(text: str) -> Optional[str]:
    """
    Extract product type from natural language text using patterns.
    
    Examples:
        "put this on a mug" → "mug"
        "create a t-shirt with this design" → "t-shirt"
        "make me a hoodie" → "hoodie"
        "add to phone case" → "phone case"
        "I want this on a sweater" → "sweater"
        "can you make me a coffee cup?" → "coffee cup"
    """
    if not text:
        return None
    
    text_lower = text.lower().strip()
    
    # First try patterns
    for pattern, group in PRODUCT_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            extracted = match.group(group).strip()
            # Clean up common words
            extracted = re.sub(r'\s*(please|now|quickly|asap|today|thanks|thank you)\s*', '', extracted).strip()
            # Remove trailing punctuation
            extracted = re.sub(r'[?!.,;:]+$', '', extracted).strip()
            if extracted and len(extracted) < 50 and len(extracted) > 1:  # Sanity check
                return extracted
    
    return None


def resolve_product_type(product_type: str) -> Dict[str, Any]:
    """
    Resolve a product type string to blueprint_id and print_provider_id.
    
    Smart matching with:
    - Direct product names: "mug", "t-shirt"
    - Synonyms: "cup" → "mug", "sweater" → "sweatshirt"  
    - Natural language: "put this on a mug" → detects "mug"
    - Fuzzy matching: "coffee mugs" → "mug"
    - Typo tolerance: "hoody" → "hoodie"
    - Plural handling: "mugs" → "mug"
    - Context awareness: "for my dog" → pet products
    
    Args:
        product_type: Human-readable product type or natural language request
    
    Returns:
        Dict with blueprint_id, print_provider_id, name, and matched_from
    """
    if not product_type:
        # Default to t-shirt
        result = PRINTIFY_PRODUCT_CATALOG["t-shirt"].copy()
        result["matched_from"] = "default"
        return result
    
    # Normalize input
    original = product_type
    normalized = product_type.lower().strip()
    
    # Try to extract product from natural language patterns first
    extracted = extract_product_from_text(normalized)
    if extracted:
        logger.info(f"🎯 Extracted product from text: '{extracted}' from '{original}'")
        normalized = extracted
    
    # 0. Check common misspellings first
    if normalized in COMMON_MISSPELLINGS:
        corrected = COMMON_MISSPELLINGS[normalized]
        logger.info(f"📝 Corrected typo: '{normalized}' → '{corrected}'")
        normalized = corrected
    
    # Also check each word for misspellings
    words = normalized.split()
    corrected_words = []
    for word in words:
        if word in COMMON_MISSPELLINGS:
            corrected_words.append(COMMON_MISSPELLINGS[word])
        else:
            corrected_words.append(word)
    normalized = " ".join(corrected_words)
    
    # 1. Direct match in catalog
    if normalized in PRINTIFY_PRODUCT_CATALOG:
        result = PRINTIFY_PRODUCT_CATALOG[normalized].copy()
        result["matched_from"] = f"direct:{normalized}"
        return result
    
    # 1b. Try singular form
    singular = normalize_plural(normalized)
    if singular != normalized and singular in PRINTIFY_PRODUCT_CATALOG:
        result = PRINTIFY_PRODUCT_CATALOG[singular].copy()
        result["matched_from"] = f"singular:{normalized}→{singular}"
        logger.info(f"📝 Plural→Singular: '{normalized}' → '{singular}'")
        return result
    
    # 2. Check synonyms
    if normalized in PRODUCT_SYNONYMS:
        canonical = PRODUCT_SYNONYMS[normalized]
        if canonical in PRINTIFY_PRODUCT_CATALOG:
            result = PRINTIFY_PRODUCT_CATALOG[canonical].copy()
            result["matched_from"] = f"synonym:{normalized}→{canonical}"
            logger.info(f"🔄 Synonym match: '{normalized}' → '{canonical}'")
            return result
    
    # 2b. Try singular form for synonyms
    if singular != normalized and singular in PRODUCT_SYNONYMS:
        canonical = PRODUCT_SYNONYMS[singular]
        if canonical in PRINTIFY_PRODUCT_CATALOG:
            result = PRINTIFY_PRODUCT_CATALOG[canonical].copy()
            result["matched_from"] = f"synonym_singular:{singular}→{canonical}"
            logger.info(f"🔄 Synonym match (singular): '{singular}' → '{canonical}'")
            return result
    
    # 3. Fuzzy match - check if any catalog key is contained in input
    # CRITICAL: Sort by length descending to match longer/more specific terms first
    # This prevents "canvas tote bag" from matching "canvas" (wall art) instead of "tote bag"
    sorted_catalog_keys = sorted(PRINTIFY_PRODUCT_CATALOG.keys(), key=len, reverse=True)
    for key in sorted_catalog_keys:
        if key in normalized:
            result = PRINTIFY_PRODUCT_CATALOG[key].copy()
            result["matched_from"] = f"contains:{key}"
            logger.info(f"🎯 Best match found: '{key}' in '{normalized}'")
            return result
    
    # 4. Fuzzy match - check if input is contained in any catalog key
    # Also sort by length to prefer more specific matches
    for key in sorted_catalog_keys:
        if normalized in key:
            result = PRINTIFY_PRODUCT_CATALOG[key].copy()
            result["matched_from"] = f"partial:{normalized}→{key}"
            return result
    
    # 5. Check if any synonym key is in the normalized string
    # Sort by length descending to match more specific terms first
    sorted_synonyms = sorted(PRODUCT_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True)
    for syn_key, canonical in sorted_synonyms:
        if syn_key in normalized:
            if canonical in PRINTIFY_PRODUCT_CATALOG:
                result = PRINTIFY_PRODUCT_CATALOG[canonical].copy()
                result["matched_from"] = f"fuzzy_synonym:{syn_key}→{canonical}"
                logger.info(f"🔄 Fuzzy synonym: found '{syn_key}' in '{normalized}' → '{canonical}'")
                return result
    
    # 6. Check product name matches
    for key, value in PRINTIFY_PRODUCT_CATALOG.items():
        if normalized in value["name"].lower():
            result = value.copy()
            result["matched_from"] = f"name_match:{key}"
            return result
    
    # 7. Word-by-word matching with plural handling
    words = normalized.split()
    for word in words:
        if len(word) < 3:
            continue
        
        word_singular = normalize_plural(word)
        
        # Check catalog
        if word in PRINTIFY_PRODUCT_CATALOG:
            result = PRINTIFY_PRODUCT_CATALOG[word].copy()
            result["matched_from"] = f"word_match:{word}"
            return result
        if word_singular != word and word_singular in PRINTIFY_PRODUCT_CATALOG:
            result = PRINTIFY_PRODUCT_CATALOG[word_singular].copy()
            result["matched_from"] = f"word_match_singular:{word}→{word_singular}"
            return result
            
        # Check synonyms
        if word in PRODUCT_SYNONYMS:
            canonical = PRODUCT_SYNONYMS[word]
            if canonical in PRINTIFY_PRODUCT_CATALOG:
                result = PRINTIFY_PRODUCT_CATALOG[canonical].copy()
                result["matched_from"] = f"word_synonym:{word}→{canonical}"
                return result
        if word_singular != word and word_singular in PRODUCT_SYNONYMS:
            canonical = PRODUCT_SYNONYMS[word_singular]
            if canonical in PRINTIFY_PRODUCT_CATALOG:
                result = PRINTIFY_PRODUCT_CATALOG[canonical].copy()
                result["matched_from"] = f"word_synonym_singular:{word_singular}→{canonical}"
                return result
    
    # 8. Typo tolerance using Levenshtein distance (max 2 edits for short words, 3 for longer)
    best_match = None
    best_distance = float('inf')
    
    for key in PRINTIFY_PRODUCT_CATALOG:
        dist = levenshtein_distance(normalized, key)
        max_allowed = 2 if len(key) <= 5 else 3
        if dist <= max_allowed and dist < best_distance:
            best_distance = dist
            best_match = key
    
    if best_match:
        result = PRINTIFY_PRODUCT_CATALOG[best_match].copy()
        result["matched_from"] = f"typo_correction:{normalized}→{best_match}(dist={best_distance})"
        logger.info(f"📝 Typo correction: '{normalized}' → '{best_match}' (distance: {best_distance})")
        return result
    
    # Also check synonyms with typo tolerance
    for syn_key, canonical in PRODUCT_SYNONYMS.items():
        dist = levenshtein_distance(normalized, syn_key)
        max_allowed = 2 if len(syn_key) <= 5 else 3
        if dist <= max_allowed and dist < best_distance:
            if canonical in PRINTIFY_PRODUCT_CATALOG:
                best_distance = dist
                best_match = canonical
    
    if best_match:
        result = PRINTIFY_PRODUCT_CATALOG[best_match].copy()
        result["matched_from"] = f"typo_synonym:{normalized}→{best_match}(dist={best_distance})"
        logger.info(f"📝 Typo synonym correction: '{normalized}' → '{best_match}'")
        return result
    
    # 9. Context-based fallback - detect what the user is talking about
    context = detect_context(original)
    if context and context in CONTEXT_DEFAULTS:
        default_product = CONTEXT_DEFAULTS[context]
        if default_product in PRINTIFY_PRODUCT_CATALOG:
            result = PRINTIFY_PRODUCT_CATALOG[default_product].copy()
            result["matched_from"] = f"context:{context}→{default_product}"
            logger.info(f"🎯 Context detection: '{original}' → context '{context}' → '{default_product}'")
            return result
    
    # Default to t-shirt with warning
    logger.warning(f"⚠️ Unknown product type '{product_type}', defaulting to t-shirt")
    result = PRINTIFY_PRODUCT_CATALOG["t-shirt"].copy()
    result["matched_from"] = f"default (no match for '{product_type}')"
    return result


def list_available_products() -> Dict[str, List[str]]:
    """Get all available product types grouped by category."""
    categories = {
        "apparel": [],
        "drinkware": [],
        "phone_cases": [],
        "home_decor": [],
        "wall_art": [],
        "bags": [],
        "stationery": [],
        "accessories": [],
        "pet": [],
        "kids": []
    }
    
    category_keywords = {
        "apparel": ["shirt", "tee", "hoodie", "sweatshirt", "tank", "sleeve", "crop", "neck"],
        "drinkware": ["mug", "tumbler", "bottle", "travel"],
        "phone_cases": ["phone", "case", "iphone", "samsung"],
        "home_decor": ["pillow", "blanket", "shower", "doormat", "mousepad", "coaster"],
        "wall_art": ["canvas", "poster", "print", "framed", "metal", "acrylic", "wood"],
        "bags": ["tote", "backpack", "fanny", "crossbody", "drawstring"],
        "stationery": ["notebook", "journal", "sticker", "magnet", "card", "postcard"],
        "accessories": ["hat", "cap", "beanie", "socks", "flip", "apron", "mask"],
        "pet": ["pet", "dog"],
        "kids": ["baby", "onesie", "kids", "bib"]
    }
    
    for product_key in PRINTIFY_PRODUCT_CATALOG.keys():
        for cat, keywords in category_keywords.items():
            if any(kw in product_key for kw in keywords):
                categories[cat].append(product_key)
                break
    
    return categories


class PrintifyTools(ToolBase):
    """Printify API integration tools with Shopify sync."""
    
    BASE_URL = "https://api.printify.com/v1"
    
    # Cache for blueprints - loaded once from API
    _blueprint_cache: Optional[List[Dict[str, Any]]] = None
    _blueprint_cache_time: float = 0
    CACHE_TTL = 3600  # 1 hour cache
    
    def __init__(self, api_token: str, shop_id: str, shopify_tools=None):
        self.api_token = api_token
        self.shop_id = shop_id
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self._shopify_tools = shopify_tools
    
    def set_shopify_tools(self, shopify_tools):
        """Set Shopify tools for cross-platform sync."""
        self._shopify_tools = shopify_tools
    
    async def _sync_to_shopify(
        self,
        title: str,
        description: str,
        price: float,
        image_url: str = None,
        product_type: str = "Print on Demand",
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Sync a product to Shopify after creating on Printify.
        Returns Shopify product info or error.
        """
        if not self._shopify_tools:
            logger.warning("Shopify tools not configured - skipping Shopify sync")
            return {"synced": False, "reason": "Shopify not configured"}
        
        try:
            # Create product on Shopify
            shopify_result = await self._shopify_tools.create_product(
                title=title,
                description=description,
                price=str(price),
                product_type=product_type,
                tags=tags or ["printify", "print-on-demand"],
                image_url=image_url,
                status="active"  # Make it public on Shopify
            )
            
            if shopify_result and shopify_result.get("product"):
                shopify_product = shopify_result["product"]
                logger.info(f"✓ Synced to Shopify: {shopify_product.get('id')}")
                return {
                    "synced": True,
                    "shopify_product_id": shopify_product.get("id"),
                    "shopify_url": f"https://{self._shopify_tools.shop_url}/products/{shopify_product.get('handle')}"
                }
            else:
                logger.warning(f"Shopify sync returned unexpected result: {shopify_result}")
                return {"synced": False, "reason": "Unexpected Shopify response"}
                
        except Exception as e:
            logger.error(f"Failed to sync to Shopify: {e}")
            return {"synced": False, "reason": str(e)}
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """Make API request to Printify with retry logic."""
        import asyncio
        
        url = f"{self.BASE_URL}{endpoint}"
        last_error = None
        
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=self.headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        result = await response.json()
                        
                        if response.status >= 400:
                            logger.error(f"Printify API error (attempt {attempt + 1}): {result}")
                            last_error = Exception(f"Printify API error: {result}")
                            if attempt < retry_count - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            raise last_error
                        
                        return result
            except aiohttp.ClientError as e:
                logger.error(f"Network error (attempt {attempt + 1}): {e}")
                last_error = e
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        raise last_error or Exception("Request failed after retries")
    
    # ═══════════════════════════════════════════════════════════════════
    # DYNAMIC BLUEPRINT DISCOVERY - Query Printify API for product types
    # ═══════════════════════════════════════════════════════════════════
    
    async def get_all_blueprints(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch all available blueprints from Printify API with caching.
        
        Returns list of blueprints with id, title, description, and images.
        This is the source of truth for all available product types.
        Results are cached for 1 hour to avoid repeated API calls.
        
        Args:
            force_refresh: If True, bypasses cache and fetches fresh data
        """
        import time
        
        # Check cache first
        current_time = time.time()
        if not force_refresh and PrintifyTools._blueprint_cache is not None:
            cache_age = current_time - PrintifyTools._blueprint_cache_time
            if cache_age < PrintifyTools.CACHE_TTL:
                logger.debug(f"📦 Using cached blueprints ({len(PrintifyTools._blueprint_cache)} items, {int(cache_age)}s old)")
                return PrintifyTools._blueprint_cache
        
        try:
            endpoint = "/catalog/blueprints.json"
            result = await self._request("GET", endpoint)
            if isinstance(result, list):
                logger.info(f"📦 Fetched {len(result)} blueprints from Printify API (fresh)")
                # Cache the results
                PrintifyTools._blueprint_cache = result
                PrintifyTools._blueprint_cache_time = current_time
                return result
            data = result.get("data", []) if isinstance(result, dict) else []
            PrintifyTools._blueprint_cache = data
            PrintifyTools._blueprint_cache_time = current_time
            return data
        except Exception as e:
            logger.error(f"Failed to fetch blueprints: {e}")
            # Return stale cache if available
            if PrintifyTools._blueprint_cache is not None:
                logger.warning("Using stale cached blueprints due to API error")
                return PrintifyTools._blueprint_cache
            return []
    
    async def search_blueprint(self, product_type: str) -> Optional[Dict[str, Any]]:
        """
        Search Printify catalog for a blueprint matching the product type.
        
        Uses advanced scoring:
        - Exact matches get highest priority
        - Multi-word matching with bonus for all words matching
        - Common aliases and variations handled
        - Returns best available provider
        
        Args:
            product_type: Human-readable product type (e.g., "canvas tote bag", "mug", "beanie")
            
        Returns:
            Blueprint info with blueprint_id, print_provider_id, name, etc.
        """
        try:
            blueprints = await self.get_all_blueprints()
            product_type_lower = product_type.lower().strip()
            query_words = set(product_type_lower.split())
            
            # Common word normalizations - EXPANDED for better matching
            word_aliases = {
                # Apparel
                "tee": "t-shirt", "top": "t-shirt", "shirt": "t-shirt",
                "cap": "hat", 
                "pullover": "hoodie", "sweater": "sweatshirt",
                # Drinkware
                "cup": "mug", 
                # Stationery  
                "notebook": "notebook", "journal": "journal",
                # Home
                "pillow": "pillow", "cushion": "pillow",
                "blanket": "blanket", "throw": "blanket",
                "clock": "clock", "watch": "watch",
                "poster": "poster", "print": "print", "art": "art",
                # Accessories
                "sock": "socks", "socks": "socks",
                "beanie": "beanie", "knit": "beanie",
                # Novelty - ADDED playing cards, puzzles, etc
                "playing": "playing", "cards": "card", "card": "card", 
                "deck": "card", "poker": "card",
                "puzzle": "puzzle", "jigsaw": "puzzle",
                "ornament": "ornament", "christmas": "ornament",
                "flag": "flag", "garden": "garden",
                "coaster": "coaster", "coasters": "coaster",
            }
            
            # Normalize query words
            normalized_query = set()
            for word in query_words:
                normalized_query.add(word_aliases.get(word, word))
            
            scores = []
            for bp in blueprints:
                title = bp.get("title", "").lower()
                description = bp.get("description", "").lower()
                title_words = set(title.split())
                
                score = 0
                
                # 1. Exact title match (highest priority)
                if product_type_lower == title:
                    score += 1000
                
                # 2. Query is fully contained in title
                elif product_type_lower in title:
                    score += 500
                
                # 3. Title is fully contained in query  
                elif title in product_type_lower:
                    score += 400
                
                # 4. All query words appear in title (bonus)
                words_in_title = sum(1 for w in normalized_query if w in title)
                if words_in_title == len(normalized_query) and len(normalized_query) > 0:
                    score += 300  # All words match bonus
                
                # 5. Individual word matching with position weighting
                for word in normalized_query:
                    if len(word) < 2:
                        continue
                    # Check if word is in title
                    if word in title:
                        score += 50
                        # Bonus if it's a primary word (first or key descriptor)
                        if title.startswith(word) or f" {word}" in title:
                            score += 25
                    # Partial word match (e.g., "hood" in "hoodie")
                    elif any(word in tw or tw in word for tw in title_words if len(tw) > 2):
                        score += 20
                
                # 6. Description matching (lower weight)
                for word in normalized_query:
                    if len(word) > 2 and word in description:
                        score += 5
                
                # 7. Penalize generic matches (e.g., "Classic T-Shirt" when asking for "beanie")
                # If none of the core query words are in the title, heavily penalize
                core_match = any(w in title for w in query_words if len(w) > 3)
                if not core_match and score < 100:
                    score = max(0, score - 50)
                
                if score > 0:
                    scores.append((score, bp))
            
            # Sort by score descending
            scores.sort(key=lambda x: x[0], reverse=True)
            
            if scores and scores[0][0] >= 20:  # Minimum threshold
                best_match = scores[0][1]
                logger.info(f"🎯 Dynamic blueprint search: '{product_type}' → #{best_match.get('id')} {best_match.get('title')} (score: {scores[0][0]})")
                
                # Log top 3 matches for debugging
                if len(scores) >= 3:
                    logger.debug(f"Top matches: {[(s[0], s[1].get('title')) for s in scores[:3]]}")
                
                # Get print providers for this blueprint
                blueprint_id = best_match.get("id")
                providers = await self.get_print_providers(blueprint_id)
                
                if providers:
                    # Sort by title to prefer consistent providers
                    if isinstance(providers, list) and len(providers) > 1:
                        # Prefer providers with more options usually
                        providers = sorted(providers, key=lambda p: p.get("title", ""), reverse=False)
                    
                    provider = providers[0] if isinstance(providers, list) else providers
                    provider_id = provider.get("id")
                    
                    return {
                        "blueprint_id": blueprint_id,
                        "print_provider_id": provider_id,
                        "name": best_match.get("title"),
                        "description": best_match.get("description", ""),
                        "matched_from": "dynamic_api_search",
                        "match_score": scores[0][0],
                        "all_providers": [p.get("id") for p in providers] if isinstance(providers, list) else [provider_id]
                    }
            
            logger.warning(f"No blueprint found for '{product_type}'")
            return None
            
        except Exception as e:
            logger.error(f"Dynamic blueprint search failed: {e}")
            return None
    
    async def get_print_providers(self, blueprint_id: int) -> List[Dict[str, Any]]:
        """Get available print providers for a blueprint."""
        try:
            endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers.json"
            result = await self._request("GET", endpoint)
            if isinstance(result, list):
                return result
            return result.get("data", []) if isinstance(result, dict) else []
        except Exception as e:
            logger.error(f"Failed to get print providers for blueprint {blueprint_id}: {e}")
            return []
    
    @tool(
        name="printify_search_product_types",
        description="Search Printify catalog for available product types by name. Use this to find the right blueprint for any product.",
        category="printify"
    )
    async def search_product_types(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for product types in the Printify catalog.
        
        Args:
            query: Product type to search for (e.g., "canvas tote", "mug", "hoodie")
            limit: Max results to return
            
        Returns:
            List of matching product types with blueprint IDs
        """
        try:
            blueprints = await self.get_all_blueprints()
            query_lower = query.lower().strip()
            
            matches = []
            for bp in blueprints:
                title = bp.get("title", "").lower()
                if query_lower in title or any(word in title for word in query_lower.split()):
                    matches.append({
                        "blueprint_id": bp.get("id"),
                        "title": bp.get("title"),
                        "description": bp.get("description", "")[:100]
                    })
                    if len(matches) >= limit:
                        break
            
            return {
                "success": True,
                "query": query,
                "matches": matches,
                "total_found": len(matches),
                "hint": "Use the blueprint_id with printify_create_product or just use printify_smart_create_product with the product title"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    @tool(
        name="printify_get_catalog",
        description="Get the complete Printify product catalog with all available product types, categories, and keywords. Use this to see what products can be created.",
        category="printify"
    )
    async def get_catalog(self) -> Dict[str, Any]:
        """
        Get the complete Printify product catalog available for creation.
        
        Returns organized list of all product types by category with:
        - Product name
        - Keywords that trigger creation
        - Blueprint ID and print provider info
        """
        catalog = {
            "success": True,
            "description": "Available Printify product types you can create",
            "categories": {}
        }
        
        # Organize by category
        categories = {
            "👕 Apparel": ["t-shirt", "hoodie", "sweatshirt", "tank top", "long sleeve", "crop top", "v-neck"],
            "☕ Drinkware": ["mug", "mug 15oz", "black mug", "travel mug", "tumbler", "water bottle"],
            "📱 Phone Cases": ["phone case", "iphone case", "samsung case", "clear phone case"],
            "🏠 Home & Living": ["pillow", "blanket", "shower curtain", "doormat", "mousepad", "coaster"],
            "🖼️ Wall Art": ["canvas", "poster", "framed poster", "metal print", "acrylic print", "wood print"],
            "👜 Bags": ["tote bag", "backpack", "fanny pack", "crossbody bag", "drawstring bag"],
            "📓 Stationery": ["notebook", "journal", "sticker", "magnet", "greeting card", "postcard"],
            "🧢 Accessories": ["hat", "cap", "beanie", "socks", "flip flops", "apron", "face mask"],
            "🐕 Pet Products": ["pet bandana", "pet bowl"],
            "👶 Baby & Kids": ["baby onesie", "kids t-shirt", "baby bib"]
        }
        
        for category, products in categories.items():
            catalog["categories"][category] = []
            for product in products:
                if product in PRINTIFY_PRODUCT_CATALOG:
                    info = PRINTIFY_PRODUCT_CATALOG[product]
                    # Find synonyms that map to this product
                    synonyms = [k for k, v in PRODUCT_SYNONYMS.items() if v == product][:5]
                    catalog["categories"][category].append({
                        "product_type": product,
                        "full_name": info["name"],
                        "blueprint_id": info["blueprint_id"],
                        "also_known_as": synonyms
                    })
        
        catalog["total_products"] = len(PRINTIFY_PRODUCT_CATALOG)
        catalog["usage_tip"] = "Just say 'create a [product_type] with my design' or use natural language like 'put this on a mug'"
        
        return catalog
    
    @tool(
        name="printify_list_all_products",
        description="List ALL available product types from the FULL Printify catalog (fetched from API). Shows everything available - beanies, clocks, puzzles, ornaments, etc.",
        category="printify"
    )
    async def list_all_products(self, category_filter: str = None, limit: int = 100) -> Dict[str, Any]:
        """
        Fetch and list ALL available product types from the Printify API.
        
        Unlike get_catalog, this dynamically fetches from Printify's API
        to show every single product available, not just our curated list.
        
        Args:
            category_filter: Optional filter (e.g., "accessories", "home", "apparel")
            limit: Max results (default 100)
        
        Returns:
            Complete list of available products from Printify
        """
        try:
            blueprints = await self.get_all_blueprints()
            
            # Group by detected category
            categories = {
                "apparel": [],
                "drinkware": [],
                "home": [],
                "accessories": [],
                "bags": [],
                "wall_art": [],
                "stationery": [],
                "tech": [],
                "pet": [],
                "kids": [],
                "novelty": [],
                "other": []
            }
            
            # Category detection keywords
            category_keywords = {
                "apparel": ["shirt", "tee", "hoodie", "sweatshirt", "tank", "jersey", "polo", "dress", "legging", "shorts", "pants", "jacket"],
                "drinkware": ["mug", "cup", "tumbler", "bottle", "glass", "can", "cooler"],
                "home": ["pillow", "blanket", "towel", "curtain", "doormat", "rug", "mat", "clock", "coaster"],
                "accessories": ["hat", "cap", "beanie", "socks", "mask", "apron", "bandana", "scarf", "gloves"],
                "bags": ["bag", "tote", "pouch", "backpack", "fanny", "clutch"],
                "wall_art": ["canvas", "poster", "print", "frame", "metal print", "acrylic", "tapestry"],
                "stationery": ["notebook", "journal", "sticker", "magnet", "card", "postcard"],
                "tech": ["phone", "case", "mousepad", "laptop", "mouse pad"],
                "pet": ["pet", "dog", "cat"],
                "kids": ["baby", "kid", "infant", "onesie", "bib", "toddler"],
                "novelty": ["puzzle", "ornament", "flag", "playing card", "game", "cutting board"]
            }
            
            for bp in blueprints[:limit]:
                title = bp.get("title", "").lower()
                blueprint_id = bp.get("id")
                
                # Detect category
                detected_category = "other"
                for cat, keywords in category_keywords.items():
                    if any(kw in title for kw in keywords):
                        detected_category = cat
                        break
                
                # Skip if filter doesn't match
                if category_filter and category_filter.lower() not in detected_category:
                    continue
                
                categories[detected_category].append({
                    "name": bp.get("title"),
                    "blueprint_id": blueprint_id,
                    "description": bp.get("description", "")[:80] if bp.get("description") else ""
                })
            
            # Build result
            result = {
                "success": True,
                "total_blueprints": len(blueprints),
                "showing": min(limit, len(blueprints)),
                "categories": {},
                "how_to_use": "Use printify_smart_create_product with any product name to create it automatically"
            }
            
            for cat, products in categories.items():
                if products:  # Only include non-empty categories
                    result["categories"][cat] = {
                        "count": len(products),
                        "products": products[:20]  # Limit per category
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list all products: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @tool(
        name="printify_list_products",
        description="List all products in the Printify shop",
        category="printify"
    )
    async def list_products(self, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        """List products from Printify shop."""
        endpoint = f"/shops/{self.shop_id}/products.json?limit={limit}&page={page}"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_get_product",
        description="Get details of a specific product",
        category="printify"
    )
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get a specific product."""
        endpoint = f"/shops/{self.shop_id}/products/{product_id}.json"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_get_mockup_urls",
        description="Get mockup image URLs from a Printify product - use these images for video generation, marketing, or social media",
        category="printify"
    )
    async def get_mockup_urls(self, product_id: str) -> Dict[str, Any]:
        """
        Get all mockup image URLs from a Printify product.
        
        These mockup images show the product with your design applied.
        Use them for:
        - Creating product videos
        - Social media marketing
        - Website product images
        - Ad creatives
        
        Args:
            product_id: Printify product ID
            
        Returns:
            {
                "success": True,
                "mockups": [
                    {"url": "https://...", "position": "front", "is_default": True},
                    ...
                ],
                "default_mockup_url": "https://...",
                "product_title": "...",
                "product_id": "..."
            }
        """
        try:
            # Get product details
            product = await self.get_product(product_id)
            
            if not product or not product.get("images"):
                return {
                    "success": False,
                    "error": "Product not found or has no mockup images",
                    "product_id": product_id
                }
            
            mockups = []
            default_url = None
            
            for img in product.get("images", []):
                src = img.get("src")
                if src:
                    is_default = img.get("is_default", False)
                    mockup = {
                        "url": src,
                        "position": img.get("position", "front"),
                        "is_default": is_default,
                        "variant_ids": img.get("variant_ids", [])
                    }
                    mockups.append(mockup)
                    
                    if is_default:
                        default_url = src
            
            # If no default, use first mockup
            if not default_url and mockups:
                default_url = mockups[0]["url"]
            
            logger.info(f"Found {len(mockups)} mockups for product {product_id}")
            
            return {
                "success": True,
                "mockups": mockups,
                "default_mockup_url": default_url,
                "mockup_count": len(mockups),
                "product_title": product.get("title", ""),
                "product_id": product_id,
                "note": "Use default_mockup_url for video generation or marketing materials"
            }
            
        except Exception as e:
            logger.error(f"Failed to get mockup URLs: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id
            }
    
    @tool(
        name="printify_create_product",
        description="Create a new product on Printify with design",
        category="printify"
    )
    async def create_product(
        self,
        title: str,
        description: str,
        blueprint_id: int,
        print_provider_id: int,
        image_url: str = None,
        variants: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None,
        # Parameter aliases for planning agent flexibility
        design_url: str = None,
        design_image_url: str = None,
        design_image_id: str = None,  # Sometimes agent provides uploaded image ID
        url: str = None,
        image_path: str = None,
        price: int = None,  # Ignored - pricing is set per variant
        **kwargs  # Catch any other unexpected params
    ) -> Dict[str, Any]:
        """
        Create a new product on Printify.
        
        Args:
            title: Product title
            description: Product description
            blueprint_id: Printify blueprint ID (e.g., 6 for t-shirt, 12 for mug, 384 for canvas)
            print_provider_id: Print provider ID
            image_url: URL of the design image (accepts many aliases)
            variants: List of variant configurations
            tags: Product tags
        """
        # Resolve image URL from aliases (ignore design_image_id as it's handled by upload)
        actual_image_url = image_url or design_url or design_image_url or url or image_path
        if not actual_image_url and not design_image_id:
            raise ValueError("Must provide image_url (or design_url/url alias)")
        
        # Get or upload image ID
        if design_image_id:
            # Image already uploaded, use that ID
            image_id = design_image_id
            logger.info(f"Using pre-uploaded image ID: {image_id}")
        else:
            # Upload the image
            upload_result = await self.upload_image(actual_image_url)
            image_id = upload_result.get("id")
        
        if not image_id:
            raise Exception("Failed to get/upload image to Printify")
        
        # Get blueprint placeholders
        placeholders = await self._get_blueprint_placeholders(
            blueprint_id,
            print_provider_id
        )
        
        logger.info(f"Retrieved {len(placeholders)} placeholders for blueprint {blueprint_id}")
        
        # Build print areas - ensure ALL variants are covered
        print_areas = []
        all_variant_ids_in_areas = set()
        
        for placeholder in placeholders:
            variant_ids = placeholder.get("variant_ids", [])
            all_variant_ids_in_areas.update(variant_ids)
            
            print_areas.append({
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": placeholder.get("position", "front"),
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            })
        
        logger.info(f"Print areas cover {len(all_variant_ids_in_areas)} variants")
        
        # Get variants (or use provided ones)
        product_variants = variants or await self._get_default_variants(
            blueprint_id,
            print_provider_id
        )
        
        # Ensure all enabled variants are in print_areas
        enabled_variant_ids = {v.get("id") for v in product_variants if v.get("is_enabled", True)}
        missing_variants = enabled_variant_ids - all_variant_ids_in_areas
        
        if missing_variants:
            logger.warning(f"Some variants not in print_areas: {missing_variants}")
            # If we're missing variants, add them to the first print area
            if print_areas:
                print_areas[0]["variant_ids"].extend(list(missing_variants))
                logger.info(f"Added missing variants to first print area")
        
        # CRITICAL: Ensure exact match between variants array and print_areas
        # Remove any variants that aren't in print_areas
        valid_variant_ids = all_variant_ids_in_areas | missing_variants
        product_variants = [v for v in product_variants if v.get("id") in valid_variant_ids]
        
        logger.info(f"Final validation: {len(product_variants)} variants match {len(valid_variant_ids)} in print_areas")
        
        # Build product data
        product_data = {
            "title": title,
            "description": description,
            "blueprint_id": blueprint_id,
            "print_provider_id": print_provider_id,
            "variants": product_variants,
            "print_areas": print_areas
        }
        
        if tags:
            product_data["tags"] = tags
        
        logger.info(f"Creating product with {len(product_variants)} variants and {len(print_areas)} print areas")
        endpoint = f"/shops/{self.shop_id}/products.json"
        result = await self._request("POST", endpoint, product_data)
        
        # Auto-publish to connected store (Shopify) immediately
        product_id = result.get("id")
        if product_id:
            try:
                await self.publish_product(product_id, visible=True)
                logger.info(f"✓ Product {product_id} auto-published to Shopify")
                result["published"] = True
                result["shopify_status"] = "live"
            except Exception as pub_error:
                logger.warning(f"Auto-publish failed: {pub_error}")
                result["published"] = False
                result["shopify_status"] = "draft"
        
        return result
    
    @tool(
        name="printify_smart_create_product",
        description="Smart product creation - works for ANY product type (beanie, socks, clock, coaster, hoodie, mug, journal, poster, etc). Just specify product type and design. Auto-discovers all parameters.",
        category="printify"
    )
    async def smart_create_product(
        self,
        title: str,
        description: str,
        product_type: str,
        image_url: str = None,
        design_url: str = None,
        tags: Optional[List[str]] = None,
        price_cents: int = 2499,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create ANY PRODUCT TYPE using human-readable product type.
        
        This is the MAIN entry point for creating products. It:
        1. Searches the FULL Printify catalog dynamically
        2. Auto-discovers blueprint IDs and print providers
        3. Auto-fills all required parameters
        4. Works for ANY product - from beanies to clocks to wall art
        
        Supported product types (examples - works for ANYTHING on Printify):
        - Apparel: t-shirt, hoodie, sweatshirt, tank top, beanie, socks, leggings
        - Drinkware: mug, tumbler, water bottle, travel mug
        - Phone cases: phone case, iphone case, samsung case
        - Home: pillow, blanket, canvas, poster, clock, coaster, doormat, shower curtain
        - Wall Art: canvas print, framed poster, metal print, acrylic print, wood print
        - Stationery: notebook, journal, sticker, magnet, greeting card, postcard
        - Bags: tote bag, backpack, fanny pack, drawstring bag
        - Accessories: hat, cap, beanie, socks, apron, flip flops
        - Novelty: puzzle, ornament, playing cards, garden flag
        - Pet: pet bandana, dog bowl
        - Kids: baby onesie, kids t-shirt
        
        Args:
            title: Product title
            description: Product description
            product_type: ANY product type - e.g., "beanie", "clock", "socks", "poster"
            image_url: URL of design image
            design_url: Alias for image_url
            tags: Product tags
            price_cents: Price in cents (default: 2499 = $24.99)
        
        Returns:
            Created product data including ID, URL, and status
        """
        # Get actual image URL
        actual_image_url = image_url or design_url or kwargs.get("url") or kwargs.get("design_image_url")
        
        if not actual_image_url:
            return {
                "success": False,
                "error": "Must provide image_url or design_url for the product design",
                "hint": "Provide the URL of your design image"
            }
        
        # Prepare tags
        product_tags = tags or [product_type.lower(), "custom", "design"]
        
        # Use the UNIVERSAL product creator for ALL products
        # This dynamically searches the Printify catalog and auto-fills everything
        logger.info(f"🚀 Smart create: '{product_type}' - '{title}'")
        
        result = await self._create_any_product(
            title=title,
            description=description,
            product_type=product_type,
            image_url=actual_image_url,
            price_cents=price_cents,
            tags=product_tags
        )
        
        return result
    
    @tool(
        name="printify_upload_image",
        description="Upload an image to Printify from a URL",
        category="printify"
    )
    async def upload_image(
        self,
        image_url: str = None,
        filename: str = "design.png",
        file_name: str = None,
        image_path: str = None,
        design_url: str = None,
        design_image_url: str = None,
        url: str = None
    ) -> Dict[str, Any]:
        """
        Upload an image to Printify.
        
        ALWAYS downloads and saves image locally first, then uploads base64.
        This ensures compatibility with all image sources (Replicate, URLs, etc.)
        """
        # Handle aliases
        actual_url = image_url or image_path or design_url or design_image_url or url
        if not actual_url:
            raise ValueError("Must provide image_url parameter")
        
        if file_name:
            filename = file_name
            
        import base64
        from pathlib import Path
        import tempfile
        from PIL import Image
        import io
        
        endpoint = "/uploads/images.json"
        
        # Step 1: Get image data (from local file or URL)
        image_data = None
        
        # Check if it's a local file path
        if actual_url.startswith('/files/'):
            # Local file storage path - extract file ID and read from disk
            try:
                file_id = actual_url.split('/')[-1]
                logger.info(f"Reading local file: {file_id}")
                
                # Try to find the file in data/files/ using ABSOLUTE paths
                import os
                base_path = Path(os.getcwd()) / "data" / "files"
                possible_paths = [
                    base_path / "images" / file_id,
                    base_path / "generated" / file_id,
                    base_path / "uploads" / file_id,
                    base_path / file_id
                ]
                
                # Also try with common extensions if no extension
                if '.' not in file_id:
                    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                        for p in list(possible_paths):
                            possible_paths.append(Path(str(p) + ext))
                
                file_path = None
                for path in possible_paths:
                    logger.info(f"Checking: {path}")
                    if path.exists():
                        file_path = path
                        break
                
                if not file_path:
                    # Try to find any file matching the ID
                    import glob
                    matches = list(base_path.rglob(f"*{file_id}*"))
                    logger.info(f"Found {len(matches)} matches for {file_id}")
                    if matches:
                        file_path = matches[0]
                
                if file_path and file_path.exists():
                    logger.info(f"✓ Found local file at: {file_path}")
                    with open(file_path, 'rb') as f:
                        image_data = f.read()
                    logger.info(f"✓ Read {len(image_data)} bytes from local file")
                else:
                    raise FileNotFoundError(f"Could not find local file for: {actual_url} (searched in {base_path})")
                    
            except Exception as e:
                logger.error(f"Failed to read local file: {e}")
                raise Exception(f"Cannot read local file: {e}")
        
        elif not actual_url.startswith(('http://', 'https://')):
            # Treat as local file system path or filename
            try:
                local_path = Path(actual_url)
                if local_path.exists():
                    logger.info(f"Reading local file: {local_path}")
                    with open(local_path, 'rb') as f:
                        image_data = f.read()
                    logger.info(f"Read {len(image_data)} bytes from {local_path}")
                else:
                    # File doesn't exist at given path - try to find it
                    logger.info(f"File not found at {actual_url}, searching for it...")
                    import os
                    base_path = Path(os.getcwd()) / "data" / "files"
                    
                    # Search strategies:
                    # 1. Look for exact filename anywhere
                    # 2. Look for partial filename match
                    # 3. Get the most recent image file
                    
                    filename_only = local_path.name
                    found_path = None
                    
                    # Strategy 1: Exact filename match
                    for match in base_path.rglob(filename_only):
                        found_path = match
                        logger.info(f"Found exact match: {found_path}")
                        break
                    
                    # Strategy 2: Partial match (without extension)
                    if not found_path:
                        name_stem = local_path.stem.lower()
                        for match in base_path.rglob("*"):
                            if match.is_file() and name_stem in match.stem.lower():
                                found_path = match
                                logger.info(f"Found partial match: {found_path}")
                                break
                    
                    # Strategy 3: Get most recent image file
                    if not found_path:
                        image_dirs = [
                            base_path / "images",
                            base_path / "generated",
                            base_path / "images" / "generated"
                        ]
                        recent_files = []
                        for img_dir in image_dirs:
                            if img_dir.exists():
                                for f in img_dir.iterdir():
                                    if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                                        recent_files.append((f, f.stat().st_mtime))
                        
                        if recent_files:
                            # Sort by modification time, most recent first
                            recent_files.sort(key=lambda x: x[1], reverse=True)
                            found_path = recent_files[0][0]
                            logger.info(f"Using most recent image: {found_path}")
                    
                    if found_path and found_path.exists():
                        with open(found_path, 'rb') as f:
                            image_data = f.read()
                        logger.info(f"Read {len(image_data)} bytes from {found_path}")
                    else:
                        raise FileNotFoundError(f"Could not find image file: {actual_url}")
                        
            except FileNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to read local file: {e}")
                raise Exception(f"Cannot read local file: {e}")
        
        else:
            # Download from URL
            async with aiohttp.ClientSession() as session:
                try:
                    logger.info(f"Downloading image from {actual_url}...")
                    async with session.get(actual_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        if response.status != 200:
                            # Check if this is a Replicate URL that may have expired
                            if 'replicate.delivery' in actual_url and response.status in [403, 404, 410]:
                                logger.warning(f"Replicate URL expired (HTTP {response.status}), searching for local cached version...")
                                
                                # Try to find locally saved version
                                import os
                                from pathlib import Path
                                base_path = Path(os.getcwd()) / "data" / "files" / "images"
                                
                                # Get most recent image as fallback
                                if base_path.exists():
                                    image_files = sorted(
                                        [f for f in base_path.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']],
                                        key=lambda x: x.stat().st_mtime,
                                        reverse=True
                                    )
                                    if image_files:
                                        local_fallback = image_files[0]
                                        logger.info(f"Using local fallback image: {local_fallback}")
                                        with open(local_fallback, 'rb') as f:
                                            image_data = f.read()
                                        logger.info(f"Read {len(image_data)} bytes from fallback")
                                    else:
                                        raise Exception(f"Replicate URL expired (HTTP {response.status}) and no local fallback found")
                                else:
                                    raise Exception(f"Replicate URL expired (HTTP {response.status}) and no local fallback available")
                            else:
                                raise Exception(f"Failed to download image: HTTP {response.status}")
                        else:
                            image_data = await response.read()
                            logger.info(f"Downloaded {len(image_data)} bytes")
                        
                except aiohttp.ClientError as e:
                    # Network error - try local fallback for Replicate URLs
                    if 'replicate.delivery' in actual_url:
                        logger.warning(f"Network error for Replicate URL, trying local fallback: {e}")
                        import os
                        from pathlib import Path
                        base_path = Path(os.getcwd()) / "data" / "files" / "images"
                        
                        if base_path.exists():
                            image_files = sorted(
                                [f for f in base_path.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']],
                                key=lambda x: x.stat().st_mtime,
                                reverse=True
                            )
                            if image_files:
                                local_fallback = image_files[0]
                                logger.info(f"Using local fallback image: {local_fallback}")
                                with open(local_fallback, 'rb') as f:
                                    image_data = f.read()
                            else:
                                raise Exception(f"Cannot upload to Printify: image download failed - {e}")
                        else:
                            raise Exception(f"Cannot upload to Printify: image download failed - {e}")
                    else:
                        logger.error(f"Failed to download image: {e}")
                        raise Exception(f"Cannot upload to Printify: image download failed - {e}")
        
        # Step 2: Convert to PNG if needed (Printify prefers PNG)
        try:
            # Open image with PIL to ensure it's valid and convert to PNG
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed (removes alpha channel issues)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                    img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as PNG
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG', optimize=True)
            png_data = png_buffer.getvalue()
            
            logger.info(f"Converted to PNG: {len(png_data)} bytes")
            
        except Exception as e:
            logger.error(f"Failed to convert image: {e}")
            # Fall back to original data if conversion fails
            png_data = image_data
        
        # Step 3: Base64 encode
        try:
            encoded = base64.b64encode(png_data).decode("utf-8")
            logger.info(f"Image encoded, size: {len(encoded)} characters")
            
            # Step 4: Upload to Printify
            # Ensure filename ends with .png
            if not filename.endswith('.png'):
                filename = filename.rsplit('.', 1)[0] + '.png'
            
            data = {
                "file_name": filename,
                "contents": encoded
            }
            
            result = await self._request("POST", endpoint, data)
            
            # Clean up temp file
            try:
                temp_file.unlink()
            except:
                pass
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to encode/upload image: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "image_upload_failed",
                "message": f"Could not upload image to Printify: {str(e)}"
            }
    
    @tool(
        name="printify_publish_product",
        description="Publish a product to connected sales channels (Shopify, etc.) and make it publicly visible",
        category="printify"
    )
    async def publish_product(
        self,
        product_id: str,
        title: bool = True,
        description: bool = True,
        images: bool = True,
        variants: bool = True,
        tags: bool = True,
        visible: bool = True  # Make product visible/public on the store
    ) -> Dict[str, Any]:
        """
        Publish product to connected stores (Shopify, etc.).
        
        This makes the product live and visible to customers on your connected store.
        
        Args:
            product_id: The Printify product ID
            title: Sync title to store
            description: Sync description to store
            images: Sync images to store
            variants: Sync variants/pricing to store
            tags: Sync tags to store
            visible: Make product publicly visible (default True)
        """
        endpoint = f"/shops/{self.shop_id}/products/{product_id}/publish.json"
        data = {
            "title": title,
            "description": description,
            "images": images,
            "variants": variants,
            "tags": tags,
            "visible": visible  # This makes it public on the store
        }
        result = await self._request("POST", endpoint, data)
        
        # Also set publishing status to ensure it's live
        try:
            # Update product to ensure it's not in draft mode
            update_endpoint = f"/shops/{self.shop_id}/products/{product_id}/publishing_succeeded.json"
            await self._request("POST", update_endpoint, {})
            logger.info(f"Product {product_id} published and set to visible on connected store")
        except Exception as e:
            # This endpoint may not exist on all API versions, that's OK
            logger.debug(f"Publishing succeeded endpoint not available: {e}")
        
        return result
    
    @tool(
        name="printify_list_blueprints",
        description="List available product blueprints (t-shirts, mugs, etc.)",
        category="printify"
    )
    async def list_blueprints(self) -> Dict[str, Any]:
        """Get available blueprints."""
        return await self._request("GET", "/catalog/blueprints.json")
    
    # Default fallbacks for common product types
    BLUEPRINT_DEFAULTS = {
        6: {"name": "Unisex Heavy Cotton Tee", "provider_id": 99, "provider_name": "Monster Digital"},  # Gildan 5000
        145: {"name": "Unisex Softstyle T-Shirt", "provider_id": 99, "provider_name": "Monster Digital"},  # Gildan 64000
        12: {"name": "Ceramic Mug 11oz", "provider_id": 28, "provider_name": "Duplium"},
        380: {"name": "Unisex Hoodie", "provider_id": 99, "provider_name": "Monster Digital"},
    }
    
    @tool(
        name="printify_get_print_providers",
        description="Get print providers for a blueprint",
        category="printify"
    )
    async def get_print_providers(self, blueprint_id: int) -> Dict[str, Any]:
        """Get print providers for a blueprint."""
        # Handle invalid blueprint_id (e.g., passed as string 'from_previous_step')
        if not isinstance(blueprint_id, int):
            try:
                blueprint_id = int(blueprint_id)
            except (ValueError, TypeError):
                # Default to Unisex Heavy Cotton Tee
                blueprint_id = 6
                logger.warning(f"Invalid blueprint_id, defaulting to {blueprint_id}")
        
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers.json"
        try:
            return await self._request("GET", endpoint)
        except Exception as e:
            # Fallback to defaults if API fails
            if blueprint_id in self.BLUEPRINT_DEFAULTS:
                fallback = self.BLUEPRINT_DEFAULTS[blueprint_id]
                logger.warning(f"Print provider lookup failed, using fallback: {fallback}")
                return [{"id": fallback["provider_id"], "title": fallback["provider_name"]}]
            raise e
    
    @tool(
        name="printify_get_variants",
        description="Get variants (sizes, colors) for a blueprint/provider",
        category="printify"
    )
    async def get_variants(
        self,
        blueprint_id: int,
        print_provider_id: int
    ) -> Dict[str, Any]:
        """Get variants for blueprint and provider."""
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_delete_product",
        description="Delete a product from Printify",
        category="printify"
    )
    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        """Delete a product."""
        endpoint = f"/shops/{self.shop_id}/products/{product_id}.json"
        return await self._request("DELETE", endpoint)
    
    @tool(
        name="printify_list_orders",
        description="List orders from Printify",
        category="printify"
    )
    async def list_orders(self, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        """List orders."""
        endpoint = f"/shops/{self.shop_id}/orders.json?limit={limit}&page={page}"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_get_order",
        description="Get details of a specific Printify order",
        category="printify"
    )
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details."""
        endpoint = f"/shops/{self.shop_id}/orders/{order_id}.json"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_get_top_products",
        description="Analyze Printify orders to find top-selling products",
        category="printify"
    )
    async def get_top_products(
        self,
        limit: int = 10,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze Printify orders to determine top-selling products.
        
        Args:
            limit: Number of top products to return
            max_pages: Number of order pages to analyze (50 orders per page)
            
        Returns:
            Dict with top products ranked by sales
        """
        try:
            product_sales = {}  # product_id -> {title, count, revenue}
            total_orders = 0
            
            # Fetch multiple pages of orders
            for page in range(1, max_pages + 1):
                orders_result = await self.list_orders(limit=50, page=page)
                orders = orders_result.get("data", [])
                
                if not orders:
                    break
                
                total_orders += len(orders)
                
                for order in orders:
                    line_items = order.get("line_items", [])
                    
                    for item in line_items:
                        product_id = item.get("product_id")
                        if not product_id:
                            continue
                        
                        quantity = int(item.get("quantity", 1))
                        
                        if product_id not in product_sales:
                            product_sales[product_id] = {
                                "product_id": product_id,
                                "title": item.get("title", "Unknown"),
                                "units_sold": 0,
                                "order_count": 0
                            }
                        
                        product_sales[product_id]["units_sold"] += quantity
                        product_sales[product_id]["order_count"] += 1
            
            # Sort by units sold
            sorted_products = sorted(
                product_sales.values(),
                key=lambda x: x["units_sold"],
                reverse=True
            )[:limit]
            
            return {
                "top_products": sorted_products,
                "orders_analyzed": total_orders,
                "total_unique_products": len(product_sales)
            }
            
        except Exception as e:
            logger.error(f"Failed to get top Printify products: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze Printify orders"
            }
    
    @tool(
        name="printify_get_product_stats",
        description="Get detailed statistics for a specific Printify product",
        category="printify"
    )
    async def get_product_stats(
        self,
        product_id: str,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific product.
        
        Args:
            product_id: The Printify product ID
            max_pages: Number of order pages to analyze
            
        Returns:
            Dict with product statistics
        """
        try:
            # Get product details
            product = await self.get_product(product_id)
            
            # Analyze orders
            units_sold = 0
            order_count = 0
            orders_list = []
            
            for page in range(1, max_pages + 1):
                orders_result = await self.list_orders(limit=50, page=page)
                orders = orders_result.get("data", [])
                
                if not orders:
                    break
                
                for order in orders:
                    found_product = False
                    for item in order.get("line_items", []):
                        if str(item.get("product_id")) == str(product_id):
                            found_product = True
                            units_sold += int(item.get("quantity", 1))
                    
                    if found_product:
                        order_count += 1
                        orders_list.append({
                            "order_id": order.get("id"),
                            "status": order.get("status"),
                            "created_at": order.get("created_at")
                        })
            
            return {
                "product_id": product_id,
                "product_title": product.get("title"),
                "units_sold": units_sold,
                "order_count": order_count,
                "status": product.get("status"),
                "recent_orders": orders_list[:10]
            }
            
        except Exception as e:
            logger.error(f"Failed to get product stats: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to analyze product {product_id}"
            }
    
    @tool(
        name="printify_get_shop_stats",
        description="Get overall shop statistics from Printify including order counts and product counts",
        category="printify"
    )
    async def get_shop_stats(self, max_pages: int = 5) -> Dict[str, Any]:
        """
        Get overall shop statistics.
        
        Args:
            max_pages: Number of pages to analyze for orders
            
        Returns:
            Dict with shop statistics
        """
        try:
            # Get products
            products_result = await self.list_products(limit=100)
            products = products_result.get("data", [])
            
            # Get orders
            total_orders = 0
            total_items = 0
            status_counts = {}
            
            for page in range(1, max_pages + 1):
                orders_result = await self.list_orders(limit=50, page=page)
                orders = orders_result.get("data", [])
                
                if not orders:
                    break
                
                total_orders += len(orders)
                
                for order in orders:
                    status = order.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    line_items = order.get("line_items", [])
                    total_items += sum(int(item.get("quantity", 1)) for item in line_items)
            
            return {
                "total_products": len(products),
                "total_orders": total_orders,
                "total_items_sold": total_items,
                "order_status_breakdown": status_counts,
                "products_by_status": {
                    "published": len([p for p in products if p.get("visible", False)]),
                    "draft": len([p for p in products if not p.get("visible", False)])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get shop stats: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get shop statistics"
            }
    
    async def _get_blueprint_placeholders(
        self,
        blueprint_id: int,
        print_provider_id: int
    ) -> List[Dict]:
        """Get placeholder info for blueprint with ALL variant IDs properly grouped."""
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
        result = await self._request("GET", endpoint)
        
        # Collect ALL variant IDs that support each position
        placeholders = {}
        all_variant_ids = []
        
        for variant in result.get("variants", []):
            variant_id = variant.get("id")
            if variant_id:
                all_variant_ids.append(variant_id)
            
            for placeholder in variant.get("placeholders", []):
                pos = placeholder.get("position", "front")
                if pos not in placeholders:
                    placeholders[pos] = {
                        "position": pos,
                        "variant_ids": []
                    }
                # Add this variant to the position if not already added
                if variant_id and variant_id not in placeholders[pos]["variant_ids"]:
                    placeholders[pos]["variant_ids"].append(variant_id)
        
        # If no placeholders found, create a default one with all variants
        if not placeholders and all_variant_ids:
            placeholders["front"] = {
                "position": "front",
                "variant_ids": all_variant_ids
            }
        
        return list(placeholders.values())
    
    async def _get_default_variants(
        self,
        blueprint_id: int,
        print_provider_id: int
    ) -> List[Dict]:
        """Get default variant configuration."""
        result = await self.get_variants(blueprint_id, print_provider_id)
        
        variants = []
        for variant in result.get("variants", []):
            variants.append({
                "id": variant["id"],
                "price": 2999,  # $29.99 default
                "is_enabled": True
            })
        
        return variants

    async def _create_any_product(
        self,
        title: str,
        description: str,
        product_type: str,
        image_url: str,
        price_cents: int = 2499,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        UNIVERSAL product creator - works for ANY product type by auto-discovering everything.
        
        This is the core method that handles ANY product type available on Printify:
        - Beanies, socks, watches, clocks, coasters, journals, hoodies, etc.
        - Automatically discovers the right blueprint from Printify API
        - Automatically finds available print providers
        - Automatically gets variants and placeholders
        - Creates the product with all parameters filled in
        
        Args:
            title: Product title
            description: Product description
            product_type: Any product type (e.g., "beanie", "clock", "socks", "wall art")
            image_url: URL of the design image
            price_cents: Price in cents (default: 2499 = $24.99)
            tags: Optional product tags
        
        Returns:
            Dict with product info including success status
        """
        logger.info(f"🔧 Universal product creator: '{product_type}' - '{title}'")
        normalized = product_type.lower().strip()
        
        # Common aliases for better matching - EXPANDED for all product types
        search_aliases = {
            # Clock/time products
            "wall clock": "clock", "desk clock": "clock", "acrylic clock": "clock",
            "wrist watch": "watch", "wristwatch": "watch",
            # Home products
            "drink coasters": "coaster", "coaster set": "coaster", "coasters": "coaster",
            "cutting board": "cutting board", "cheese board": "cutting board",
            "beach towel": "towel", "bath towel": "towel", "hand towel": "towel",
            # Apparel accessories
            "knit cap": "beanie", "winter cap": "beanie", "knit beanie": "beanie",
            "crew sock": "socks", "dress socks": "socks", "athletic socks": "socks",
            "sock": "socks", "ankle socks": "socks", "tube socks": "socks",
            "dad cap": "dad hat", "baseball hat": "dad hat", "baseball cap": "cap",
            # Wall art
            "wall poster": "poster", "art poster": "poster",
            "wall canvas": "canvas", "canvas art": "canvas", "canvas print": "canvas",
            # Stationery
            "hardcover journal": "journal", "lined journal": "journal",
            "spiral notebook": "notebook", "ruled notebook": "notebook",
            # Novelty - ADDED playing cards
            "face mask": "mask", "fabric mask": "mask",
            "jigsaw puzzle": "puzzle", "jigsaw": "puzzle",
            "ornament": "ornament", "christmas ornament": "ornament", "xmas ornament": "ornament",
            "garden flag": "flag", "yard flag": "flag", "house flag": "flag",
            "playing cards": "playing card", "card deck": "playing card", "deck of cards": "playing card",
            "poker cards": "playing card", "cards": "playing card",
            # Bags
            "tote": "tote bag", "canvas bag": "tote bag", "shopping bag": "tote bag",
            "fanny pack": "fanny pack", "hip bag": "fanny pack", "belt bag": "fanny pack",
        }
        
        # Step 1: Try dynamic API search for the blueprint
        search_result = await self.search_blueprint(product_type)
        
        if not search_result:
            # Try with alias
            alias = search_aliases.get(normalized, normalized)
            if alias != normalized:
                logger.info(f"Trying alias: '{normalized}' → '{alias}'")
                search_result = await self.search_blueprint(alias)
        
        # Step 2: If dynamic search fails, fall back to static catalog
        if not search_result:
            logger.warning(f"Dynamic search failed for '{product_type}', trying static catalog...")
            
            # Check static catalog with various forms of the product type
            catalog_checks = [
                normalized,
                normalized.rstrip('s'),  # Remove trailing 's' (socks -> sock doesn't exist but try)
                search_aliases.get(normalized, normalized),
            ]
            
            for check in catalog_checks:
                if check in PRINTIFY_PRODUCT_CATALOG:
                    catalog_entry = PRINTIFY_PRODUCT_CATALOG[check]
                    search_result = {
                        "blueprint_id": catalog_entry["blueprint_id"],
                        "print_provider_id": catalog_entry["print_provider_id"],
                        "name": catalog_entry["name"],
                        "matched_from": f"static_catalog:{check}",
                        "all_providers": [catalog_entry["print_provider_id"]]
                    }
                    logger.info(f"✓ Found in static catalog: {catalog_entry['name']}")
                    break
        
        if not search_result:
            return {
                "success": False,
                "error": f"Could not find a Printify product matching '{product_type}'",
                "hint": "Try being more specific (e.g., 'knit beanie' instead of just 'hat')",
                "suggestion": "Use printify_list_all_products to see available product types",
                "tried": [product_type, normalized, search_aliases.get(normalized)]
            }
        
        blueprint_id = search_result["blueprint_id"]
        print_provider_id = search_result["print_provider_id"]
        product_name = search_result["name"]
        
        logger.info(f"✓ Found blueprint: {product_name} (ID: {blueprint_id}, Provider: {print_provider_id})")
        
        try:
            # Step 2: Upload the image
            logger.info(f"Uploading design image: {image_url[:50]}...")
            upload_result = await self.upload_image(image_url, f"{title.replace(' ', '_')}.png")
            
            if not upload_result or upload_result.get("success") == False:
                error_msg = upload_result.get("message") or upload_result.get("error") or "Unknown upload error"
                return {
                    "success": False,
                    "error": f"Image upload failed: {error_msg}",
                    "image_url": image_url
                }
            
            image_id = upload_result.get("id")
            if not image_id:
                return {
                    "success": False,
                    "error": "Failed to get image ID from upload",
                    "upload_result": upload_result
                }
            
            logger.info(f"✓ Image uploaded: {image_id}")
            
            # Step 3: Get variants from the API
            variants_result = await self.get_variants(blueprint_id, print_provider_id)
            variants = variants_result.get("variants", [])
            
            if not variants:
                # Try other providers - first from the search result, then fetch all
                logger.warning(f"No variants for provider {print_provider_id}, trying alternatives...")
                all_providers = search_result.get("all_providers", [])
                
                # If no providers cached, fetch them from the API
                if not all_providers or len(all_providers) <= 1:
                    logger.info(f"Fetching all providers for blueprint {blueprint_id}...")
                    providers = await self.get_print_providers(blueprint_id)
                    all_providers = [p.get("id") for p in providers if p.get("id")]
                    logger.info(f"Found {len(all_providers)} providers to try")
                
                for alt_provider in all_providers:
                    if alt_provider != print_provider_id:
                        try:
                            variants_result = await self.get_variants(blueprint_id, alt_provider)
                            variants = variants_result.get("variants", [])
                            if variants:
                                print_provider_id = alt_provider
                                logger.info(f"✓ Found {len(variants)} variants with provider {alt_provider}")
                                break
                        except Exception as e:
                            logger.debug(f"Provider {alt_provider} failed: {e}")
                            continue
            
            if not variants:
                return {
                    "success": False,
                    "error": f"No variants available for {product_name}. This product may not be available for custom printing.",
                    "blueprint_id": blueprint_id,
                    "print_provider_id": print_provider_id,
                    "hint": "Try a different product type or check if the product is available in your region",
                    "providers_tried": all_providers[:5] if all_providers else [print_provider_id]
                }
            
            # Limit variants to avoid API limits (usually 50-100 max)
            max_variants = min(len(variants), 50)
            selected_variants = variants[:max_variants]
            logger.info(f"Using {len(selected_variants)} of {len(variants)} variants")
            
            # Build variant list with pricing
            variant_list = []
            variant_ids = []
            for variant in selected_variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Step 4: Get placeholders and build print areas
            placeholders = await self._get_blueprint_placeholders(blueprint_id, print_provider_id)
            
            print_areas = []
            if placeholders:
                for placeholder in placeholders:
                    # Only include variant IDs that are in our selected variants
                    placeholder_variant_ids = [v for v in placeholder.get("variant_ids", []) if v in variant_ids]
                    if placeholder_variant_ids:
                        print_areas.append({
                            "variant_ids": placeholder_variant_ids,
                            "placeholders": [{
                                "position": placeholder.get("position", "front"),
                                "images": [{
                                    "id": image_id,
                                    "x": 0.5,
                                    "y": 0.5,
                                    "scale": 1.0,
                                    "angle": 0
                                }]
                            }]
                        })
            
            # Fallback: create default print area if none built
            if not print_areas:
                print_areas = [{
                    "variant_ids": variant_ids,
                    "placeholders": [{
                        "position": "front",
                        "images": [{
                            "id": image_id,
                            "x": 0.5,
                            "y": 0.5,
                            "scale": 1.0,
                            "angle": 0
                        }]
                    }]
                }]
            
            logger.info(f"Built {len(print_areas)} print areas covering {len(variant_ids)} variants")
            
            # Step 5: Create the product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            if tags:
                product_data["tags"] = tags
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            product_id = result.get("id")
            logger.info(f"✓ Product created: {product_id}")
            
            # Step 6: Auto-publish to Shopify
            published = False
            shopify_status = "draft"
            try:
                await self.publish_product(product_id, visible=True)
                published = True
                shopify_status = "live"
                logger.info(f"✓ Published to Shopify: {product_id}")
            except Exception as pub_error:
                logger.warning(f"Auto-publish failed: {pub_error}")
            
            return {
                "success": True,
                "product_id": product_id,
                "title": title,
                "product_type": product_name,
                "original_request": product_type,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "image_id": image_id,
                "variants_count": len(variant_list),
                "price": price_cents / 100.0,
                "published": published,
                "shopify_status": shopify_status,
                "product_url": f"https://printify.com/app/products/{product_id}",
                "note": f"{product_name} is now LIVE on your store" if published else f"{product_name} created but not yet published"
            }
            
        except Exception as e:
            logger.error(f"Universal product creation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "product_type": product_type,
                "blueprint_found": product_name if search_result else None,
                "blueprint_id": blueprint_id if search_result else None
            }

    @tool(
        name="printify_create_tshirt",
        description="Create a t-shirt product on Printify with a design image. This is a simplified helper that handles all the complexity automatically.",
        category="printify"
    )
    async def create_tshirt(
        self,
        title: str,
        description: str,
        image_url: str = None,
        image_path: str = None,  # Alias for image_url
        design_url: str = None,  # Alias for image_url
        design_image_url: str = None,  # Alias for image_url
        price_cents: int = 2499,
        price: float = None,  # Alias for price_cents (will convert dollars to cents)
        blueprint_id: int = 6,  # Gildan 5000 by default
        print_provider_id: int = 99  # Monster Digital by default
    ) -> Dict[str, Any]:
        """
        Create a t-shirt product on Printify - simplified helper.
        
        This method handles all the complexity of:
        1. Uploading the image
        2. Getting variants
        3. Setting up print areas
        4. Creating the product
        
        Args:
            title: Product title
            description: Product description
            image_url: URL of the design image
            image_path: Alias for image_url
            price_cents: Price in cents (default 2499 = $24.99)
            blueprint_id: Blueprint ID (default 6 = Gildan 5000 Heavy Cotton Tee)
            print_provider_id: Provider ID (default 99 = Monster Digital)
            
        Returns:
            Dict with created product info
        """
        # Handle image_url alias
        actual_url = image_url or image_path or design_url or design_image_url
        if not actual_url:
            raise ValueError("Must provide image_url or image_path parameter")
        
        # Handle price parameter - convert dollars to cents if needed
        if price is not None:
            price_cents = int(price * 100)  # Convert $24.99 to 2499 cents
        
        try:
            # Step 1: Upload the image
            logger.info(f"Uploading design image: {actual_url}")
            upload_result = await self.upload_image(actual_url, f"{title.replace(' ', '_')}.png")
            
            # Check if upload failed
            if not upload_result or upload_result.get("success") == False:
                error_msg = upload_result.get("message") or upload_result.get("error") or "Unknown upload error"
                raise Exception(f"Image upload failed: {error_msg}")
            
            image_id = upload_result.get("id")
            if not image_id:
                raise Exception("Failed to get image ID from upload result")
            
            logger.info(f"Image uploaded successfully: {image_id}")
            
            # Step 2: Get variants and placeholders
            variants_result = await self.get_variants(blueprint_id, print_provider_id)
            variants = variants_result.get("variants", [])
            
            if not variants:
                raise Exception("No variants available for this product")
            
            # Build variant list with pricing
            # Limit to 20 variants to avoid API "max 100 variants" errors
            limited_variants = variants[:20]
            logger.info(f"Using {len(limited_variants)} of {len(variants)} variants to stay within API limits")
            
            variant_list = []
            variant_ids = []
            for variant in limited_variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Step 3: Build print areas
            print_areas = [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
            
            # Step 4: Create the product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            product_id = result.get("id")
            logger.info(f"T-shirt created successfully: {product_id}")
            
            # Automatically publish the product with visible=True for Shopify
            try:
                publish_result = await self.publish_product(product_id, visible=True)
                logger.info(f"✓ T-shirt published to Shopify: {product_id}")
                published = True
                shopify_status = "live"
            except Exception as pub_error:
                logger.warning(f"Failed to auto-publish t-shirt: {pub_error}")
                published = False
                shopify_status = "draft"
            
            actual_price = price_cents / 100.0
            
            return {
                "success": True,
                "product_id": product_id,
                "title": title,
                "image_id": image_id,
                "variants_count": len(variant_list),
                "published": published,
                "shopify_status": shopify_status,
                "price": actual_price,
                "product_url": f"https://printify.com/app/products/{product_id}",
                "note": "Product is now LIVE on your Shopify store" if published else "Product created but not yet live on Shopify"
            }
            
        except Exception as e:
            logger.error(f"Failed to create t-shirt: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "tshirt_creation_failed",
                "message": f"Could not create t-shirt on Printify: {str(e)}",
                "troubleshooting": "Check Printify API credentials and image URL validity"
            }

    @tool(
        name="printify_create_mug",
        description="Create a mug product on Printify with a design image. This is a simplified helper that handles all the complexity automatically.",
        category="printify"
    )
    async def create_mug(
        self,
        title: str,
        description: str,
        image_url: str = None,
        image_path: str = None,  # Alias for image_url
        design_url: str = None,  # Alias for image_url
        design_image_url: str = None,  # Alias for image_url
        price_cents: int = 1499,
        price: float = None,  # Alias for price_cents (will convert dollars to cents)
        blueprint_id: int = None,  # Will auto-discover if not provided
        print_provider_id: int = None  # Will auto-discover if not provided
    ) -> Dict[str, Any]:
        """
        Create a mug product on Printify - simplified helper.
        
        This method handles all the complexity of:
        1. Auto-discovering valid mug blueprints if not specified
        2. Uploading the image
        3. Getting variants
        4. Setting up print areas
        5. Creating the product
        
        Args:
            title: Product title
            description: Product description
            image_url: URL of the design image
            image_path: Alias for image_url
            price_cents: Price in cents (default 1499 = $14.99)
            blueprint_id: Blueprint ID (auto-discovers if not provided)
            print_provider_id: Provider ID (auto-discovers if not provided)
            
        Returns:
            Dict with created product info
        """
        # Handle image_url alias
        actual_url = image_url or image_path or design_url or design_image_url
        if not actual_url:
            raise ValueError("Must provide image_url or image_path parameter")
        
        # Handle price parameter - convert dollars to cents if needed
        if price is not None:
            price_cents = int(price * 100)  # Convert $19.99 to 1999 cents
        
        # Auto-discover mug blueprint if not specified
        if blueprint_id is None or print_provider_id is None:
            logger.info("Auto-discovering mug blueprint...")
            try:
                blueprints_result = await self.list_blueprints()
                blueprints = blueprints_result if isinstance(blueprints_result, list) else []
                
                # Find a mug blueprint
                for bp in blueprints:
                    if "mug" in bp.get("title", "").lower():
                        blueprint_id = bp.get("id")
                        logger.info(f"Found mug blueprint: {bp.get('title')} (ID: {blueprint_id})")
                        
                        # Get first available provider
                        providers = await self.get_print_providers(blueprint_id)
                        if isinstance(providers, list) and providers:
                            print_provider_id = providers[0].get("id")
                            logger.info(f"Using provider: {providers[0].get('title')} (ID: {print_provider_id})")
                            break
                
                # Fallback to defaults if discovery fails
                if blueprint_id is None:
                    logger.warning("Auto-discovery failed, using default blueprint 12")
                    blueprint_id = 12
                    print_provider_id = 28
            except Exception as e:
                logger.error(f"Blueprint auto-discovery error: {e}, using defaults")
                blueprint_id = 12
                print_provider_id = 28
        
        try:
            # Step 1: Upload the image
            logger.info(f"Uploading design image: {actual_url}")
            upload_result = await self.upload_image(actual_url, f"{title.replace(' ', '_')}_mug.png")
            
            # Check if upload failed
            if not upload_result or upload_result.get("success") == False:
                error_msg = upload_result.get("message") or upload_result.get("error") or "Unknown upload error"
                raise Exception(f"Image upload failed: {error_msg}")
            
            image_id = upload_result.get("id")
            if not image_id:
                raise Exception("Failed to get image ID from upload result")
            
            logger.info(f"Image uploaded successfully: {image_id}")
            
            # Step 2: Get variants and placeholders
            variants_result = await self.get_variants(blueprint_id, print_provider_id)
            variants = variants_result.get("variants", [])
            
            if not variants:
                raise Exception("No variants available for this product")
            
            # Build variant list with pricing
            # Limit to 20 variants to avoid API "max 100 variants" errors
            limited_variants = variants[:20]
            logger.info(f"Using {len(limited_variants)} of {len(variants)} variants to stay within API limits")
            
            variant_list = []
            variant_ids = []
            for variant in limited_variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Step 3: Build print areas (mugs typically have "front" area)
            print_areas = [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
            
            # Step 4: Create the product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            product_id = result.get("id")
            logger.info(f"Mug created successfully: {product_id}")
            
            # Automatically publish the product with visible=True for Shopify
            try:
                publish_result = await self.publish_product(product_id, visible=True)
                logger.info(f"✓ Mug published to Shopify: {product_id}")
                published = True
                shopify_status = "live"
            except Exception as pub_error:
                logger.warning(f"Failed to auto-publish mug: {pub_error}")
                published = False
                shopify_status = "draft"
            
            actual_price = price_cents / 100.0
            
            return {
                "success": True,
                "product_id": product_id,
                "title": title,
                "image_id": image_id,
                "variants_count": len(variant_list),
                "published": published,
                "shopify_status": shopify_status,
                "price": actual_price,
                "product_url": f"https://printify.com/app/products/{product_id}",
                "note": "Product is now LIVE on your Shopify store" if published else "Product created but not yet live on Shopify"
            }
            
        except Exception as e:
            logger.error(f"Failed to create mug: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "mug_creation_failed",
                "message": f"Could not create mug on Printify: {str(e)}",
                "troubleshooting": "Check Printify API credentials and image URL validity"
            }

    @tool(
        name="printify_create_notebook",
        description="Create a spiral notebook product on Printify with a cover design image. Perfect for journals, planners, and note-taking products.",
        category="printify"
    )
    async def create_notebook(
        self,
        title: str,
        description: str,
        image_url: str = None,
        image_path: str = None,  # Alias for image_url
        design_url: str = None,  # Alias for image_url
        design_image_url: str = None,  # Alias for image_url
        price_cents: int = 1999,
        price: float = None,  # Alias for price_cents (will convert dollars to cents)
        blueprint_id: int = None,  # Will auto-discover if not provided
        print_provider_id: int = None  # Will auto-discover if not provided
    ) -> Dict[str, Any]:
        """
        Create a spiral notebook product on Printify - simplified helper.
        
        This method handles all the complexity of:
        1. Auto-discovering valid notebook blueprints if not specified
        2. Uploading the cover design image
        3. Getting variants (ruled, blank, graph paper)
        4. Setting up print areas for front cover
        5. Creating the product
        
        Args:
            title: Product title
            description: Product description
            image_url: URL of the cover design image
            image_path: Alias for image_url
            price_cents: Price in cents (default 1999 = $19.99)
            blueprint_id: Blueprint ID (auto-discovers if not provided)
            print_provider_id: Provider ID (auto-discovers if not provided)
            
        Returns:
            Dict with created product info
        """
        # Handle image_url alias
        actual_url = image_url or image_path or design_url or design_image_url
        if not actual_url:
            raise ValueError("Must provide image_url or image_path parameter with the notebook cover design")
        
        # Handle price parameter - convert dollars to cents if needed
        if price is not None:
            price_cents = int(price * 100)  # Convert $19.99 to 1999 cents
        
        # Auto-discover notebook blueprint if not specified
        if blueprint_id is None or print_provider_id is None:
            logger.info("Auto-discovering notebook blueprint...")
            try:
                blueprints_result = await self.list_blueprints()
                blueprints = blueprints_result if isinstance(blueprints_result, list) else []
                
                # Find a notebook/journal blueprint
                for bp in blueprints:
                    bp_title = bp.get("title", "").lower()
                    if "notebook" in bp_title or "journal" in bp_title:
                        blueprint_id = bp.get("id")
                        logger.info(f"Found notebook blueprint: {bp.get('title')} (ID: {blueprint_id})")
                        
                        # Get first available provider
                        providers = await self.get_print_providers(blueprint_id)
                        if isinstance(providers, list) and providers:
                            print_provider_id = providers[0].get("id")
                            logger.info(f"Using provider: {providers[0].get('title')} (ID: {print_provider_id})")
                            break
                
                # Fallback to hardcover journal if spiral not found
                if blueprint_id is None:
                    logger.warning("Auto-discovery failed, trying hardcover journal blueprint 630")
                    blueprint_id = 630
                    providers = await self.get_print_providers(blueprint_id)
                    if isinstance(providers, list) and providers:
                        print_provider_id = providers[0].get("id")
                    else:
                        print_provider_id = 56
            except Exception as e:
                logger.error(f"Blueprint auto-discovery error: {e}, using hardcover journal defaults")
                blueprint_id = 630  # Hardcover journal as fallback
                print_provider_id = 56
        
        try:
            # Step 1: Upload the cover image
            logger.info(f"Uploading notebook cover design: {actual_url}")
            upload_result = await self.upload_image(actual_url, f"{title.replace(' ', '_')}_notebook.png")
            
            # Check if upload failed
            if not upload_result or upload_result.get("success") == False:
                error_msg = upload_result.get("message") or upload_result.get("error") or "Unknown upload error"
                raise Exception(f"Image upload failed: {error_msg}")
            
            image_id = upload_result.get("id")
            if not image_id:
                raise Exception("Failed to get image ID from upload result")
            
            logger.info(f"Cover image uploaded successfully: {image_id}")
            
            # Step 2: Get variants
            variants_result = await self.get_variants(blueprint_id, print_provider_id)
            variants = variants_result.get("variants", [])
            
            if not variants:
                # Try to discover print providers if default doesn't work
                logger.warning(f"No variants found for provider {print_provider_id}, trying auto-discovery")
                providers = await self.get_print_providers(blueprint_id)
                if isinstance(providers, list) and providers:
                    for provider in providers:
                        print_provider_id = provider.get("id")
                        variants_result = await self.get_variants(blueprint_id, print_provider_id)
                        variants = variants_result.get("variants", [])
                        if variants:
                            logger.info(f"Found variants with provider {print_provider_id}")
                            break
            
            if not variants:
                raise Exception("No variants available for this notebook product. Please check blueprint and provider IDs.")
            
            # Build variant list with pricing
            # Limit to 20 variants to avoid API limits
            limited_variants = variants[:20]
            logger.info(f"Using {len(limited_variants)} of {len(variants)} notebook variants")
            
            variant_list = []
            variant_ids = []
            for variant in limited_variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Step 3: Build print areas (notebook has "front" for cover design)
            print_areas = [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
            
            # Step 4: Create the product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            product_id = result.get("id")
            logger.info(f"Notebook created successfully: {product_id}")
            
            # Automatically publish the product with visible=True for Shopify
            try:
                publish_result = await self.publish_product(product_id, visible=True)
                logger.info(f"✓ Notebook published to Shopify: {product_id}")
                published = True
                shopify_status = "live"
            except Exception as pub_error:
                logger.warning(f"Failed to auto-publish notebook: {pub_error}")
                published = False
                shopify_status = "draft"
            
            actual_price = price_cents / 100.0
            
            return {
                "success": True,
                "product_id": product_id,
                "title": title,
                "image_id": image_id,
                "variants_count": len(variant_list),
                "published": published,
                "shopify_status": shopify_status,
                "price": actual_price,
                "product_url": f"https://printify.com/app/products/{product_id}",
                "product_type": "notebook",
                "note": "Notebook is now LIVE on your Shopify store" if published else "Notebook created but not yet live on Shopify"
            }
            
        except Exception as e:
            logger.error(f"Failed to create notebook: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "notebook_creation_failed",
                "message": f"Could not create notebook on Printify: {str(e)}",
                "troubleshooting": "Check Printify API credentials, image URL validity, and ensure notebook blueprint is available"
            }

    @tool(
        name="printify_create_wall_art",
        description="Create wall art products on Printify (canvas, framed posters, metal prints). Auto-discovers available products.",
        category="printify"
    )
    async def create_wall_art(
        self,
        title: str,
        description: str,
        image_url: str = None,
        image_path: str = None,
        design_url: str = None,
        design_image_url: str = None,
        product_type: str = "canvas",  # canvas, framed, poster, metal
        price_cents: int = 4999,
        price: float = None
    ) -> Dict[str, Any]:
        """
        Create wall art products on Printify (canvas, framed prints, posters, metal prints).
        
        This method auto-discovers available wall art blueprints and handles all complexity.
        
        Args:
            title: Product title
            description: Product description
            image_url: URL of the design image
            product_type: Type of wall art - "canvas", "framed", "poster", or "metal"
            price_cents: Price in cents (default 4999 = $49.99)
            price: Price in dollars (alternative to price_cents)
            
        Returns:
            Dict with created product info
        """
        # Handle image_url aliases
        actual_url = image_url or image_path or design_url or design_image_url
        if not actual_url:
            raise ValueError("Must provide image_url parameter")
        
        # Handle price conversion
        if price is not None:
            price_cents = int(price * 100)
        
        # Wall art blueprint IDs - these are common Printify blueprints
        # Note: Availability varies by region and provider
        WALL_ART_BLUEPRINTS = {
            "canvas": [
                {"id": 384, "name": "Canvas (Stretched)", "provider": 29},
                {"id": 607, "name": "Canvas Print", "provider": 99},
            ],
            "framed": [
                {"id": 643, "name": "Framed Paper Poster", "provider": 99},
                {"id": 594, "name": "Framed Canvas", "provider": 29},
                {"id": 186, "name": "Framed poster", "provider": 27},
            ],
            "poster": [
                {"id": 252, "name": "Premium Poster", "provider": 27},
                {"id": 1, "name": "Poster", "provider": 99},
                {"id": 641, "name": "Paper Poster", "provider": 99},
            ],
            "metal": [
                {"id": 599, "name": "Metal Print", "provider": 99},
                {"id": 385, "name": "Metal Wall Art", "provider": 29},
            ]
        }
        
        product_type_lower = product_type.lower()
        if product_type_lower not in WALL_ART_BLUEPRINTS:
            product_type_lower = "canvas"  # Default to canvas
        
        blueprints_to_try = WALL_ART_BLUEPRINTS.get(product_type_lower, [])
        
        try:
            # First, try to auto-discover available wall art blueprints
            logger.info(f"Discovering {product_type} blueprints...")
            
            # Try each blueprint option until one works
            working_blueprint = None
            working_provider = None
            
            # First try the known blueprints
            for bp in blueprints_to_try:
                try:
                    logger.info(f"Trying blueprint {bp['id']} ({bp['name']})...")
                    # Check if this blueprint/provider combo is available
                    variants_result = await self.get_variants(bp['id'], bp['provider'])
                    variants = variants_result.get("variants", [])
                    if variants:
                        working_blueprint = bp['id']
                        working_provider = bp['provider']
                        logger.info(f"✓ Found working blueprint: {bp['name']} with {len(variants)} variants")
                        break
                except Exception as e:
                    logger.debug(f"Blueprint {bp['id']} not available: {e}")
                    continue
            
            # If no known blueprints work, try to discover from catalog
            if not working_blueprint:
                logger.info("Searching catalog for wall art products...")
                try:
                    all_blueprints = await self.list_blueprints()
                    if isinstance(all_blueprints, list):
                        search_terms = {
                            "canvas": ["canvas"],
                            "framed": ["frame", "framed"],
                            "poster": ["poster", "print"],
                            "metal": ["metal"]
                        }
                        terms = search_terms.get(product_type_lower, ["canvas", "poster", "print"])
                        
                        for bp in all_blueprints:
                            bp_title = bp.get("title", "").lower()
                            if any(term in bp_title for term in terms):
                                # Get providers for this blueprint
                                try:
                                    providers = await self.get_print_providers(bp['id'])
                                    if isinstance(providers, list) and providers:
                                        for prov in providers:
                                            try:
                                                variants_result = await self.get_variants(bp['id'], prov['id'])
                                                if variants_result.get("variants"):
                                                    working_blueprint = bp['id']
                                                    working_provider = prov['id']
                                                    logger.info(f"✓ Discovered: {bp.get('title')} (ID: {bp['id']}) with provider {prov.get('title')}")
                                                    break
                                            except:
                                                continue
                                        if working_blueprint:
                                            break
                                except:
                                    continue
                            if working_blueprint:
                                break
                except Exception as e:
                    logger.error(f"Catalog search failed: {e}")
            
            if not working_blueprint:
                return {
                    "success": False,
                    "error": f"No {product_type} products available",
                    "message": f"Could not find any available {product_type} products in your Printify catalog. This may be a regional availability issue.",
                    "suggestion": "Try a different product type (canvas, poster, framed, metal) or check Printify's catalog in your region."
                }
            
            # Now create the product using the working blueprint
            logger.info(f"Creating {product_type} with blueprint {working_blueprint}, provider {working_provider}")
            
            # Upload the image
            upload_result = await self.upload_image(actual_url, f"{title.replace(' ', '_')}.png")
            if not upload_result or upload_result.get("success") == False:
                error_msg = upload_result.get("message") or upload_result.get("error") or "Unknown upload error"
                raise Exception(f"Image upload failed: {error_msg}")
            
            image_id = upload_result.get("id")
            if not image_id:
                raise Exception("Failed to get image ID from upload")
            
            # Get variants
            variants_result = await self.get_variants(working_blueprint, working_provider)
            variants = variants_result.get("variants", [])
            
            # Limit variants and build list
            limited_variants = variants[:15]
            variant_list = []
            variant_ids = []
            for variant in limited_variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Build print areas
            print_areas = [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
            
            # Create product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": working_blueprint,
                "print_provider_id": working_provider,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            product_id = result.get("id")
            logger.info(f"Wall art created: {product_id}")
            
            # Publish with visible=True for immediate Shopify visibility
            published = False
            shopify_status = "draft"
            try:
                await self.publish_product(product_id, visible=True)
                published = True
                shopify_status = "live"
                logger.info(f"✓ Wall art published to Shopify: {product_id}")
            except Exception as pub_error:
                logger.warning(f"Auto-publish failed: {pub_error}")
            
            return {
                "success": True,
                "product_id": product_id,
                "product_type": product_type,
                "blueprint_id": working_blueprint,
                "title": title,
                "variants_count": len(variant_list),
                "published": published,
                "shopify_status": shopify_status,
                "price": price_cents / 100,
                "product_url": f"https://printify.com/app/products/{product_id}",
                "note": "Product is now LIVE on your Shopify store" if published else "Product created but not yet live on Shopify"
            }
            
        except Exception as e:
            logger.error(f"Failed to create wall art: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Could not create {product_type} on Printify: {str(e)}",
                "troubleshooting": "Check image URL validity and Printify API credentials"
            }

    @tool(
        name="printify_create_coaster",
        description="Create coaster products on Printify with a design image. Auto-discovers available coaster blueprints.",
        category="printify"
    )
    async def create_coaster(
        self,
        title: str,
        description: str,
        image_url: str = None,
        image_path: str = None,  # Alias for image_url
        design_url: str = None,  # Alias for image_url
        design_image_url: str = None,  # Alias for image_url
        price_cents: int = 1299,
        price: float = None,  # Alias for price_cents (will convert dollars to cents)
        blueprint_id: int = None,  # Will auto-discover if not provided
        print_provider_id: int = None  # Will auto-discover if not provided
    ) -> Dict[str, Any]:
        """
        Create a coaster product on Printify - simplified helper.
        
        This method handles all the complexity of:
        1. Auto-discovering valid coaster blueprints if not specified
        2. Uploading the design image
        3. Getting variants
        4. Setting up print areas
        5. Creating the product
        
        Args:
            title: Product title
            description: Product description
            image_url: URL of the design image
            image_path: Alias for image_url
            price_cents: Price in cents (default 1299 = $12.99)
            blueprint_id: Blueprint ID (auto-discovers if not provided)
            print_provider_id: Provider ID (auto-discovers if not provided)
            
        Returns:
            Dict with created product info
        """
        # Handle image_url alias
        actual_url = image_url or image_path or design_url or design_image_url
        if not actual_url:
            raise ValueError("Must provide image_url or image_path parameter")
        
        # Handle price parameter - convert dollars to cents if needed
        if price is not None:
            price_cents = int(price * 100)
        
        # Auto-discover coaster blueprint if not specified
        if blueprint_id is None or print_provider_id is None:
            logger.info("Auto-discovering coaster blueprint...")
            try:
                blueprints_result = await self.list_blueprints()
                blueprints = blueprints_result if isinstance(blueprints_result, list) else []
                
                # Find a coaster blueprint
                for bp in blueprints:
                    bp_title = bp.get("title", "").lower()
                    if "coaster" in bp_title:
                        blueprint_id = bp.get("id")
                        logger.info(f"Found coaster blueprint: {bp.get('title')} (ID: {blueprint_id})")
                        
                        # Get first available provider
                        providers = await self.get_print_providers(blueprint_id)
                        if isinstance(providers, list) and providers:
                            print_provider_id = providers[0].get("id")
                            logger.info(f"Using provider: {providers[0].get('title')} (ID: {print_provider_id})")
                            break
                
                # Fallback to mousepad if coaster not found (similar product)
                if blueprint_id is None:
                    logger.warning("No coaster blueprint found, trying mouse pad as alternative (389)")
                    blueprint_id = 389
                    providers = await self.get_print_providers(blueprint_id)
                    if isinstance(providers, list) and providers:
                        print_provider_id = providers[0].get("id")
                    else:
                        print_provider_id = 56
            except Exception as e:
                logger.error(f"Blueprint auto-discovery error: {e}, using mousepad as fallback")
                blueprint_id = 389
                print_provider_id = 56
        
        try:
            # Step 1: Upload the image
            logger.info(f"Uploading coaster design image: {actual_url}")
            upload_result = await self.upload_image(actual_url, f"{title.replace(' ', '_')}_coaster.png")
            
            # Check if upload failed
            if not upload_result or upload_result.get("success") == False:
                error_msg = upload_result.get("message") or upload_result.get("error") or "Unknown upload error"
                raise Exception(f"Image upload failed: {error_msg}")
            
            image_id = upload_result.get("id")
            if not image_id:
                raise Exception("Failed to get image ID from upload result")
            
            logger.info(f"Image uploaded successfully: {image_id}")
            
            # Step 2: Get variants
            variants_result = await self.get_variants(blueprint_id, print_provider_id)
            variants = variants_result.get("variants", [])
            
            if not variants:
                # Try to discover print providers if default doesn't work
                logger.warning(f"No variants found for provider {print_provider_id}, trying auto-discovery")
                providers = await self.get_print_providers(blueprint_id)
                if isinstance(providers, list) and providers:
                    for provider in providers:
                        print_provider_id = provider.get("id")
                        variants_result = await self.get_variants(blueprint_id, print_provider_id)
                        variants = variants_result.get("variants", [])
                        if variants:
                            logger.info(f"Found variants with provider {print_provider_id}")
                            break
            
            if not variants:
                raise Exception("No variants available for this product")
            
            # Limit variants
            limited_variants = variants[:15]
            logger.info(f"Using {len(limited_variants)} of {len(variants)} variants")
            
            variant_list = []
            variant_ids = []
            for variant in limited_variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Step 3: Build print areas
            print_areas = [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
            
            # Step 4: Create the product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            product_id = result.get("id")
            logger.info(f"Coaster created successfully: {product_id}")
            
            # Automatically publish the product with visible=True for Shopify
            try:
                publish_result = await self.publish_product(product_id, visible=True)
                logger.info(f"✓ Coaster published to Shopify: {product_id}")
                published = True
                shopify_status = "live"
            except Exception as pub_error:
                logger.warning(f"Failed to auto-publish coaster: {pub_error}")
                published = False
                shopify_status = "draft"
            
            actual_price = price_cents / 100.0
            
            return {
                "success": True,
                "product_id": product_id,
                "title": title,
                "image_id": image_id,
                "variants_count": len(variant_list),
                "published": published,
                "shopify_status": shopify_status,
                "price": actual_price,
                "product_url": f"https://printify.com/app/products/{product_id}",
                "product_type": "coaster",
                "note": "Coaster is now LIVE on your Shopify store" if published else "Coaster created but not yet live on Shopify"
            }
            
        except Exception as e:
            logger.error(f"Failed to create coaster: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "coaster_creation_failed",
                "message": f"Could not create coaster on Printify: {str(e)}",
                "troubleshooting": "Check Printify API credentials, image URL validity, and ensure coaster blueprint is available"
            }