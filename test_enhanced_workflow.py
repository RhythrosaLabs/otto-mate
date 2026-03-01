#!/usr/bin/env python3
"""
Test Enhanced Workflow Orchestrator
====================================

Tests the new MODALITY → MODEL enforcement system with LangChain and CrewAI patterns.

This validates:
1. Modality detection from user requests
2. Model selection based on modality (not model → modality inference)
3. LangChain-style task interpretation
4. CrewAI-style task delegation
5. End-to-end workflow execution
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def test_modality_detection():
    """Test modality detection system."""
    from anthropic import Anthropic
    from src.core.modality_system import get_modality_detector
    
    print("\n" + "="*70)
    print("TEST 1: Modality Detection")
    print("="*70)
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key or anthropic_api_key.startswith("your_"):
        print("⚠️  ANTHROPIC_API_KEY not set, using mock mode")
        return
    
    client = Anthropic(api_key=anthropic_api_key)
    detector = get_modality_detector(client)
    
    test_requests = [
        "Create a logo for my coffee shop",
        "Generate a promotional video for our new product",
        "Write a blog post about AI trends",
        "Create an image of a sunset and write a poem about it",
        "Build me a website with animations and interactive elements"
    ]
    
    for request in test_requests:
        print(f"\n📝 Request: {request}")
        modalities = await detector.detect_modalities(request)
        print(f"   Detected modalities:")
        for m in modalities:
            print(f"      • {m.modality.value} (priority: {m.priority}, quality: {m.quality_level})")


async def test_modality_to_model_mapping():
    """Test MODALITY → MODEL mapping."""
    from src.core.modality_system import get_modality_mapper, Modality, ModalityRequirement
    
    print("\n" + "="*70)
    print("TEST 2: MODALITY → MODEL Mapping")
    print("="*70)
    
    mapper = get_modality_mapper()
    
    test_modalities = [
        Modality.TEXT,
        Modality.IMAGE,
        Modality.VIDEO,
        Modality.AUDIO,
        Modality.CODE
    ]
    
    print("\n🎯 Testing different quality levels and preferences:\n")
    
    for modality in test_modalities:
        print(f"{modality.value.upper()}:")
        
        # Standard quality
        model = mapper.select_model(modality, quality_level="standard")
        print(f"  Standard: {model}")
        
        # High quality
        model = mapper.select_model(modality, quality_level="high")
        print(f"  High quality: {model}")
        
        # Prefer speed
        model = mapper.select_model(modality, prefer_speed=True)
        print(f"  Prefer speed: {model}")
        
        # Prefer cost
        model = mapper.select_model(modality, prefer_cost=True)
        print(f"  Prefer cost: {model}")
        
        print()


async def test_task_interpretation():
    """Test LangChain-based task interpretation."""
    from anthropic import Anthropic
    from src.core.langchain_task_interpreter import get_task_interpreter
    
    print("\n" + "="*70)
    print("TEST 3: LangChain Task Interpretation")
    print("="*70)
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key or anthropic_api_key.startswith("your_"):
        print("⚠️  ANTHROPIC_API_KEY not set, skipping test")
        return
    
    client = Anthropic(api_key=anthropic_api_key)
    interpreter = get_task_interpreter(client)
    
    test_request = "Create a professional logo for 'EcoTech Solutions', a sustainable technology company. It should be modern, include green colors, and convey innovation."
    
    print(f"\n📝 Request: {test_request}\n")
    
    interpreted = await interpreter.interpret_task(test_request)
    
    print(f"✅ Task Interpretation Complete:")
    print(f"   Task Type: {interpreted.task_type.value}")
    print(f"   Complexity: {interpreted.complexity.value}")
    print(f"   Primary Goal: {interpreted.primary_goal}")
    print(f"   Required Modalities: {', '.join(interpreted.required_modalities)}")
    print(f"   Steps: {len(interpreted.steps)}")
    print(f"   Estimated Duration: {interpreted.estimated_duration_minutes} minutes")
    print(f"\n   Success Criteria:")
    for criterion in interpreted.success_criteria:
        print(f"      • {criterion}")
    
    if interpreted.parameters:
        print(f"\n   Parameters:")
        for param in interpreted.parameters[:5]:  # Show first 5
            print(f"      • {param.name}: {param.value} ({param.type})")


async def test_full_workflow():
    """Test complete workflow orchestration."""
    from anthropic import Anthropic
    from src.core.enhanced_workflow_orchestrator import get_enhanced_orchestrator
    from src.core.tool_registry import ToolRegistry
    
    print("\n" + "="*70)
    print("TEST 4: Complete Workflow Orchestration")
    print("="*70)
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key or anthropic_api_key.startswith("your_"):
        print("⚠️  ANTHROPIC_API_KEY not set, skipping test")
        return
    
    client = Anthropic(api_key=anthropic_api_key)
    tool_registry = ToolRegistry()
    
    orchestrator = get_enhanced_orchestrator(client, tool_registry)
    
    test_request = "Write a short blog post about renewable energy and create a featured image"
    
    print(f"\n📝 Request: {test_request}\n")
    print("🚀 Executing workflow...\n")
    
    # Callback to show progress
    async def progress_callback(update):
        update_type = update.get("type")
        
        if update_type == "workflow_started":
            print(f"🎬 Workflow started: {update['workflow_id']}")
        
        elif update_type == "stage_started":
            print(f"   ➤ Stage: {update['stage']}")
        
        elif update_type == "stage_completed":
            stage = update['stage']
            print(f"   ✅ {stage} completed")
            
            if stage == "modality_detection":
                print(f"      Modalities: {', '.join(update.get('modalities', []))}")
            elif stage == "model_selection":
                print(f"      Model mapping:")
                for mod, model in update.get('mapping', {}).items():
                    print(f"         {mod} → {model}")
        
        elif update_type == "agent_started":
            print(f"      🤖 Agent: {update['agent']} ({update['role']})")
        
        elif update_type == "agent_completed":
            print(f"      ✅ Agent completed")
        
        elif update_type == "workflow_completed":
            print(f"\n✅ Workflow completed!")
            print(f"   Quality Score: {update['quality_score']:.2f}")
            print(f"   Duration: {update['duration']:.1f}s")
    
    result = await orchestrator.execute_workflow(
        test_request,
        context={"test_mode": True},
        callback=progress_callback
    )
    
    print("\n" + "-"*70)
    print("WORKFLOW RESULT:")
    print("-"*70)
    print(f"Success: {result.success}")
    print(f"Quality Score: {result.quality_score:.2f}")
    print(f"Total Duration: {result.total_duration:.1f}s")
    print(f"\nModalities Detected:")
    for m in result.detected_modalities:
        print(f"   • {m.modality.value} (priority {m.priority})")
    
    print(f"\nModality → Model Mapping:")
    for modality, model in result.modality_model_mapping.items():
        print(f"   {modality} → {model}")
    
    print(f"\nStages:")
    for stage in result.stages:
        status_icon = "✅" if stage.status == "completed" else "❌" if stage.status == "failed" else "⏳"
        print(f"   {status_icon} {stage.stage_name}: {stage.duration:.2f}s")
    
    print(f"\nFinal Output (truncated):")
    output_str = str(result.final_output)
    print(f"   {output_str[:300]}...")
    
    # Show workflow stats
    print("\n" + "-"*70)
    stats = orchestrator.get_workflow_stats()
    print("ORCHESTRATOR STATISTICS:")
    print("-"*70)
    print(f"Total Workflows: {stats['total_workflows']}")
    if stats['total_workflows'] > 0:
        print(f"Success Rate: {stats['success_rate']:.1%}")
        print(f"Average Duration: {stats['avg_duration']:.1f}s")
        print(f"Average Quality: {stats['avg_quality_score']:.2f}")
        print(f"\nModality Usage:")
        for modality, count in stats['modality_usage'].items():
            print(f"   {modality}: {count}")


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" ENHANCED WORKFLOW ORCHESTRATOR TEST SUITE")
    print(" MODALITY → MODEL Enforcement Demo")
    print("="*70)
    
    try:
        # Test 1: Modality Detection
        await test_modality_detection()
        
        # Test 2: Model Selection
        await test_modality_to_model_mapping()
        
        # Test 3: Task Interpretation
        await test_task_interpretation()
        
        # Test 4: Full Workflow
        await test_full_workflow()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print("\n" + "="*70)
        print(f"❌ TEST FAILED: {e}")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
