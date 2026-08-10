import datetime
import asyncio
import re

# Sourced from official portals:
# PMJDY: https://www.pmjdy.gov.in/
# APY: https://www.npscra.nsdl.co.in/
# PMJJBY / PMSBY: https://www.jansuraksha.gov.in/
# PMMY (PM MUDRA): https://www.mudra.org.in/
# Stand-Up India: https://www.standupmitra.in/
# JanSamarth: https://www.jansamarth.in/

SCHEMES_DB = {
    "pmjdy": {
        "scheme_name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "aliases": [
            "PMJDY",
            "Jan Dhan",
            "Jan Dhan Yojana",
            "Pradhan Mantri Jan Dhan"
        ],
        "source": "https://www.pmjdy.gov.in/",
        "source_updated_at": "2026-05-20T00:00:00Z",
        "overview": "National Mission for Financial Inclusion to ensure access to financial services, namely, basic savings & deposit accounts, remittance, credit, insurance, pension in an affordable manner.",
        "eligibility": "Any Indian citizen of age 10 years or more who does not have an existing bank account can open a PMJDY account with zero balance. Final eligibility is determined by the relevant bank/authority.",
        "benefits": "Provides a zero-balance basic savings account, a free RuPay debit card, built-in accidental insurance cover of Rs. 2 Lakhs (for accounts opened after 28.08.2018), life cover of Rs. 30,000, and an overdraft facility of up to Rs. 10,000 to eligible account holders.",
        "application": "You can open a PMJDY account at any bank branch or authorized Business Correspondent (Bank Mitra) outlet. Download the account opening form from the official website or obtain it directly at the bank.",
        "documents": "Requires official valid documents (OVD) for KYC, which include Aadhaar card, PAN card, Voter ID, Driving License, or Passport.",
        "latest_status": "Active and operational across all public and private sector banks in India."
    },
    "apy": {
        "scheme_name": "Atal Pension Yojana (APY)",
        "aliases": [
            "APY",
            "Atal Pension",
            "Atal Pension Yojana"
        ],
        "source": "https://www.npscra.nsdl.co.in/scheme-atal-pension-yojana.php",
        "source_updated_at": "2026-06-15T00:00:00Z",
        "overview": "A guaranteed monthly pension scheme targeting workers in the unorganized sector, administered by the Pension Fund Regulatory and Development Authority (PFRDA) through banks.",
        "eligibility": "Open to all Indian citizens aged between 18 and 40 years who have a bank account and are not taxpayers or beneficiaries of any social security scheme. Final eligibility is determined by the relevant bank/authority.",
        "benefits": "Guarantees a minimum monthly pension of Rs. 1,000, Rs. 2,000, Rs. 3,000, Rs. 4,000, or Rs. 5,000 after reaching age 60, depending on the subscriber's contribution. On the subscriber's demise, the spouse gets the same pension, and on the death of both, the accumulated corpus is returned to the nominee.",
        "application": "Contact the bank branch or post office where your savings bank account is maintained. Fill out the APY registration form and enable the auto-debit consent.",
        "documents": "APY registration form, Aadhaar card, and active bank account details.",
        "latest_status": "Active. Over 5 crore citizens enrolled since launch."
    },
    "pmjjby": {
        "scheme_name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "aliases": [
            "PMJJBY",
            "Jeevan Jyoti",
            "Jeevan Jyoti Bima",
            "Pradhan Mantri Jeevan Jyoti Bima Yojana"
        ],
        "source": "https://www.jansuraksha.gov.in/",
        "source_updated_at": "2026-04-10T00:00:00Z",
        "overview": "A one-year life insurance scheme renewable from year to year, offering life insurance cover for death due to any cause.",
        "eligibility": "Available to all individual bank or post office account holders aged between 18 and 50 years. Final eligibility is determined by the relevant bank/authority.",
        "benefits": "Offers a life insurance cover of Rs. 2 Lakhs in case of death due to any reason, for an annual premium of Rs. 436 auto-debited from the subscriber's account.",
        "application": "Submit the PMJJBY enrolment form and auto-debit consent to the bank or post office where your savings account is held.",
        "documents": "Aadhaar card, PMJJBY enrolment form, and savings bank account number.",
        "latest_status": "Active. Premium is Rs. 436 per annum."
    },
    "pmsby": {
        "scheme_name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "aliases": [
            "PMSBY",
            "Suraksha Bima",
            "Suraksha Bima Yojana",
            "Pradhan Mantri Suraksha Bima Yojana"
        ],
        "source": "https://www.jansuraksha.gov.in/",
        "source_updated_at": "2026-04-10T00:00:00Z",
        "overview": "A one-year personal accident insurance scheme renewable from year to year, offering coverage for accidental death and disability.",
        "eligibility": "Available to all individual bank or post office account holders aged between 18 and 70 years. Final eligibility is determined by the relevant bank/authority.",
        "benefits": "Offers an accidental death or total disability cover of Rs. 2 Lakhs, and a partial disability cover of Rs. 1 Lakh, for a premium of Rs. 20 per annum auto-debited from the subscriber's account.",
        "application": "Submit the PMSBY enrolment form and auto-debit consent to the bank or post office where your savings account is maintained.",
        "documents": "Aadhaar card, PMSBY enrolment form, and savings bank account details.",
        "latest_status": "Active. Premium is Rs. 20 per annum."
    },
    "pmmy": {
        "scheme_name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "aliases": [
            "PMMY",
            "PM Mudra",
            "MUDRA",
            "Mudra Yojana",
            "Mudra loan",
            "Mudra scheme",
            "Pradhan Mantri Mudra",
            "Pradhan Mantri Mudra Yojana"
        ],
        "source": "https://www.mudra.org.in/",
        "source_updated_at": "2026-02-05T00:00:00Z",
        "overview": "Pradhan Mantri MUDRA Yojana (PMMY) is a scheme launched for providing loans up to 10 Lakh to the non-corporate, non-farm small/micro enterprises.",
        "eligibility": "Any Indian citizen who has a business plan for a non-farm sector income generating activity such as manufacturing, processing, trading or service sector and whose credit need is up to 10 Lakh can apply. Final eligibility is determined by the relevant bank or lending institution.",
        "benefits": "Provides collateral-free loans up to 10 Lakh under three categories: Shishu (loans up to 50,000), Kishor (loans from 50,000 to 5 Lakh), and Tarun (loans from 5 Lakh to 10 Lakh). Interest rates are determined by RBI guidelines.",
        "application": "Loans can be applied for at commercial banks, regional rural banks (RRBs), small finance banks, microfinance institutions (MFIs), and NBFCs, or online through the Udyamitra portal.",
        "documents": "MUDRA application form, business plan, identity proof (Aadhaar, Voter ID, PAN), residence proof, business address proof, and passport-size photographs.",
        "latest_status": "Active. Credit limits and disbursement targets are updated annually by the government."
    },
    "standup_india": {
        "scheme_name": "Stand-Up India",
        "aliases": [
            "Stand-Up India",
            "Standup India",
            "Stand Up India"
        ],
        "source": "https://www.standupmitra.in/",
        "source_updated_at": "2026-03-12T00:00:00Z",
        "overview": "Stand-Up India Scheme facilitates bank loans between 10 Lakh and 1 Crore to at least one Scheduled Caste (SC) or Scheduled Tribe (ST) borrower and at least one woman borrower per bank branch for setting up a greenfield enterprise.",
        "eligibility": "SC/ST and/or women entrepreneurs, above 18 years of age. Enterprise must be a greenfield project (first-time venture). In case of non-individual enterprises, at least 51% of shareholding must be held by SC/ST/Woman borrower. Final eligibility is determined by the lending bank.",
        "benefits": "Provides composite loans between 10 Lakh and 1 Crore covering up to 75% of project cost, with a repayment period of 7 years and a maximum moratorium period of 18 months.",
        "application": "Apply online via the Stand-Up India Portal or at any bank branch.",
        "documents": "Identity proof, residence proof, business address proof, SC/ST certificate if applicable, project report, and partnership deed/incorporation details.",
        "latest_status": "Active. Extended by the government to support entrepreneurship."
    },
    "jansamarth": {
        "scheme_name": "JanSamarth",
        "aliases": [
            "JanSamarth",
            "Jan Samarth",
            "JanSamarth Portal"
        ],
        "source": "https://www.jansamarth.in/",
        "source_updated_at": "2026-04-18T00:00:00Z",
        "overview": "JanSamarth is a unique digital portal linking government credit-linked schemes to connect lenders and beneficiaries, providing simplified loan approvals.",
        "eligibility": "Varies by underlying scheme. Open to students, farmers, MSME entrepreneurs, and self-help groups seeking credit-linked government subsidies. Final eligibility is determined by participating lenders.",
        "benefits": "Single digital platform to check eligibility for 13+ credit-linked government schemes, apply online, and obtain digital in-principle approval from multiple banks.",
        "application": "Apply directly online at the official website jansamarth.in.",
        "documents": "Aadhaar card, PAN card, business registration, income details, and bank statements.",
        "latest_status": "Active. Facilitates multiple loans under Education, Agri Infrastructure, Livelihood, and Business Activity categories."
    }
}

