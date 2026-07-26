"""
FalconIQ AML Platform — Sample Dataset Generator
Generates ~2100 realistic customer records compatible with the dashboard schema.
Outputs CSV to Desktop for easy access.
"""
import csv
import random
import os
from datetime import datetime, timedelta, timezone

random.seed(42)

OUTPUT_CSV = os.path.expanduser("~/Desktop/FalconIQ_AML_Sample_Dataset_2100_Customers.csv")

# ── Enum Values (matching backend/app/constants/risk.py) ──
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
KYC_STATUSES = ["PENDING", "VERIFIED", "FAILED", "EXPIRED"]
SEGMENTS = ["RETAIL", "PRIVATE", "CORPORATE", "SME", "WEALTH"]

COUNTRIES = ["USA", "GBR", "DEU", "FRA", "CAN", "AUS", "IND", "SGP", "ARE", "JPN", "CHE", "NLD", "BRA", "KOR", "HKG", "MYS", "ZAF", "NGA"]
HIGH_RISK_COUNTRIES = ["AFG", "IRN", "PRK", "SYR", "RUS", "MMR", "VEN", "YEM", "LBY", "SDN"]

# ── Realistic Indian & International Names ──
FIRST_NAMES_INDIAN = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Bhavya", "Chirag", "Deepa", "Dhruv", "Esha",
    "Gaurav", "Hari", "Isha", "Jayesh", "Kavya", "Lakshmi", "Manish", "Neha", "Om", "Priya",
    "Rahul", "Sakshi", "Tanvi", "Uday", "Varun", "Vivek", "Yash", "Zara", "Ravi", "Sanjay",
    "Pooja", "Meena", "Kiran", "Suresh", "Nandini", "Rohan", "Shreya", "Akash", "Divya", "Harsh",
    "Anjali", "Rajesh", "Simran", "Vikram", "Swati", "Arun", "Pallavi", "Nitin", "Megha", "Kunal",
]
LAST_NAMES_INDIAN = [
    "Sharma", "Patel", "Gupta", "Singh", "Kumar", "Agarwal", "Joshi", "Verma", "Reddy", "Nair",
    "Malhotra", "Chopra", "Mehta", "Iyer", "Rao", "Pillai", "Desai", "Bhat", "Saxena", "Mishra",
    "Kapoor", "Banerjee", "Chatterjee", "Das", "Mukherjee", "Shah", "Sinha", "Pandey", "Tiwari", "Jain",
]
FIRST_NAMES_INTL = [
    "James", "Olivia", "William", "Emma", "Alexander", "Sofia", "Benjamin", "Isabella", "Lucas", "Mia",
    "Henry", "Charlotte", "Daniel", "Amelia", "Michael", "Harper", "David", "Evelyn", "Joseph", "Abigail",
    "Chen", "Wei", "Yuki", "Sakura", "Ahmed", "Fatima", "Omar", "Layla", "Hans", "Greta",
    "Pierre", "Marie", "Carlos", "Ana", "Sven", "Ingrid", "Kazuki", "Yuna", "Ibrahim", "Aisha",
]
LAST_NAMES_INTL = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Davis", "Miller", "Wilson", "Moore", "Taylor",
    "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson",
    "Wang", "Li", "Zhang", "Liu", "Chen", "Tanaka", "Sato", "Kim", "Park", "Nguyen",
    "Mueller", "Schmidt", "Schneider", "Fischer", "Weber", "Dupont", "Bernard", "Petit", "Robert", "Moreau",
]

OCCUPATIONS = [
    "Software Engineer", "Bank Manager", "Doctor", "Lawyer", "Business Owner", "Trader", "Accountant",
    "Government Employee", "Teacher", "Real Estate Agent", "Import/Export Dealer", "Jeweller",
    "Retired", "Consultant", "Pharmacist", "Agriculture", "Factory Owner", "Freelancer",
    "CEO", "CFO", "Director", "VP Finance", "Fund Manager", "Hedge Fund Analyst",
    "Stock Broker", "Insurance Agent", "Chartered Accountant", "Architect", "Civil Servant",
    "Politician", "Mining Executive", "Shipping Magnate", "Textile Manufacturer", "Diplomat",
    "NGO Director", "Crypto Trader", "Restaurant Owner", "Hotelier", "Contractor",
]

