import os
import json
import re
from datetime import date

EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Education",
    "Health & Medical",
    "Utilities",
    "Rent & Housing",
    "Personal Care",
    "Travel",
    "Subscriptions",
    "Groceries",
    "Sports & Fitness",
    "Gifts & Donations",
    "Other"
]


def is_openai_configured() -> bool:
    groq_key = os.environ.get('GROQ_API_KEY', '').strip()
    if groq_key and not groq_key.startswith('your_') and len(groq_key) > 10:
        return True
    openai_key = os.environ.get('OPENAI_API_KEY', '').strip()
    return bool(openai_key and not openai_key.startswith('your_') and not openai_key.startswith('sk-fake') and len(openai_key) > 20)


def get_client():
    """Return tuple of (client, model_name). Prefers Groq (100% free) then OpenAI."""
    groq_key = os.environ.get('GROQ_API_KEY', '').strip()
    if groq_key and not groq_key.startswith('your_') and len(groq_key) > 10:
        try:
            from openai import OpenAI
            return OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1"), "openai/gpt-oss-120b"
        except Exception as e:
            print(f"Groq init notice: {e}")

    openai_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if openai_key and not openai_key.startswith('your_') and not openai_key.startswith('sk-fake') and len(openai_key) > 20:
        try:
            from openai import OpenAI
            return OpenAI(api_key=openai_key), "gpt-4o-mini"
        except Exception as e:
            print(f"OpenAI init notice: {e}")

    return None, None


def categorize_expense(description: str, amount: float = 0.0) -> str:
    """Categorize expense using Groq/OpenAI if configured, otherwise rule-based categorizer."""
    desc = (description or '').strip()
    if not desc:
        return "Other"

    client, model = get_client()
    if client:
        try:
            prompt = f"""You are an expense categorization system for college students in India.
Categorize the following expense into exactly one of these categories:
{', '.join(EXPENSE_CATEGORIES)}

Expense Description: {desc}
Amount: ₹{amount}

Respond with ONLY the exact category name, nothing else."""

            extra_params = {}
            if "groq.com" in str(getattr(client, 'base_url', '')):
                extra_params["extra_body"] = {"reasoning_format": "hidden"}

            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
                temperature=0.0,
                **extra_params
            )
            raw_category = (resp.choices[0].message.content or "").strip()
            clean_category = raw_category.strip("`'\"* \t\n.,")

            # 1. Exact match
            if clean_category in EXPENSE_CATEGORIES:
                return clean_category

            # 2. Case-insensitive exact match
            for cat in EXPENSE_CATEGORIES:
                if cat.lower() == clean_category.lower():
                    return cat

            # 3. Whole-word category match in LLM response
            for cat in EXPENSE_CATEGORIES:
                if re.search(rf"\b{re.escape(cat)}\b", raw_category, re.IGNORECASE):
                    return cat

        except Exception as e:
            print(f"AI categorize notice, using rule-based fallback: {e}")

    return _rule_based_categorize(desc)