def find_scheme(scheme_query: str) -> str | None:
    """Finds matching database key based on query matching keys or aliases."""
    query = re.sub(r'[^\w\s]', '', scheme_query.lower()).strip()
    if not query:
        return None

    # Try exact match on keys or exact match on aliases first
    for key, data in SCHEMES_DB.items():
        if query == key:
            return key
        for alias in data.get("aliases", []):
            alias_clean = re.sub(r'[^\w\s]', '', alias.lower()).strip()
            if query == alias_clean:
                return key

    # Try word-based matching (all alias words present in user query)
    query_words = set(query.split())
    for key, data in SCHEMES_DB.items():
        for alias in data.get("aliases", []):
            alias_clean = re.sub(r'[^\w\s]', '', alias.lower()).strip()
            alias_words = alias_clean.split()
            if alias_words and all(word in query_words for word in alias_words):
                return key

    # Fallback to simple substring match
    for key, data in SCHEMES_DB.items():
        for alias in data.get("aliases", []):
            alias_clean = re.sub(r'[^\w\s]', '', alias.lower()).strip()
            if alias_clean in query or query in alias_clean:
                return key

    return None

def normalize_info_type(info_query: str) -> str:
    """Normalizes natural language variations to standard database keys."""
    iq = info_query.lower().strip()
    
    # eligibility mappings
    if any(keyword in iq for keyword in ["who can apply", "am i eligible", "qualification", "eligible", "eligibility"]):
        return "eligibility"
    
    # benefits mappings
    if any(keyword in iq for keyword in ["advantages", "what do i get", "benefit", "benefits", "premium", "premium amount", "category", "categories", "loan category", "loan categories"]):
        return "benefits"
        
    # application mappings
    if any(keyword in iq for keyword in ["how do i apply", "where can i apply", "apply", "application", "enroll", "enrollment"]):
        return "application"
        
    # documents mappings
    if any(keyword in iq for keyword in ["documents needed", "what papers do i need", "document", "documents", "paper", "papers"]):
        return "documents"
        
    # latest_status mappings
    if any(keyword in iq for keyword in ["latest", "current status", "is it still active", "status", "latest_status", "active"]):
        return "latest_status"
        
    return "overview"

