#!/usr/bin/env python3
"""Test all new modules ported from printify_clean."""

import sys
sys.path.insert(0, '.')

def test_modules():
    print("Testing new modules...")
    print()

    # 1. BrandBrain
    print("1. Testing BrandBrain...")
    try:
        from src.tools.brand_brain import BrandBrain, get_brand_brain
        brain = get_brand_brain()
        profile = brain.load_profile()
        print(f"   Brand: {profile['brand_name']}")
        print(f"   Data dir: {brain.brand_dir}")
        print("   ✓ BrandBrain OK")
    except Exception as e:
        print(f"   ✗ BrandBrain FAILED: {e}")
    print()

    # 2. MultiPlatformPoster
    print("2. Testing MultiPlatformPoster...")
    try:
        from src.tools.social_poster import (
            MultiPlatformPoster, get_multi_platform_poster,
            get_available_platforms, PLATFORM_CONFIG
        )
        poster = get_multi_platform_poster()
        platforms = get_available_platforms()
        print(f"   Platforms: {len(platforms)}")
        print(f"   Available: {list(platforms.keys())}")
        print("   ✓ MultiPlatformPoster OK")
    except Exception as e:
        print(f"   ✗ MultiPlatformPoster FAILED: {e}")
    print()

    # 3. EmailMarketingService
    print("3. Testing EmailMarketingService...")
    try:
        from src.tools.email_marketing import EmailMarketingService, get_email_service
        service = get_email_service()
        print(f"   Configured: {service.is_configured()}")
        print(f"   Provider: {service.provider}")
        print(f"   Templates: {list(EmailMarketingService.TEMPLATE_TYPES.keys())}")
        print("   ✓ EmailMarketingService OK")
    except Exception as e:
        print(f"   ✗ EmailMarketingService FAILED: {e}")
    print()

    # 4. EnhancedTaskQueueEngine
    print("4. Testing EnhancedTaskQueueEngine...")
    try:
        from src.tools.task_queue_engine import (
            EnhancedTaskQueueEngine, get_task_queue_engine,
            Task, TaskStep, TaskStatus, TaskPriority, 
            Artifact, ArtifactType
        )
        queue = get_task_queue_engine()
        stats = queue.get_statistics()
        print(f"   Tasks: {stats['total_tasks']}")
        print(f"   Status types: {[s.value for s in TaskStatus]}")
        print(f"   Priority levels: {[p.name for p in TaskPriority]}")
        print("   ✓ EnhancedTaskQueueEngine OK")
    except Exception as e:
        print(f"   ✗ EnhancedTaskQueueEngine FAILED: {e}")
    print()

    # 5. Test combined exports
    print("5. Testing combined exports from __init__.py...")
    try:
        from src.tools import (
            BrandBrain, get_brand_brain,
            MultiPlatformPoster, get_multi_platform_poster,
            EmailMarketingService, get_email_service,
            EnhancedTaskQueueEngine, get_task_queue_engine,
            Task, TaskStep, TaskStatus, TaskPriority, Artifact, ArtifactType
        )
        print("   ✓ All exports accessible")
    except Exception as e:
        print(f"   ✗ Combined exports FAILED: {e}")
    print()

    print("=" * 50)
    print("Module testing complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_modules()
