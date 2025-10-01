import httpx
import re
from pymongo import UpdateOne
from ..core.mongo_client import mongo_client

# HKMA - fake bank scams news reports
HKMA_FRAUDULENT_SCAMS_API = "https://api.hkma.gov.hk/public/bank-svf-info/fraudulent-bank-scams?lang=tc"
# HKMA - trusted bank hotlines
HKMA_HOTLINES_API = "https://api.hkma.gov.hk/public/bank-svf-info/hotlines-auth-retailbanks-rep?lang=tc"
# HKMA - trusted authorized institutions and their subsidiaries
HKMA_AI_RELATED_TRUSTEES_API = "https://api.hkma.gov.hk/public/bank-svf-info/ai-related-trustees"

# for all HKMA requests, add more complete headers to mimic a browser
HKMA_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}


async def sync_hkma_scam_reports():
    """Fetch the latest scam news releases from HKMA, extract suspicious URLs and entities."""
    db = mongo_client.get_db()
    collection = db.scam_indicators
    print("Syncing HKMA scam news releases (Traditional Chinese)...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(HKMA_FRAUDULENT_SCAMS_API, headers=HKMA_HEADERS)
            response.raise_for_status()
            data = response.json()
            
            updates = []
            
            for report in data.get("result", {}).get("records", []):
                fraud_url = report.get("fraud_website_address")
                alleged_name = report.get("alleged_name")

                if fraud_url:
                    updates.append(UpdateOne(
                        {"value": fraud_url.strip()},
                        {"$set": {
                            "type": "url", 
                            "source": "HKMA_scam_report", 
                            "alleged_name": alleged_name,
                            "report_date": report.get("issue_date")
                        }},
                        upsert=True
                    ))
                if alleged_name:
                     updates.append(UpdateOne(
                        {"value": alleged_name.strip()},
                        {"$set": {
                            "type": "entity_name", 
                            "source": "HKMA_scam_report",
                            "related_url": fraud_url,
                            "report_date": report.get("issue_date")
                        }},
                        upsert=True
                    ))
            
            if updates:
                result = await collection.bulk_write(updates)
                print(f"HKMA scam news release sync completed: {result.bulk_api_result}")
            else:
                print("No new updates in HKMA scam news releases.")

        except Exception as e:
            print(f"Error occurred while processing HKMA scam news releases: {e}")

async def sync_official_contacts():
    """Sync HKMA bank hotlines, authorized institutions and their subsidiaries to build a 'whitelist'."""
    db = mongo_client.get_db()
    hotline_collection = db.official_contacts
    entity_collection = db.licensed_entities
    print("Syncing official contact information and related companies (Traditional Chinese)...")

    async with httpx.AsyncClient() as client:
        # 1. Fetch Bank Hotlines
        try:
            res_hotlines = await client.get(HKMA_HOTLINES_API, headers=HKMA_HEADERS)
            res_hotlines.raise_for_status()
            print(f"Bank hotline API status code: {res_hotlines.status_code}")
            hotlines_data = res_hotlines.json()
            hotlines = hotlines_data.get("result", {}).get("records", [])
            
            updates_hotline = []
            for item in hotlines:
                for hotline in item.get("hotline", []):
                    updates_hotline.append(UpdateOne(
                        {"value": hotline.replace(" ", ""), "type": "hotline"},
                        {"$set": {"entity_name_tc": item.get("name_chi"), "entity_name_en": item.get("name_en")}},
                        upsert=True
                    ))
            if updates_hotline:
                await hotline_collection.bulk_write(updates_hotline)
                print(f"Bank hotline sync completed, total {len(updates_hotline)} records.")
            else:
                print("No new updates in bank hotlines.")

        except httpx.HTTPStatusError as e:
            print(f"Failed to request bank hotline API: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        except Exception as e:
            print(f"Error occurred while processing bank hotlines: {e}")
            
        # 2. Fetch Authorized Institutions (AI) and their Subsidiaries (AISub)
        for segment in ["AI", "AISub"]:
            try:
                print(f"Fetching HKMA authorized institution data: segment={segment} (Traditional Chinese)")
                params = {'lang': 'tc', 'segment': segment}
                res_entities = await client.get(HKMA_AI_RELATED_TRUSTEES_API, headers=HKMA_HEADERS, params=params)
                res_entities.raise_for_status()
                print(f"HKMA entity API (segment={segment}) status code: {res_entities.status_code}")
                entities_data = res_entities.json()
                entities = entities_data.get("result", {}).get("records", [])
                
                segment_updates = []
                for item in entities:
                    segment_updates.append(UpdateOne(
                        {"name_en": item.get("eng_name")},
                        {"$set": {
                            "name_tc": item.get("chi_name"),
                            "parent_institution": item.get("parent_ai"),
                            "type": "authorized_institution_related",
                            "source": "HKMA",
                            "segment": segment
                        }},
                        upsert=True
                    ))
                if segment_updates:
                    await entity_collection.bulk_write(segment_updates)
                    print(f"HKMA related companies (segment={segment}) sync completed, total {len(segment_updates)} records.")
                else:
                    print(f"No new updates in HKMA related companies (segment={segment}).")
            except httpx.HTTPStatusError as e:
                print(f"Failed to request HKMA entity API (segment={segment}): {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            except Exception as e:
                print(f"Error occurred while processing HKMA entity (segment={segment}): {e}")


