#!/usr/bin/env python3
"""
Quick test script to verify Printify credentials are loaded from .env
"""

from src.utils.config import get_settings
from src.tools.printify import PrintifyTools
import asyncio

async def test_printify():
    settings = get_settings()
    
    print("🔍 Checking Printify Configuration...")
    print(f"   API Token: {'✅ Set' if settings.printify_api_token else '❌ Missing'}")
    print(f"   Shop ID: {'✅ Set' if settings.printify_shop_id else '❌ Missing'}")
    
    if not settings.printify_api_token:
        print("\n❌ PRINTIFY_API_TOKEN not found in .env")
        print("   Add to .env: PRINTIFY_API_TOKEN=your_token_here")
        return
    
    if not settings.printify_shop_id:
        print("\n❌ PRINTIFY_SHOP_ID not found in .env")
        print("   Add to .env: PRINTIFY_SHOP_ID=your_shop_id")
        return
    
    # Test connection
    print("\n🔗 Testing Printify API connection...")
    printify = PrintifyTools(
        api_token=settings.printify_api_token,
        shop_id=settings.printify_shop_id
    )
    
    try:
        # Try to list products
        result = await printify.list_products()
        print(f"✅ Connected! Found {len(result.get('data', []))} products")
        print(f"   Shop ID: {settings.printify_shop_id}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Verify API token is correct")
        print("   2. Check shop ID matches your Printify account")
        print("   3. Ensure API token has proper permissions")
        return False

if __name__ == "__main__":
    asyncio.run(test_printify())
