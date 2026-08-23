import os
import json
import re

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
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    return bool(key and not key.startswith('your_openai') and not key.startswith('sk-fake') and len(key) > 20)


def get_client():
    if not is_openai_configured():
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    except Exception as e:
        print(f"OpenAI init notice: {e}")
        return None


def categorize_expense(description: str, amount: float) -> str:
    """Categorize expense using OpenAI if configured, otherwise rule-based categorizer."""
    client = get_client()
    if client:
        try:
            prompt = f"""You are an expense categorization system for college students in India.
Categorize the following expense into exactly one of these categories:
{', '.join(EXPENSE_CATEGORIES)}

Expense Description: {description}
Amount: ₹{amount}

Respond with ONLY the category name, nothing else."""

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.1
            )
            category = resp.choices[0].message.content.strip()
            if category in EXPENSE_CATEGORIES:
                return category
            for cat in EXPENSE_CATEGORIES:
                if cat.lower() in category.lower() or category.lower() in cat.lower():
                    return cat
        except Exception as e:
            print(f"OpenAI categorize error, using rule-based: {e}")

    return _rule_based_categorize(description)


def _rule_based_categorize(description: str) -> str:
    """Smart keyword and pattern based categorizer tailored for college students in India."""
    desc = (description or '').lower().strip()
    rules = {
        "Food & Dining": [
            "zomato", "swiggy", "domino", "pizza", "burger", "mcdonald", "kfc", "subway",
            "cafe", "coffee", "starbucks", "chai", "tea", "canteen", "mess", "lunch",
            "dinner", "breakfast", "biryani", "dhaba", "restaurant", "food", "snack", "eat", "shawarma"
        ],
        "Transportation": [
            "uber", "ola", "rapido", "auto", "rickshaw", "bus", "metro", "train", "cab", "taxi",
            "petrol", "fuel", "diesel", "bike", "scooter", "fare", "toll", "parking"
        ],
        "Groceries": [
            "grocery", "kirana", "dmart", "bigbasket", "blinkit", "zepto", "instamart",
            "vegetables", "fruits", "milk", "bread", "eggs", "supermarket", "ration"
        ],
        "Shopping": [
            "amazon", "flipkart", "myntra", "ajio", "meesho", "zara", "h&m", "clothes",
            "shirt", "t-shirt", "jeans", "shoes", "sneakers", "shopping", "mall", "electronics", "keyboard"
        ],
        "Entertainment": [
            "netflix", "prime", "hotstar", "youtube", "spotify", "apple music", "movie",
            "cinema", "pvr", "inox", "gaming", "game", "steam", "playstation", "concert", "club"
        ],
        "Education": [
            "book", "textbook", "notebook", "stationery", "pen", "udemy", "coursera",
            "course", "tuition", "coaching", "college", "university", "exam", "fee", "xerox", "printout"
        ],
        "Health & Medical": [
            "pharmacy", "medicine", "doctor", "hospital", "clinic", "health", "medical",
            "chemist", "tablet", "syrup", "apollo", "1mg", "netmeds"
        ],
        "Subscriptions": [
            "subscription", "membership", "icloud", "google one", "chatgpt", "github", "linkedin"
        ],
        "Utilities": [
            "electricity", "water", "internet", "wifi", "broadband", "recharge", "mobile",
            "jio", "airtel", "vi", "cylinder", "gas", "bill"
        ],
        "Rent & Housing": [
            "rent", "hostel", "pg", "room", "landlord", "flat", "maintenance"
        ],
        "Personal Care": [
            "salon", "haircut", "barber", "spa", "shampoo", "cosmetic", "beauty", "grooming", "gym", "fitness"
        ],
        "Travel": [
            "flight", "hotel", "trip", "vacation", "tour", "travel", "oyo", "makemytrip", "goibibo", "irctc"
        ],
    }
    for category, keywords in rules.items():
        for kw in keywords:
            if kw in desc:
                return category
    return "Other"


def extract_receipt_data(extracted_text: str) -> dict:
    """Extract information from OCR receipt text."""
    client = get_client()
    if client:
        try:
            prompt = f"""Extract the following information from this receipt OCR text and return valid JSON only:
- merchant: name of the store/merchant
- amount: total amount as a number (no currency symbol)
- date: date in YYYY-MM-DD format (use today if not found)
- description: brief description of the purchase

Receipt Text:
{extracted_text}

Respond with ONLY a valid JSON object like:
{{"merchant": "...", "amount": 0.0, "date": "YYYY-MM-DD", "description": "..."}}"""

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1
            )
            text = resp.choices[0].message.content.strip()
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                text = match.group(1).strip()
            return json.loads(text)
        except Exception as e:
            print(f"Receipt AI parse error, using heuristic parser: {e}")

    # Heuristic fallback parser for receipt text
    return _heuristic_receipt_parser(extracted_text)