def _rule_based_categorize(description: str) -> str:
    """Smart keyword and pattern based categorizer tailored for college students in India."""
    desc = (description or '').lower().strip()
    if not desc:
        return "Other"

    rules = {
        "Food & Dining": [
            "zomato", "swiggy", "domino", "dominos", "pizza", "burger", "mcdonald", "mcdonalds", "kfc", "subway",
            "cafe", "coffee", "starbucks", "chai", "tea", "canteen", "mess", "lunch",
            "dinner", "breakfast", "biryani", "dhaba", "restaurant", "food", "snack", "snacks", "eat",
            "shawarma", "dosa", "idli", "vada", "sambar", "uttapam", "thali", "paneer", "paratha",
            "roti", "bhature", "chole", "pav bhaji", "samosa", "kachori", "momos", "maggi",
            "noodles", "roll", "chaat", "sweet", "mithai", "ice cream", "juice", "shake",
            "lassi", "bhojanalaya", "sweets", "bakery", "pastry", "cake", "beverage", "dining"
        ],
        "Transportation": [
            "uber", "ola", "rapido", "auto", "autorickshaw", "rickshaw", "bus", "metro", "train", "cab", "taxi",
            "petrol", "fuel", "diesel", "bike", "scooter", "fare", "toll", "parking", "commute", "transit", "ticket",
            "railway", "local train"
        ],
        "Groceries": [
            "grocery", "groceries", "kirana", "dmart", "bigbasket", "blinkit", "zepto", "instamart",
            "vegetables", "fruits", "milk", "bread", "eggs", "supermarket", "ration", "provisions", "dairy"
        ],
        "Shopping": [
            "amazon", "flipkart", "myntra", "ajio", "meesho", "zara", "h&m", "clothes", "clothing",
            "shirt", "t-shirt", "jeans", "pants", "trousers", "shoes", "sneakers", "shopping", "mall", "electronics",
            "keyboard", "mouse", "headphones", "earbuds", "watch", "outfit", "apparel"
        ],
        "Entertainment": [
            "netflix", "prime", "hotstar", "youtube", "spotify", "apple music", "movie", "movies",
            "cinema", "pvr", "inox", "gaming", "game", "games", "steam", "playstation", "xbox", "concert", "club",
            "party", "outing", "bowling", "arcade"
        ],
        "Education": [
            "book", "books", "textbook", "textbooks", "notebook", "notebooks", "stationery", "pen", "pens",
            "udemy", "coursera", "course", "courses", "tuition", "coaching", "college", "university",
            "exam", "exam fee", "fee", "fees", "xerox", "printout", "photocopy", "semester", "library", "assignment"
        ],
        "Health & Medical": [
            "pharmacy", "medicine", "medicines", "doctor", "hospital", "clinic", "health", "medical",
            "chemist", "tablet", "tablets", "syrup", "apollo", "1mg", "netmeds", "dentist", "therapy",
            "bandage", "consultation"
        ],
        "Subscriptions": [
            "subscription", "subscriptions", "membership", "icloud", "google one", "chatgpt", "github", "linkedin",
            "duolingo", "patreon", "medium", "software"
        ],
        "Utilities": [
            "electricity", "water bill", "water", "internet", "wifi", "broadband", "recharge", "mobile recharge", "mobile",
            "jio", "airtel", "vi", "bsnl", "cylinder", "gas", "electricity bill", "utility", "bill"
        ],
        "Rent & Housing": [
            "rent", "hostel", "pg", "room rent", "room", "landlord", "flat", "maintenance", "accommodation"
        ],
        "Personal Care": [
            "salon", "haircut", "barber", "spa", "shampoo", "cosmetic", "beauty", "grooming",
            "skincare", "parlour", "soap", "facewash"
        ],
        "Sports & Fitness": [
            "gym", "fitness", "badminton", "cricket", "football", "sports", "swimming", "workout", "protein",
            "creatine", "supplement", "turf"
        ],
        "Travel": [
            "flight", "flights", "hotel", "hotels", "trip", "vacation", "tour", "travel", "oyo", "makemytrip",
            "goibibo", "irctc", "resort", "homestay", "airbnb"
        ],
        "Gifts & Donations": [
            "gift", "gifts", "donation", "charity", "birthday", "anniversary", "present", "treat"
        ]
    }

    # Match using word boundaries to prevent substring collisions (e.g. 'steam' matching 'tea', 'theater' matching 'eat')
    for category, keywords in rules.items():
        for kw in keywords:
            if " " in kw:
                if kw in desc:
                    return category
            else:
                if re.search(rf"\b{re.escape(kw)}\b", desc):
                    return category

    return "Other"


