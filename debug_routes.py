#!/usr/bin/env python3
"""
Debug script to check FastAPI routes registration
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.main import app
    
    print("FastAPI 路由調試")
    print("=" * 50)
    print(f"總路由數量: {len(app.routes)}")
    print()
    
    print("所有註冊的路由:")
    print("-" * 30)
    
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            print(f"{methods:15} {route.path}")
        elif hasattr(route, 'path'):
            print(f"{'N/A':15} {route.path}")
        else:
            print(f"{'Unknown':15} {str(route)}")
    
    print()
    print("檢查特定路由:")
    print("-" * 30)
    
    # Check for auth routes
    auth_routes = [r for r in app.routes if hasattr(r, 'path') and '/auth' in r.path]
    print(f"認證路由數量: {len(auth_routes)}")
    for route in auth_routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
        print(f"  {methods:15} {route.path}")
    
    # Check for media routes
    media_routes = [r for r in app.routes if hasattr(r, 'path') and '/media' in r.path]
    print(f"多媒體路由數量: {len(media_routes)}")
    for route in media_routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
        print(f"  {methods:15} {route.path}")
        
except ImportError as e:
    print(f"導入錯誤: {e}")
    print("請確保在正確的目錄中運行此腳本")
except Exception as e:
    print(f"錯誤: {e}")
