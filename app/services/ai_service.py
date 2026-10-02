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
            prompt = f"""You are an expert receipt, invoice, and order details parser.
Extract the following information from this receipt/order OCR text and return valid JSON only:
- merchant: name of the store, platform, or brand (e.g. Cadbury, Blinkit, Zepto, Swiggy, Zomato, Amazon). Do NOT use navigation labels like 'Order Details', 'Help', or 'Delivery Details'.
- amount: total purchase price / payable amount as a float number (NO currency symbols).
  IMPORTANT RULES FOR AMOUNT:
  * NEVER use Order IDs (like OD33875...), Barcodes, SKU codes, Phone numbers, Dates, PIN codes, or Tracking IDs as the amount!
  * Look for price indicators (₹, Rs, INR, Price, Total, MRP, etc.).
  * If individual item prices are shown (e.g. ₹54, ₹47) and a combined grand total is omitted, calculate the sum of the item prices (e.g. 54 + 47 = 101.0).
  * In student budgeting, typical transaction amounts range between ₹5 and ₹50,000. Any number with 7+ integer digits is an ID, NOT a price.
- date: purchase or order date in YYYY-MM-DD format (convert e.g. '28th Sep 2026' -> '2026-09-28'). If not found, use '{date.today()}'.
- description: brief summary of purchased items (e.g. 'Cadbury Oreo, Dairy Milk Crackle').

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
                max_tokens=600,
                temperature=0.1,
                **extra_params
            )
            text = resp.choices[0].message.content.strip()
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                text = match.group(1).strip()
            
            parsed = json.loads(text)
            # Sanity guard: if the LLM accidentally returned an ID (> 200,000), drop to fallback
            if float(parsed.get('amount', 0)) > 200000:
                print(f"Suspiciously large amount from LLM ({parsed.get('amount')}), running heuristic guard.")
                return _heuristic_receipt_parser(extracted_text)
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
    """Extract receipt details using robust regex and contextual filtering."""
    raw_lines = [line.strip() for line in (text or '').split('\n') if line.strip()]

    # Patterns for navigation, order IDs, phone numbers, and ads
    nav_pattern = re.compile(
        r'^(?:<|>|\b)?\s*(?:order details|help|rate your experience|did you find|delivery details|order delivered|other|placed on)\b',
        re.IGNORECASE
    )
    order_id_pattern = re.compile(r'(?:order\s*#?|od|id|sku|tracking|barcode)\s*[:#]?[a-z0-9_]{6,}', re.IGNORECASE)
    phone_pattern = re.compile(r'\b[6-9]\d{9}\b')
    ad_pattern = re.compile(r'\b(?:lifetime free|credit card|kotak|apply now|ad\b)', re.IGNORECASE)

    # 1. Date Extraction (handles "28th Sep 2026", "29 Sep 2026", "2026-09-28", "28/09/2026")
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

    # Primary: Grand total / Amount due / Total paid
    total_match = re.search(
        r'(?:grand\s*total|final\s*total|total\s*amount|total|net\s*amount|amount\s*paid|paid|bill\s*amount)\s*[:=]?\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)',
        text,
        re.IGNORECASE
    )
    if total_match:
        val = float(total_match.group(1))
        # Exclude IDs, years, or numbers over 200,000
        if 0 < val < 200000 and val != float(date_str[:4] if len(date_str) >= 4 else 0):
            amount = val

    # Secondary: Scan individual item lines for prices with currency markers
    if amount == 0.0:
        item_prices = []
        for line in raw_lines:
            # Exclude lines that are clearly order numbers, phone numbers, ads, or addresses
            if order_id_pattern.search(line) or phone_pattern.search(line) or ad_pattern.search(line):
                continue
            
            # Find price patterns: ₹, Rs, INR, or common OCR misreads ('w54', 'R47') followed by digits
            matches = re.findall(r'(?:₹|rs\.?|inr|[wR])\s*(\d+(?:\.\d{1,2})?)', line, re.IGNORECASE)
            for m in matches:
                val = float(m)
                # Valid price range for items: ₹1 to ₹50,000 (discards weight numbers like 41759)
                if 1 <= val < 50000:
                    item_prices.append(val)

        if item_prices:
            # Sum up valid item prices
            amount = sum(item_prices)

    # 3. Merchant and Description Extraction
    candidate_items = []
    for line in raw_lines:
        if (nav_pattern.search(line) or order_id_pattern.search(line) or 
            phone_pattern.search(line) or ad_pattern.search(line) or
            len(line) < 3 or re.match(r'^[^\w\s]+$', line)):
            continue

        clean_line = re.sub(r'(?:₹|rs\.?|inr|[wR])\s*\d+(?:\.\d{1,2})?', '', line, flags=re.IGNORECASE).strip()
        clean_line = re.sub(r'\s*\d+\s*x\s*[\d.]+\s*(?:g|ml|kg|l)?', '', clean_line, flags=re.IGNORECASE).strip()
        clean_line = re.sub(r'^[|\-_.]+|\s*[|\-_.]+$', '', clean_line).strip()

        if len(clean_line) >= 4 and not re.search(r'\b(?:hostel|street|address|kumar|road|nagar)\b', clean_line, re.IGNORECASE):
            candidate_items.append(clean_line)

    if candidate_items:
        combined_text = " ".join(candidate_items)
        brand_match = re.search(r'\b(Cadbury|Amul|Nestle|Pepsi|Coke|Blinkit|Zepto|Instamart|Swiggy|Zomato|Amazon|Flipkart)\b', combined_text, re.IGNORECASE)
        if brand_match:
            merchant = brand_match.group(1).title()
        else:
            merchant = candidate_items[0][:30]
        description = ", ".join(candidate_items[:3])[:60]
    else:
        merchant = "Store Purchase"
        description = "Receipt purchase"

    return {
        "merchant": merchant[:30],
        "amount": round(amount, 2),
        "date": date_str or str(date.today()),
        "description": description or f"{merchant} purchase"
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