def extract_receipt_data(extracted_text: str) -> dict:
    """Extract information from OCR receipt or order screenshot text."""
    client, model = get_client()
    if client:
        try:
            prompt = f"""You are an expert receipt, invoice, and order details parser for India.
Extract the following information from this receipt/order OCR text and return valid JSON only:
- merchant: name of the store, platform, restaurant, or brand (e.g. Domino's Pizza, Zomato, Swiggy, Blinkit, Zepto, Amazon, Cadbury, McDonald's). If not explicitly written, infer it from the dish/item names (e.g. 'Capsicum & Red Paprika with Videshi Hot Sauce, Veg Parcel' are signature Domino's Pizza items). If delivery order, use 'Food Delivery' if brand is uncertain. Never return null or navigation labels like 'Order Details', 'Help', 'Delivery Details', or 'Order Delivered'.
- amount: total purchase price / payable amount as a float number (NO currency symbols).
  CRITICAL RULES FOR AMOUNT:
  * In Indian digital receipts and food delivery apps, Tesseract OCR frequently misreads the Rupee symbol (₹) as '%', '~', '*', 'z', or as a leading digit '7' before a 3-4 digit amount (for example, reading '₹659.03' as '%659.03', '~659.03', or '7659.03'). If you see '%659.03' or '7659.03' next to 'Reorder' or 'Total' for a few food items, the price is 659.03, NOT 7659.03.
  * Standalone price numbers (with or without 'Total') next to action buttons like 'Reorder' or 'Pay' represent the total order amount.
  * NEVER use Order IDs (like OD33875..., Order #118), Barcodes, SKU codes, Phone numbers, Dates, PIN codes, or Tracking IDs as the amount!
  * If individual item prices are shown (e.g. ₹54, ₹47) and a combined grand total is omitted, calculate the sum of the item prices (e.g. 54 + 47 = 101.0).
  * In student budgeting, typical transaction amounts range between ₹5 and ₹50,000.
- date: purchase or order date in YYYY-MM-DD format (convert e.g. '17 Oct 2026' -> '2026-10-17', '28th Sep 2026' -> '2026-09-28'). If not found, use '{date.today()}'.
- description: brief summary of purchased items (e.g. 'Capsicum & Red Paprika Pizza, Paneer Makhani Pizza, Veg Parcel' or 'Cadbury Oreo, Dairy Milk Crackle').

Receipt/Order Text:
{extracted_text}

Respond with ONLY a valid JSON object like:
{{"merchant": "...", "amount": 0.0, "date": "YYYY-MM-DD", "description": "..."}}"""

            extra_params = {}
            if "groq.com" in str(getattr(client, 'base_url', '')):
                extra_params["extra_body"] = {"reasoning_format": "hidden"}

            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.0,
                **extra_params
            )
            text = (resp.choices[0].message.content or "").strip()
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                text = match.group(1).strip()
            else:
                json_match = re.search(r'(\{[\s\S]*\})', text)
                if json_match:
                    text = json_match.group(1).strip()

            parsed = json.loads(text) if text else {}
            amount_val = float(parsed.get('amount', 0) or 0)
            merchant_val = (parsed.get('merchant') or '').strip()

            # Sanity guards: if the LLM accidentally returned 0, an ID (> 200,000), or null merchant
            if amount_val <= 0 or amount_val > 200000 or not merchant_val:
                print(f"LLM output need heuristic refinement (amount={amount_val}, merchant={merchant_val}).")
                heur = _heuristic_receipt_parser(extracted_text)
                if amount_val <= 0 or amount_val > 200000:
                    parsed['amount'] = heur['amount']
                if not merchant_val:
                    parsed['merchant'] = heur['merchant']
                if not parsed.get('description'):
                    parsed['description'] = heur['description']
                if not parsed.get('date'):
                    parsed['date'] = heur['date']

            return parsed
        except Exception as e:
            print(f"Receipt AI parse error, using heuristic parser: {e}")

    # Heuristic fallback parser for receipt text
    return _heuristic_receipt_parser(extracted_text)


_MONTH_LOOKUP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}


