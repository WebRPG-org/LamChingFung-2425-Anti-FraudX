import requests
import time
from requests.exceptions import RequestException
from cachetools import cached, TTLCache
from typing import List
from ..models import KmbBusRoute

# 巴士路線 WFS API URL
KMB_ROUTE_LIST_API_URL = "https://data.etabus.gov.hk/v1/transport/kmb/route/"
cache = TTLCache(maxsize=1, ttl=86400)  # Cache for 1 day
@cached(cache)
def get_all_bus_routes() -> List[KmbBusRoute]:
    """get all bus routes from WFS API and cache the result for 1 day"""
    print("正在從獲取最新的巴士路線數據...")

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
        'Referer': 'https://portal.csdi.gov.hk/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    for attempt in range(MAX_RETRIES):
        print(f"嘗試第 {attempt + 1} / {MAX_RETRIES} 次請求...")
        try:
            response = requests.get(KMB_ROUTE_LIST_API_URL, headers=headers, timeout=30)
            response.raise_for_status()             # Raise an error for bad responses
            data = response.json().get('data', [])
            if not data:
                print("警告：從 API 獲取的 data 列表為空。")
                return []      
            validated_routes = validated_routes = [KmbBusRoute(**route_data) for route_data in data] # analysis and validate the data
            print(f"成功獲取並驗證了 {len(validated_routes)} 條路線數據。")
            return validated_routes
        except RequestException as e:
            print(f"第 {attempt + 1} 次請求失敗: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"將在 {RETRY_DELAY_SECONDS} 秒後重試...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print("已達到最大重試次數，獲取數據失敗。")
            
                return []   #return empty list on error

    return []

    
    
def translate_text_for_ai(routes: List[KmbBusRoute], lang: str = 'tc') -> str:
    text_lines = []
    for route in routes:
        line = ""
        """lang: 'tc' (繁體中文), 'sc' (簡體中文), 'en' (英文)"""
        if lang == 'tc':
            start_name = route.orig_tc
            end_name = route.dest_tc
            direction = "去程" if route.bound.upper() == 'O' else "回程"
            line = f"路線 {route.route} ({direction}): 由「{start_name}」開往「{end_name}」。"
        elif lang == 'sc':
            start_name = route.orig_sc
            end_name = route.dest_sc
            direction = "去程" if route.bound.upper() == 'O' else "回程"
            line = f"路线 {route.route} ({direction}): 由“{start_name}”开往“{end_name}”。"
        elif lang == 'en':
            start_name = route.orig_en
            end_name = route.dest_en
            direction = "Outbound" if route.bound.upper() == 'O' else "Inbound"
            line = f"Route {route.route} ({direction}): from '{start_name}' to '{end_name}'."
        

        #makesure both start_name and end_name are not None or empty
        if start_name and end_name:
            text_lines.append(line)
    return "\n".join(text_lines)        