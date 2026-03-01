#!/usr/bin/env python3
"""Quick test script to verify all new modules import correctly."""

import sys
sys.path.insert(0, '.')

def test_imports():
    print("Testing module imports...")
    
    # Test task_models
    try:
        from src.core.task_models import (
            TaskStatus, TaskPriority, ArtifactType, 
            Artifact, TaskStep, Task
        )
        print("✅ task_models: OK")
        print(f"   TaskStatus values: {len(list(TaskStatus))}")
    except Exception as e:
        print(f"❌ task_models: {e}")
        return False
    
    # Test enhanced_agent_delegation
    try:
        from src.core.enhanced_agent_delegation import (
            SPECIALIZED_AGENTS, AgentSpecialization
        )
        print("✅ enhanced_agent_delegation: OK")
        print(f"   Specialized agents: {len(SPECIALIZED_AGENTS)}")
    except Exception as e:
        print(f"❌ enhanced_agent_delegation: {e}")
        return False
    
    # Test replicate_models
    try:
        from src.tools.replicate_models import (
            REPLICATE_MODEL_CATALOG, get_model
        )
        print("✅ replicate_models: OK")
        print(f"   Model shortcuts: {len(REPLICATE_MODEL_CATALOG)}")
    except Exception as e:
        print(f"❌ replicate_models: {e}")
        return False
    
    # Test shopify_base
    try:
        from src.tools.shopify_base import ShopifyBaseClient
        print("✅ shopify_base: OK")
    except Exception as e:
        print(f"❌ shopify_base: {e}")
        return False
    
    print("\n🎉 All modules working correctly!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