def _heuristic_receipt_parser(text: str) -> dict:
    """Extract receipt details using robust regex, brand recognition, and contextual filtering."""
    raw_lines = [line.strip() for line in (text or '').split('\n') if line.strip()]

    # Patterns for navigation, statuses, ratings, order IDs, phone numbers, and ads
    nav_pattern = re.compile(
        r'^(?:<|>|\b)?\s*(?:order details|help|rate your experience|did you find|delivery details|order delivered|other|placed on|delivery|delivered|reorder|how was your food\??|overall order rating|rating|good|feedback|track order|invoice)\b',
        re.IGNORECASE
    )
    order_id_pattern = re.compile(
        r'\b(?:order\s*#?\s*\d+|order\s*id|od\s*[:#]?\s*[a-z0-9_]{4,}|id\s*[:#]\s*[a-z0-9_]{4,}|sku\b|tracking\b|barcode\b)',
        re.IGNORECASE
    )
    phone_pattern = re.compile(r'\b[6-9]\d{9}\b')
    ad_pattern = re.compile(r'\b(?:lifetime free|credit card|kotak|apply now|ad\b)', re.IGNORECASE)
    rating_pattern = re.compile(r'^[w\s*~x]+$', re.IGNORECASE)

    # 1. Date Extraction (handles "28th Sep 2026", "17 Oct 2026 19:24", "2026-09-28", "28/09/2026")
    date_str = ""
    date_word_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]{3,9})\s+(\d{4})', text)
    if date_word_match:
        day = date_word_match.group(1).zfill(2)
        mon_str = date_word_match.group(2)[:3].lower()
        mon = _MONTH_LOOKUP.get(mon_str, "01")
        year = date_word_match.group(3)
        date_str = f"{year}-{mon}-{day}"
    else:
        num_date = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})|(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
        if num_date:
            date_str = num_date.group(0)

    # 2. Amount Extraction
    amount = 0.0

    # Primary: Grand total / Amount due / Total paid / Net amount
    total_match = re.search(
        r'(?:grand\s*total|final\s*total|total\s*amount|total|net\s*amount|amount\s*paid|paid|bill\s*amount)\s*[:=]?\s*(?:₹|rs\.?|inr|[%~*])?\s*(\d+(?:\.\d{1,2})?)',
        text,
        re.IGNORECASE
    )
    if total_match:
        val = float(total_match.group(1))
        # Exclude IDs, years, or numbers over 200,000
        if 0 < val < 200000 and val != float(date_str[:4] if len(date_str) >= 4 else 0):
            amount = val

    # Secondary: Specific currency matches (₹, Rs, INR, %, ~)
    if amount == 0.0:
        currency_matches = []
        for line in raw_lines:
            if order_id_pattern.search(line) or phone_pattern.search(line) or ad_pattern.search(line):
                continue
            # Look for lines with ₹, Rs, INR, or common OCR misreads (w54, R47, %659.03, ~659.03) followed by digits
            matches = re.findall(r'(?:₹|rs\.?|inr|[wR%~*])\s*(\d+(?:\.\d{1,2})?)', line, re.IGNORECASE)
            for m in matches:
                val = float(m)
                if 1 <= val < 50000:
                    currency_matches.append(val)

        if currency_matches:
            # If multiple individual items exist (like w54 and R47 summing to 101), sum if reasonable, else max
            if len(currency_matches) > 1 and all(v < 500 for v in currency_matches):
                amount = sum(currency_matches)
            else:
                amount = max(currency_matches)

    # Tertiary: Standalone decimals like 659.03 or 7659.03 near action buttons or delivery context
    if amount == 0.0:
        for line in raw_lines:
            if order_id_pattern.search(line) or phone_pattern.search(line) or (date_word_match and date_word_match.group(0) in line):
                continue
            dec_match = re.search(r'\b(\d+)\.(\d{2})\b', line)
            if dec_match:
                candidate = float(f"{dec_match.group(1)}.{dec_match.group(2)}")
                # Check for leading '7' OCR artifact on Indian rupee (e.g. 7659.03 -> 659.03)
                if dec_match.group(1).startswith('7') and len(dec_match.group(1)) >= 4:
                    stripped = float(f"{dec_match.group(1)[1:]}.{dec_match.group(2)}")
                    if 10 <= stripped < 25000:
                        candidate = stripped
                if 1 <= candidate < 50000:
                    amount = candidate
                    break

    # 3. Merchant and Description Extraction
    candidate_items = []
    lower_text = text.lower()
    for line in raw_lines:
        if (nav_pattern.search(line) or order_id_pattern.search(line) or 
            phone_pattern.search(line) or ad_pattern.search(line) or
            rating_pattern.match(line) or
            (date_word_match and date_word_match.group(0) in line) or
            re.search(r'^\d{1,2}\s+[a-zA-Z]{3}\s+\d{4}', line) or
            re.search(r'^\d{1,2}:\d{2}', line) or
            re.search(r'^(?:₹|rs\.?|inr|[wR%~*])?\s*\d+(?:\.\d{1,2})?$', line.strip(), re.IGNORECASE) or
            len(line) < 3 or re.match(r'^[^\w\s]+$', line)):
            continue

        clean_line = re.sub(r'(?:₹|rs\.?|inr|[wR%~*])\s*\d+(?:\.\d{1,2})?', '', line, flags=re.IGNORECASE).strip()
        clean_line = re.sub(r'\s*\d+\s*x\s*[\d.]+\s*(?:g|ml|kg|l)?', '', clean_line, flags=re.IGNORECASE).strip()
        # Remove trailing quantity numbers (e.g. 'Sauce 5' -> 'Sauce', 'Items 1' -> 'Items')
        clean_line = re.sub(r'\s+\d+$', '', clean_line).strip()
        # Remove leading bullets / icons (@, (@}, [x], etc.)
        clean_line = re.sub(r'^\s*[\(\[\{]?\s*[@a-zA-Z0-9\-\*\#]\s*[\)\]\}]?\s*', '', clean_line).strip()
        clean_line = re.sub(r'^[|\-_.]+|\s*[|\-_.]+$', '', clean_line).strip()

        if len(clean_line) >= 4 and not re.search(r'\b(?:hostel|street|address|kumar|road|nagar|rating|food)\b', clean_line, re.IGNORECASE):
            if not any(clean_line.lower() in existing.lower() or existing.lower() in clean_line.lower() for existing in candidate_items):
                candidate_items.append(clean_line)

    # Infer merchant
    combined_items = " ".join(candidate_items).lower()
    if any(k in combined_items for k in ["parcel", "videshi", "desi makhani", "capsicum & red paprika", "domino"]):
        merchant = "Domino's Pizza"
    elif any(k in lower_text for k in ["cadbury"]):
        merchant = "Cadbury"
    elif any(k in lower_text for k in ["blinkit", "grofers"]):
        merchant = "Blinkit"
    elif any(k in lower_text for k in ["zepto"]):
        merchant = "Zepto"
    elif any(k in lower_text for k in ["instamart"]):
        merchant = "Swiggy Instamart"
    elif any(k in lower_text for k in ["swiggy"]):
        merchant = "Swiggy"
    elif any(k in lower_text for k in ["zomato"]):
        merchant = "Zomato"
    elif any(k in lower_text for k in ["amazon"]):
        merchant = "Amazon"
    elif any(k in lower_text for k in ["flipkart"]):
        merchant = "Flipkart"
    elif candidate_items:
        merchant = "Food Delivery" if any(k in lower_text for k in ["delivery", "order", "food"]) else candidate_items[0][:30]
    else:
        merchant = "Food Delivery" if "delivery" in lower_text else "Store Purchase"

    description = ", ".join(candidate_items[:3]) if candidate_items else f"{merchant} purchase"

    return {
        "merchant": merchant[:30],
        "amount": round(amount, 2),
        "date": date_str or str(date.today()),
        "description": description[:80] or f"{merchant} purchase"
    }


def get_financial_coach_response(question: str, financial_context: dict) -> str:
    """Get AI Financial Coach response with full financial context."""
    client, model = get_client()
    if client:
        try:
            context_str = f"""
User's Financial Summary:
- Monthly Income: ₹{financial_context.get('monthly_income', 0):,.0f}
- Total Expenses This Month: ₹{financial_context.get('total_expenses', 0):,.0f}
- Remaining Budget: ₹{financial_context.get('remaining_budget', 0):,.0f}
- Budget Amount: ₹{financial_context.get('budget_amount', 0):,.0f}
- Savings Target: ₹{financial_context.get('savings_target', 0):,.0f}
- Predicted Monthly Spending: ₹{financial_context.get('predicted_spending', 0):,.0f}
- Budget Usage: {financial_context.get('budget_usage_pct', 0):.1f}%
- Days Remaining in Month: {financial_context.get('days_remaining', 0)}
- Average Daily Spending: ₹{financial_context.get('avg_daily_spending', 0):,.0f}

Category-wise Spending:
{_format_category_spending(financial_context.get('category_spending', {}))}

Active Savings Goals:
{_format_goals(financial_context.get('goals', []))}

Budget Risks: {', '.join(financial_context.get('risks', [])) or 'None detected'}
"""
            system_prompt = """You are Budget Buddy's AI Financial Coach — a friendly, concise, and helpful assistant for college students in India.
Provide practical, personalized budgeting guidance based on the user's actual financial data.
Use ₹ for currency. Keep responses concise, clear, and actionable.
Disclaimer: Educational budgeting assistance only, not professional financial advice."""

            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Financial Context:\n{context_str}\n\nUser Question: {question}"}
                ],
                max_tokens=450,
                temperature=0.7
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI Coach error, using local financial reasoning: {e}")

    # High-quality local rule-based AI reasoning
    return _local_financial_coach_answer(question, financial_context)


