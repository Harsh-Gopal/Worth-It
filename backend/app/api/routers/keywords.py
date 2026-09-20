from fastapi import APIRouter

router = APIRouter()

# Data-driven keyword categorization matching project needs
KEYWORD_CATEGORIES = {
    "Sports & Fitness": [
        "Protein", "Whey", "Creatine", "Oats", "Peanut Butter", "Energy Drink", "Yoga Mat", "Dumbbells"
    ],
    "Beauty & Grooming": [
        "Shampoo", "Face Wash", "Body Wash", "Deodorant", "Perfume", "Hair Oil", "Sunscreen", "Moisturizer"
    ],
    "Baby Care": [
        "Diapers", "Baby Wipes", "Baby Powder", "Baby Lotion", "Baby Food", "Cerelac", "Rash Cream"
    ],
    "Snacks & Beverages": [
        "Chips", "Nachos", "Cold Drink", "Juice", "Biscuits", "Cookies", "Chocolate", "Ice Cream", "Tea", "Coffee"
    ],
    "Pet Care": [
        "Dog Food", "Cat Food", "Pet Treats", "Cat Litter", "Dog Shampoo", "Pet Toys", "Chew Sticks"
    ],
    "Home & Kitchen": [
        "Detergent", "Dishwash Liquid", "Floor Cleaner", "Toilet Cleaner", "Garbage Bags", "Tissue Paper", "Foil"
    ],
    "Electronics": [
        "Batteries", "Charging Cable", "Earphones", "Power Bank", "Extension Board", "Bulb", "Smart Plug"
    ],
    "Daily Essentials": [
        "Milk", "Bread", "Eggs", "Butter", "Cheese", "Paneer", "Curd", "Atta", "Rice", "Dal", "Oil"
    ]
}

@router.get("/")
@router.get("")
async def get_keyword_suggestions():
    """
    Returns categorized keyword suggestions.
    Responds to both /api/keywords and /api/keywords/ (with or without trailing slash).
    """
    return {
        "categories": KEYWORD_CATEGORIES
    }
