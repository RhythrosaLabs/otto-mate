"""Test aspect ratio detection in image generation."""
import asyncio
import os
import sys
sys.path.insert(0, '.')

async def test_aspect_ratio():
    from src.tools.image_generation import ImageGenerationTools
    
    token = os.environ.get('REPLICATE_API_TOKEN')
    if not token:
        print('ERROR: REPLICATE_API_TOKEN not set')
        return
    
    tools = ImageGenerationTools(token)
    
    # Test 1: Portrait via aspect_ratio parameter
    print('Test 1: Explicit aspect_ratio="portrait"')
    result = await tools.generate_image(
        prompt='A majestic dragon flying through clouds',
        aspect_ratio='portrait'
    )
    print(f'  Success: {result.get("success")}')
    print(f'  Aspect Ratio: {result.get("aspect_ratio")}')
    if result.get("images"):
        print(f'  Image URL: {result.get("images")[0][:80]}...')
    
    # Test 2: Auto-detect from prompt
    print('')
    print('Test 2: Auto-detect from prompt "portrait dimension"')
    result2 = await tools.generate_image(
        prompt='A portrait dimension illustration of a samurai warrior'
    )
    print(f'  Success: {result2.get("success")}')
    print(f'  Aspect Ratio: {result2.get("aspect_ratio")}')
    if result2.get("images"):
        print(f'  Image URL: {result2.get("images")[0][:80]}...')
    
    # Test 3: Tall keyword
    print('')
    print('Test 3: Auto-detect from prompt "tall image"')
    result3 = await tools.generate_image(
        prompt='A tall image of a lighthouse on a cliff'
    )
    print(f'  Success: {result3.get("success")}')
    print(f'  Aspect Ratio: {result3.get("aspect_ratio")}')
    if result3.get("images"):
        print(f'  Image URL: {result3.get("images")[0][:80]}...')

if __name__ == "__main__":
    asyncio.run(test_aspect_ratio())
