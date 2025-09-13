import requests
from cachetools import cached, TTLCache
from typing import List
from ..models import BusRouteProperties

# 巴士路線 WFS API URL
WFS_API_URL = "https://portal.csdi.gov.hk/server/services/common/td_rcd_1638844988873_41214/MapServer/WFSServer?service=wfs&request=GetFeature&typeName=FB_ROUTE_LINE&outputFormat=application/json"
cache = TTLCache(maxsize=1, ttl=86400)  # Cache for 1 day
@cached(cache)
def get_all_bus_routes() -> List[BusRouteProperties]:
    """get all bus routes from WFS API and cache the result for 1 day"""
    print("正在從獲取最新的巴士路線數據...")
    try:
        response = requests.get(WFS_API_URL,timeout=20)     #send GET request and timeout after 20 seconds
        response.raise_for_status()          # Raise an error for bad responses
        data = response.json()
        features = data.get('features', [])       
        validated_routes = [BusRouteProperties(**feature['properties']) for feature in features] # analysis and validate the data
        print(f"成功獲取並驗證了 {len(validated_routes)} 條路線數據。")
        return validated_routes
    except requests.exceptions.RequestException as e:
        print(f"錯誤：無法獲取數據。 {e}")
        return []   #return empty list on error
    
def translate_text_for_ai(routes: List[BusRouteProperties], lang: str = 'tc') -> str:
    text_lines = []
    for route in routes:
        line = ""
        """lang: 'tc' (繁體中文), 'sc' (簡體中文), 'en' (英文)"""
        if lang == 'tc':
            start_name = route.ST_STOP_NAME_C
            end_name = route.ED_STOP_NAME_C
            line = f"路線 {route.ROUTE_NAME_E}: 由「{start_name}」開往「{end_name}」。(公司: {route.COMPANY_CODE})"
        elif lang == 'sc':
            start_name = route.ST_STOP_NAME_S
            end_name = route.ED_STOP_NAME_S
            line = f"路线 {route.ROUTE_NAME_E}: 由“{start_name}”开往“{end_name}”。(公司: {route.COMPANY_CODE})"
        elif lang == 'en':
            start_name = route.ST_STOP_NAME_E
            end_name = route.ED_STOP_NAME_E
            line = f"Route {route.ROUTE_NAME_E}: from '{start_name}' to '{end_name}'. (Company: {route.COMPANY_CODE})"
        

        #makesure both start_name and end_name are not None or empty
        if start_name and end_name:
            text_lines.append(line)
    return "\n".join(text_lines)        