async def lookup_scheme_db(scheme_name: str, information_requested: str) -> dict:
    """Helper to query local scheme data, supporting timeout simulation."""
    name_clean = scheme_name.lower().strip()
    
    # Check for timeout simulation keyword
    if "timeout" in name_clean:
        await asyncio.sleep(12.0) # Sleep longer than the 8s threshold
        raise asyncio.TimeoutError("Connection timed out")

    # Match database key
    matched_key = find_scheme(scheme_name)

    if not matched_key or matched_key not in SCHEMES_DB:
        return {
            "success": False,
            "error_type": "NOT_FOUND",
            "message": "This scheme is not currently available in FinBuddy's curated government-scheme dataset."
        }

    scheme = SCHEMES_DB[matched_key]
    info_clean = normalize_info_type(information_requested)
    
    # Check if field exists in scheme
    if info_clean not in scheme or scheme[info_clean] is None or scheme[info_clean] == "":
        return {
            "success": False,
            "error_type": "FIELD_NOT_AVAILABLE",
            "message": "The requested information is not available for this scheme in the current dataset."
        }

    return {
        "success": True,
        "scheme_name": scheme["scheme_name"],
        "source": scheme["source"],
        "source_updated_at": scheme["source_updated_at"],
        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "info_type": info_clean,
        "content": scheme[info_clean]
    }