def _heuristic_receipt_parser(text: str) -> dict:
    """Extract receipt details using regex patterns."""
    lines = [l.strip() for l in (text or '').split('\n') if l.strip()]
    merchant = lines[0] if lines else "Store Purchase"
    
    # Try finding amount
    amount = 0.0
    amount_matches = re.findall(r'(?:total|amt|amount|net|inr|rs\.?|₹)?\s*[:=]?\s*(\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
    if amount_matches:
        amounts = [float(a) for a in amount_matches if float(a) > 0]
        if amounts:
            amount = max(amounts)

    # Try finding date
    date_str = ""
    date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})|(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
    if date_match:
        date_str = date_match.group(0)

    return {
        "merchant": merchant[:30],
        "amount": amount,
        "date": date_str,
        "description": f"{merchant[:30]} receipt purchase"
    }


def get_financial_coach_response(question: str, financial_context: dict) -> str:
    """Get AI Financial Coach response with full financial context."""
    client = get_client()
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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Financial Context:\n{context_str}\n\nUser Question: {question}"}
                ],
                max_tokens=450,
                temperature=0.7
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Coach error, using local financial reasoning: {e}")

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
    goals = ctx.get('goals', [])

    # Sort categories by spent amount
    sorted_cats = sorted(cat_spending.items(), key=lambda x: x[1], reverse=True)
    top_cat = sorted_cats[0] if sorted_cats else ("None", 0)

    if any(k in q for k in ["where", "most", "highest", "top category", "spending the most"]):
        if sorted_cats:
            cat_list = ", ".join([f"**{c}** (₹{amt:,.0f})" for c, amt in sorted_cats[:3]])
            pct = (top_cat[1] / expenses * 100) if expenses > 0 else 0
            return (
                f"📊 Your highest spending category is **{top_cat[0]}** at **₹{top_cat[1]:,.0f}** "
                f"({pct:.0f}% of your monthly expenses).\n\n"
                f"Your top 3 spending areas this month:\n"
                f"{chr(10).join([f'• **{c}**: ₹{a:,.0f}' for c, a in sorted_cats[:3]])}\n\n"
                f"💡 **Tip:** Reducing spending in {top_cat[0]} by just 15% would save you approx ₹{top_cat[1]*0.15:,.0f} this month."
            )
        return "You don't have any recorded expenses yet this month. Once you add transactions, I will analyze your top spending categories!"

    elif any(k in q for k in ["save", "saving", "goal", "target"]):
        target = ctx.get('savings_target', 0)
        potential = max(income - expenses, 0)
        return (
            f"🎯 **Savings Analysis for this Month:**\n\n"
            f"• **Monthly Income:** ₹{income:,.0f}\n"
            f"• **Current Expenses:** ₹{expenses:,.0f}\n"
            f"• **Current Surplus:** ₹{potential:,.0f}\n"
            f"• **Savings Target:** ₹{target:,.0f}\n\n"
            f"To boost your savings by ₹2,000 this month, keep your remaining daily spending under **₹{max((remaining - 2000)/max(days_left, 1), 0):,.0f}/day** for the next {days_left} days."
        )

    elif any(k in q for k in ["overspend", "over budget", "track", "budget summary", "status", "summary"]):
        usage_pct = ctx.get('budget_usage_pct', 0)
        status_msg = "🚨 You have exceeded your budget." if remaining < 0 else "✅ You are within your budget limit."
        return (
            f"📋 **Monthly Budget Health Check:**\n\n"
            f"• **Budget Limit:** ₹{budget:,.0f}\n"
            f"• **Spent So Far:** ₹{expenses:,.0f} ({usage_pct:.0f}% used)\n"
            f"• **Remaining Budget:** ₹{remaining:,.0f}\n"
            f"• **Predicted Month-End Total:** ₹{predicted:,.0f}\n"
            f"• **Days Remaining:** {days_left} days (Avg ₹{avg_daily:,.0f}/day)\n\n"
            f"{status_msg}\n"
            f"💡 Recommended daily spend limit for the rest of the month: **₹{max(remaining/max(days_left, 1), 0):,.0f}/day**."
        )

    elif any(k in q for k in ["afford", "buy", "purchase", "can i"]):
        # Check purchase affordability
        nums = re.findall(r'\d+', q.replace(',', ''))
        amount = float(nums[0]) if nums else 2000
        can_afford = (remaining >= amount)
        return (
            f"🛍️ **Purchase Evaluation:**\n\n"
            f"• Remaining budget: **₹{remaining:,.0f}**\n"
            f"• Evaluation for: **₹{amount:,.0f}**\n\n"
            f"{'✅ **Yes, you can afford this within your budget!**' if can_afford else '⚠️ **This purchase would put you over your monthly budget.**'}\n"
            f"After this purchase, your remaining budget for the next {days_left} days will be **₹{max(remaining - amount, 0):,.0f}**.\n\n"
            f"💡 Tip: Test this scenario in the **What-If Simulator** to see its full impact on your month-end prediction!"
        )

    elif any(k in q for k in ["cut", "reduce", "decrease", "less"]):
        if sorted_cats:
            return (
                f"✂️ **Suggested Expense Reductions:**\n\n"
                f"1. **{sorted_cats[0][0]}** (₹{sorted_cats[0][1]:,.0f}): Cut non-essential orders or look for student discounts.\n"
                + (f"2. **{sorted_cats[1][0]}** (₹{sorted_cats[1][1]:,.0f}): Optimize travel/subscriptions.\n" if len(sorted_cats) > 1 else "")
                + f"\n💡 Setting per-category limits in the **Budget Planner** helps keep discretionary spending in check."
            )

    return (
        f"🤖 **Financial Coach Insight:**\n\n"
        f"You have spent **₹{expenses:,.0f}** out of your **₹{income:,.0f}** income this month, leaving **₹{income - expenses:,.0f}** in balance with {days_left} days left.\n\n"
        f"• Top Category: **{top_cat[0]}** (₹{top_cat[1]:,.0f})\n"
        f"• Average Daily Spending: **₹{avg_daily:,.0f}/day**\n"
        f"• Predicted Month-End Spend: **₹{predicted:,.0f}**\n\n"
        f"Feel free to ask specific questions like *'Where am I spending the most?'*, *'How can I save ₹2,000?'*, or *'Can I afford a ₹3,000 purchase?'*!"
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
