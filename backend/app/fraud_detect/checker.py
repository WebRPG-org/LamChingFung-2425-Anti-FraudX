import re
from ..core.mongo_client import mongo_client
from thefuzz import fuzz

async def check_entity(name: str) -> dict:
    db = mongo_client.get_db()
    collection = db.sfc_alert_list
    
    query_name = name.strip()
    
    if len(query_name) < 3: # Query too short, return directly
        return {
            "risk_level": "GRAY",
            "message": f"The input '{query_name}' is too short. For accurate results, please provide a more complete company name or website."
        }

    #  Loose search, use Regex to find all possible candidates
    safe_query_regex = re.escape(query_name)
    cursor = collection.find(
        {"company_name": {"$regex": safe_query_regex, "$options": "i"}}
    ).limit(20)
    candidates = await cursor.to_list(length=20)

    if not candidates:
        return {"risk_level": "GRAY", "message": f"'{query_name}' not found in SFC alert list."}

    # Exact match priority, Check for exact matches (case insensitive)
    for candidate in candidates:
        if query_name.lower() == candidate["company_name"].lower():
            return {
                "risk_level": "RED",
                "message": f"High risk: '{query_name}' exactly matches a record in the SFC alert list.",
                "details": [{
                    "matched_name": candidate["company_name"],
                    "add_date": candidate["add_date"],
                    "type": candidate["type"],
                    "score": 100
                }]
            }

    # Weighted fuzzy scoring, If no exact match, perform fuzzy scoring on all candidates
    scored_matches = []
    for candidate in candidates:
        score = fuzz.WRatio(query_name, candidate["company_name"])
        scored_matches.append({
            "matched_name": candidate["company_name"],
            "add_date": candidate["add_date"],
            "type": candidate["type"],
            "score": score
        })

    scored_matches.sort(key=lambda x: x["score"], reverse=True)
    top_match = scored_matches[0]
    top_score = top_match["score"]
    
    # 4 level threshold judgment
    if top_score >= 95:
        return {
            "risk_level": "RED",
            "message": f"High risk: '{query_name}' found highly matching items in the SFC alert list.",
            "details": scored_matches[:3]
        }
    elif top_score >= 80:
        return {
            "risk_level": "ORANGE",
            "message": f"Medium risk: '{query_name}' found similar records in the SFC alert list, please verify carefully.",
            "details": scored_matches[:3]
        }
    elif top_score >= 40:
        return {
            "risk_level": "YELLOW",
            "message": f"Low risk: Found partially similar records. The queried '{query_name}' may be incomplete, suggest providing complete name for more accurate results.",
            "details": scored_matches[:3]
        }
    else:
        return {
            "risk_level": "GRAY",
            "message": f"'{query_name}' not found sufficiently relevant matches in the SFC alert list."
        }