def _local_financial_coach_answer(question: str, ctx: dict) -> str:
    """Generate intelligent data-driven budgeting advice locally without an external API key."""
    q = question.lower()
    income = ctx.get('monthly_income', 0)
    expenses = ctx.get('total_expenses', 0)
    budget = ctx.get('budget_amount', 0)
    remaining = ctx.get('remaining_budget', 0)
    predicted = ctx.get('predicted_spending', 0)
    avg_daily = ctx.get('avg_daily_spending', 0)
    days_left = ctx.get('days_remaining', 0)
    cat_spending = ctx.get('category_spending', {})

    # Sort categories by spent amount
    sorted_cats = sorted(cat_spending.items(), key=lambda x: x[1], reverse=True)
    top_cat = sorted_cats[0] if sorted_cats else ("None", 0)

    if any(k in q for k in ["where", "most", "highest", "top category", "spending the most"]):
        if sorted_cats:
            pct = (top_cat[1] / expenses * 100) if expenses > 0 else 0
            savings_est = top_cat[1] * 0.15
            return (
                f"Your highest spending category is **{top_cat[0]}** at **₹{top_cat[1]:,.0f}** "
                f"({pct:.0f}% of your monthly expenses).\n\n"
                f"**Top spending areas this month:**\n"
                f"{chr(10).join([f'• **{c}**: ₹{a:,.0f}' for c, a in sorted_cats[:3]])}\n\n"
                f"**Optimization Tip:** Reducing spending in {top_cat[0]} by just 15% would save you approx ₹{savings_est:,.0f} this month."
            )
        return "You don't have any recorded expenses yet this month. Once you add transactions, I will analyze your top spending categories."

    elif any(k in q for k in ["save", "saving", "goal", "target"]):
        target = ctx.get('savings_target', 0)
        potential = max(income - expenses, 0)
        daily_cap = max((remaining - 2000) / max(days_left, 1), 0)
        return (
            f"**Savings Analysis for this Month:**\n\n"
            f"• **Monthly Income:** ₹{income:,.0f}\n"
            f"• **Current Expenses:** ₹{expenses:,.0f}\n"
            f"• **Current Surplus:** ₹{potential:,.0f}\n"
            f"• **Savings Target:** ₹{target:,.0f}\n\n"
            f"To boost your savings by ₹2,000 this month, keep your remaining daily spending under **₹{daily_cap:,.0f}/day** for the next {days_left} days."
        )

    elif any(k in q for k in ["overspend", "over budget", "track", "budget summary", "status", "summary"]):
        usage_pct = ctx.get('budget_usage_pct', 0)
        status_msg = "You have exceeded your monthly budget." if remaining < 0 else "You are within your defined budget limit."
        daily_limit = max(remaining / max(days_left, 1), 0)
        return (
            f"**Monthly Budget Health Check:**\n\n"
            f"• **Budget Limit:** ₹{budget:,.0f}\n"
            f"• **Spent So Far:** ₹{expenses:,.0f} ({usage_pct:.0f}% used)\n"
            f"• **Remaining Budget:** ₹{remaining:,.0f}\n"
            f"• **Predicted Month-End Total:** ₹{predicted:,.0f}\n"
            f"• **Days Remaining:** {days_left} days (Avg ₹{avg_daily:,.0f}/day)\n\n"
            f"**Status:** {status_msg}\n"
            f"Recommended daily spend limit for the rest of the month: **₹{daily_limit:,.0f}/day**."
        )

    elif any(k in q for k in ["afford", "buy", "purchase", "can i"]):
        # Check purchase affordability
        nums = re.findall(r'\d+', q.replace(',', ''))
        amount = float(nums[0]) if nums else 2000
        can_afford = (remaining >= amount)
        afford_msg = "**Yes, you can afford this within your budget.**" if can_afford else "**This purchase would exceed your monthly budget limit.**"
        return (
            f"**Purchase Evaluation:**\n\n"
            f"• **Remaining budget:** ₹{remaining:,.0f}\n"
            f"• **Purchase Amount:** ₹{amount:,.0f}\n\n"
            f"{afford_msg}\n"
            f"After this purchase, your remaining budget for the next {days_left} days will be **₹{max(remaining - amount, 0):,.0f}**.\n\n"
            f"Tip: You can test this scenario in the What-If Simulator to evaluate its full month-end projection."
        )

    elif any(k in q for k in ["cut", "reduce", "decrease", "less"]):
        if sorted_cats:
            second_tip = f"2. **{sorted_cats[1][0]}** (₹{sorted_cats[1][1]:,.0f}): Optimize recurring subscriptions or transit.\n" if len(sorted_cats) > 1 else ""
            return (
                f"**Suggested Expense Reductions:**\n\n"
                f"1. **{sorted_cats[0][0]}** (₹{sorted_cats[0][1]:,.0f}): Cut non-essential orders or look for student discounts.\n"
                + second_tip
                + "\nSetting category limits in the Budget Planner helps keep discretionary spending in check."
            )

    bal = income - expenses
    return (
        f"**Financial Coach Insight:**\n\n"
        f"You have spent **₹{expenses:,.0f}** out of your **₹{income:,.0f}** income this month, "
        f"leaving **₹{bal:,.0f}** in balance with {days_left} days left.\n\n"
        f"• **Top Category:** {top_cat[0]} (₹{top_cat[1]:,.0f})\n"
        f"• **Average Daily Spending:** ₹{avg_daily:,.0f}/day\n"
        f"• **Predicted Month-End Spend:** ₹{predicted:,.0f}\n\n"
        f"Feel free to ask questions like *'Where am I spending the most?'*, "
        f"*'How can I save ₹2,000?'*, or *'Can I afford a ₹3,000 purchase?'*."
    )


def _format_category_spending(category_spending: dict) -> str:
    if not category_spending:
        return "  No category data available"
    lines = []
    for cat, amount in sorted(category_spending.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  - {cat}: ₹{amount:,.0f}")
    return "\n".join(lines)


def _format_goals(goals: list) -> str:
    if not goals:
        return "  No active savings goals"
    lines = []
    for g in goals:
        pct = (g.get('saved_amount', 0) / g.get('target_amount', 1) * 100) if g.get('target_amount') else 0
        lines.append(f"  - {g['name']}: ₹{g.get('saved_amount', 0):,.0f} / ₹{g.get('target_amount', 0):,.0f} ({pct:.0f}%)")
    return "\n".join(lines)