COMPANY_SUFFIXES = ["Pvt Ltd", "LLC", "Corp", "Industries", "Enterprises", "Group", "Holdings", "Trading Co", "Impex", "Exports"]
COMPANY_WORDS = [
    "Arise", "Apex", "Global", "Balaji", "Venkatha", "Surya", "Reliance", "Bright", "Pioneer", "Summit",
    "Horizon", "Stellar", "Nexus", "Prime", "Royal", "Eagle", "Phoenix", "Titan", "Crescent", "Diamond",
    "Pacific", "Atlantic", "Nordic", "Alpine", "Emerald", "Sapphire", "Golden", "Silver", "Crystal", "Metro",
]

NOW = datetime.now(timezone.utc)


def random_date(start_days_ago=730, end_days_ago=1):
    delta = timedelta(days=random.randint(end_days_ago, start_days_ago))
    return (NOW - delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def gen_email(name, idx):
    clean = name.lower().replace(" ", ".").replace("'", "")
    domains = ["gmail.com", "outlook.com", "yahoo.com", "company.co.in", "business.com", "mail.com", "protonmail.com"]
    return f"{clean}.{idx}@{random.choice(domains)}"


def gen_company_name():
    return f"{random.choice(COMPANY_WORDS)} {random.choice(COMPANY_WORDS)} {random.choice(COMPANY_SUFFIXES)}"


def generate_customers(num=2100):
    customers = []
    
    # ── Tier 1: Normal / Low Risk Customers (1400 — ~67%) ──
    for i in range(1, 1401):
        is_indian = random.random() < 0.55
        if is_indian:
            name = f"{random.choice(FIRST_NAMES_INDIAN)} {random.choice(LAST_NAMES_INDIAN)}"
            country = "IND" if random.random() < 0.7 else random.choice(COUNTRIES)
        else:
            name = f"{random.choice(FIRST_NAMES_INTL)} {random.choice(LAST_NAMES_INTL)}"
            country = random.choice(COUNTRIES)
        
        segment = random.choices(SEGMENTS, weights=[50, 10, 15, 20, 5])[0]
        if segment == "CORPORATE":
            name = gen_company_name()
        
        income = random.uniform(300000, 5000000) if country == "IND" else random.uniform(30000, 250000)
        
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "name": name,
            "email": gen_email(name, i),
            "occupation": random.choice(OCCUPATIONS),
            "annual_income": round(income, 2),
            "risk_category": "LOW",
            "kyc_status": random.choices(["VERIFIED", "PENDING"], weights=[90, 10])[0],
            "customer_segment": segment,
            "country": country,
            "created_at": random_date(730, 30),
            "updated_at": random_date(30, 1),
        })
    
    # ── Tier 2: Medium Risk Customers (400 — ~19%) ──
    for i in range(1401, 1801):
        is_indian = random.random() < 0.45
        if is_indian:
            name = f"{random.choice(FIRST_NAMES_INDIAN)} {random.choice(LAST_NAMES_INDIAN)}"
            country = "IND" if random.random() < 0.5 else random.choice(COUNTRIES)
        else:
            name = f"{random.choice(FIRST_NAMES_INTL)} {random.choice(LAST_NAMES_INTL)}"
            country = random.choice(COUNTRIES)
        
        segment = random.choices(SEGMENTS, weights=[25, 20, 25, 15, 15])[0]
        if segment == "CORPORATE":
            name = gen_company_name()
        
        income = random.uniform(800000, 15000000) if country == "IND" else random.uniform(80000, 500000)
        
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "name": name,
            "email": gen_email(name, i),
            "occupation": random.choice(OCCUPATIONS),
            "annual_income": round(income, 2),
            "risk_category": "MEDIUM",
            "kyc_status": random.choices(["VERIFIED", "PENDING", "EXPIRED"], weights=[60, 25, 15])[0],
            "customer_segment": segment,
            "country": country,
            "created_at": random_date(730, 30),
            "updated_at": random_date(30, 1),
        })
    
    # ── Tier 3: High Risk Customers (200 — ~9.5%) ──
    for i in range(1801, 2001):
        is_indian = random.random() < 0.35
        if is_indian:
            name = f"{random.choice(FIRST_NAMES_INDIAN)} {random.choice(LAST_NAMES_INDIAN)}"
        else:
            name = f"{random.choice(FIRST_NAMES_INTL)} {random.choice(LAST_NAMES_INTL)}"
        
        country = random.choices(
            COUNTRIES + HIGH_RISK_COUNTRIES,
            weights=[3]*len(COUNTRIES) + [8]*len(HIGH_RISK_COUNTRIES)
        )[0]
        
        segment = random.choices(SEGMENTS, weights=[10, 25, 30, 10, 25])[0]
        if segment == "CORPORATE":
            name = gen_company_name()
        
        income = random.uniform(2000000, 50000000) if country == "IND" else random.uniform(200000, 2000000)
        
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "name": name,
            "email": gen_email(name, i),
            "occupation": random.choice(OCCUPATIONS),
            "annual_income": round(income, 2),
            "risk_category": "HIGH",
            "kyc_status": random.choices(["VERIFIED", "PENDING", "FAILED", "EXPIRED"], weights=[30, 30, 25, 15])[0],
            "customer_segment": segment,
            "country": country,
            "created_at": random_date(730, 30),
            "updated_at": random_date(30, 1),
        })
    
    # ── Tier 4: Critical Risk Customers (100 — ~4.8%) ──
    for i in range(2001, 2101):
        is_indian = random.random() < 0.3
        if is_indian:
            name = f"{random.choice(FIRST_NAMES_INDIAN)} {random.choice(LAST_NAMES_INDIAN)}"
        else:
            name = f"{random.choice(FIRST_NAMES_INTL)} {random.choice(LAST_NAMES_INTL)}"
        
        country = random.choices(
            HIGH_RISK_COUNTRIES + ["IND", "ARE", "HKG", "SGP"],
            weights=[10]*len(HIGH_RISK_COUNTRIES) + [5, 4, 3, 3]
        )[0]
        
        segment = random.choices(SEGMENTS, weights=[5, 30, 35, 5, 25])[0]
        if segment == "CORPORATE":
            name = gen_company_name()
        
        income = random.uniform(10000000, 200000000) if country in ["IND", "ARE"] else random.uniform(500000, 10000000)
        
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "name": name,
            "email": gen_email(name, i),
            "occupation": random.choice(OCCUPATIONS),
            "annual_income": round(income, 2),
            "risk_category": "CRITICAL",
            "kyc_status": random.choices(["PENDING", "FAILED", "EXPIRED", "VERIFIED"], weights=[35, 30, 20, 15])[0],
            "customer_segment": segment,
            "country": country,
            "created_at": random_date(730, 30),
            "updated_at": random_date(30, 1),
        })
    
    return customers


