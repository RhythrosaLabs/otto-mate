#!/usr/bin/env python3
"""Test Otto Universal systems - Smart Printify detection and Universal Editor."""

import asyncio
import sys

def test_printify():
    """Test smart Printify product detection."""
    print("\n1️⃣ SMART PRINTIFY PRODUCT DETECTION")
    print("-" * 50)
    
    from src.tools.printify import resolve_product_type
    
    tests = [
        # Basic matching
        ("mug", "Mug", "direct"),
        ("t-shirt", "Tee", "direct"),
        
        # Synonyms
        ("coffee cup", "Mug", "synonym"),
        ("sweater", "Sweatshirt", "synonym"),
        ("wall art", "Canvas", "synonym"),
        
        # Baby/kid products (compound terms)
        ("baby clothes", "Baby Onesie", "compound"),
        ("toddler clothes", "Kids T-Shirt", "compound"),
        ("infant outfit", "Baby Onesie", "compound"),
        
        # Natural language extraction
        ("put this on a mug", "Mug", "NLP pattern"),
        ("I want this on a hoodie", "Hoodie", "NLP pattern"),
        ("can you make me a coffee cup?", "Mug", "NLP pattern"),
        ("create a poster with this design", "Poster", "NLP pattern"),
        
        # Plurals
        ("mugs", "Mug", "plural→singular"),
        ("hoodies", "Hoodie", "plural→singular"),
        ("pillows", "Pillow", "plural→singular"),
        
        # Typos/misspellings
        ("hoody", "Hoodie", "typo correction"),
        ("tshirt", "Tee", "typo correction"),
        ("cofee mug", "Mug", "typo correction"),
        ("swetshirt", "Sweatshirt", "typo correction"),
        
        # Context awareness
        ("something for my dog", "Pet", "context detection"),
        ("for the baby", "Baby", "context detection"),
        ("for drinking coffee", "Mug", "context detection"),
        
        # Complex natural language
        ("I need something to wear to the gym", "Tee", "context"),
        ("make me something for my phone", "Case", "context"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected, test_type in tests:
        result = resolve_product_type(query)
        name = result["name"]
        matched = result.get("matched_from", "")
        
        # Check if expected substring is in the result name
        success = expected.lower() in name.lower()
        
        if success:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"
        
        print(f"  {status} [{test_type}] \"{query}\"")
        print(f"      → {name} ({matched[:40]}...)" if len(matched) > 40 else f"      → {name} ({matched})")
    
    print(f"\n  Results: {passed}/{len(tests)} passed")
    return failed == 0


async def test_editor():
    """Test universal media editor."""
    print("\n2️⃣ UNIVERSAL MEDIA EDITOR")
    print("-" * 50)
    
    from src.tools.universal_editor import UniversalEditor
    
    editor = UniversalEditor()
    result = await editor.list_capabilities()
    print(f"  ✅ Editor loaded successfully")
    return True


def main():
    print("=" * 60)
    print("TESTING OTTO UNIVERSAL SMART SYSTEMS")
    print("=" * 60)
    
    # Test Printify
    printify_ok = test_printify()
    
    # Test Editor
    editor_ok = asyncio.run(test_editor())
    
    print("\n" + "=" * 60)
    if printify_ok and editor_ok:
        print("ALL SYSTEMS OPERATIONAL ✅")
    else:
        print("SOME TESTS NEED REVIEW ⚠️")
    print("=" * 60)
    
    return 0 if (printify_ok and editor_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