def write_csv(customers):
    fieldnames = [
        "customer_id", "name", "email", "occupation", "annual_income",
        "risk_category", "kyc_status", "customer_segment", "country",
        "created_at", "updated_at"
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)
    print(f"\n✅ Successfully generated {len(customers)} customer records!")
    print(f"📄 CSV saved to: {OUTPUT_CSV}")
    print(f"📊 Risk Distribution:")
    from collections import Counter
    risk_counts = Counter(c["risk_category"] for c in customers)
    for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        print(f"   {level:10s}: {risk_counts.get(level, 0):>5d} customers")
    kyc_counts = Counter(c["kyc_status"] for c in customers)
    print(f"\n🔐 KYC Status:")
    for status in ["VERIFIED", "PENDING", "FAILED", "EXPIRED"]:
        print(f"   {status:10s}: {kyc_counts.get(status, 0):>5d} customers")
    country_counts = Counter(c["country"] for c in customers)
    print(f"\n🌍 Top 10 Countries:")
    for country, count in country_counts.most_common(10):
        print(f"   {country:5s}: {count:>5d} customers")
    segment_counts = Counter(c["customer_segment"] for c in customers)
    print(f"\n🏦 Customer Segments:")
    for seg in ["RETAIL", "PRIVATE", "CORPORATE", "SME", "WEALTH"]:
        print(f"   {seg:12s}: {segment_counts.get(seg, 0):>5d} customers")


if __name__ == "__main__":
    print("🏗️  FalconIQ AML Platform — Sample Dataset Generator")
    print("=" * 55)
    customers = generate_customers(2100)
    random.shuffle(customers)
    write_csv(customers)
