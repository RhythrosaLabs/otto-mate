#!/usr/bin/env python3
"""
Quick Start Script for Otto Universal v2.0
==========================================

This script demonstrates the new super intelligent system capabilities.
"""

import asyncio
import json
from anthropic import Anthropic, AsyncAnthropic

# Import new v2 components
from src.core.unified_agent_system import (
    IntelligentAgent,
    AgentCrew,
    AgentConfig,
    AgentRole,
    AgentTask,
    AgentMode
)
from src.core.super_intelligent_chat import SuperIntelligentChat
from src.core.tool_registry import ToolRegistry


async def demo_super_intelligent_chat():
    """Demonstrate the super intelligent chat capabilities."""
    print("\n" + "="*80)
    print("DEMO 1: Super Intelligent Chat")
    print("="*80 + "\n")
    
    # Initialize
    anthropic = Anthropic()
    async_anthropic = AsyncAnthropic()
    tools = ToolRegistry()
    
    chat = SuperIntelligentChat(
        anthropic_client=anthropic,
        async_anthropic_client=async_anthropic,
        tool_registry=tools
    )
    
    # Example 1: Simple chat
    print("Example 1: Simple Conversation")
    print("-" * 40)
    response = await chat.chat(
        message="What can you help me with?",
        stream=False
    )
    print(f"Otto: {response}\n")
    
    # Example 2: Complex task
    print("Example 2: Complex Task Execution")
    print("-" * 40)
    response = await chat.chat(
        message="Explain the key differences between CrewAI, AutoGPT, and Claude SDK in terms of agent architecture",
        stream=False,
        use_tools=True
    )
    print(f"Otto: {response}\n")
    
    # Example 3: Streaming response
    print("Example 3: Streaming Response")
    print("-" * 40)
    print("Otto: ", end='', flush=True)
    async for chunk in await chat.chat(
        message="Tell me about the benefits of multi-agent systems",
        stream=True
    ):
        print(chunk, end='', flush=True)
    print("\n")


async def demo_agent_crew():
    """Demonstrate multi-agent crew capabilities."""
    print("\n" + "="*80)
    print("DEMO 2: Multi-Agent Crew")
    print("="*80 + "\n")
    
    # Initialize
    anthropic = Anthropic()
    tools = ToolRegistry()
    
    # Create crew
    crew = AgentCrew(
        name="Demo Crew",
        anthropic_client=anthropic,
        tool_registry=tools
    )
    
    # Add agents
    print("Creating specialized agents...")
    
    crew.add_agent(AgentConfig(
        agent_id="orchestrator",
        role=AgentRole.ORCHESTRATOR,
        name="Demo Orchestrator",
        description="Coordinates the crew",
        capabilities=["coordination", "planning"],
        mode=AgentMode.AUTONOMOUS
    ))
    
    crew.add_agent(AgentConfig(
        agent_id="researcher",
        role=AgentRole.RESEARCHER,
        name="Demo Researcher",
        description="Conducts research",
        capabilities=["research", "analysis"],
        mode=AgentMode.AUTONOMOUS
    ))
    
    crew.add_agent(AgentConfig(
        agent_id="executor",
        role=AgentRole.EXECUTOR,
        name="Demo Executor",
        description="Executes tasks",
        capabilities=["execution", "tools"],
        tools=["all"],
        mode=AgentMode.AUTONOMOUS
    ))
    
    print(f"Created crew with {len(crew.agents)} agents\n")
    
    # Show crew status
    status = crew.get_crew_status()
    print("Crew Status:")
    print(json.dumps(status, indent=2))
    print()
    
    # Execute a task
    print("Executing collaborative task...")
    task = AgentTask(
        task_id="demo_task_001",
        description="Research the latest AI agent frameworks and summarize key features",
        goal="Provide a comprehensive comparison"
    )
    
    result = await crew.execute_task(task)
    print(f"\nTask Result:")
    print(json.dumps(result, indent=2))


async def demo_autonomous_task():
    """Demonstrate autonomous task execution."""
    print("\n" + "="*80)
    print("DEMO 3: Autonomous Task Execution")
    print("="*80 + "\n")
    
    # Initialize
    anthropic = Anthropic()
    tools = ToolRegistry()
    
    # Create single intelligent agent
    agent = IntelligentAgent(
        config=AgentConfig(
            agent_id="demo_agent",
            role=AgentRole.EXECUTOR,
            name="Demo Agent",
            description="Autonomous agent for task execution",
            capabilities=["autonomous_execution", "self_correction"],
            mode=AgentMode.AUTONOMOUS,
            use_thinking=True,
            use_planning=True,
            max_iterations=5
        ),
        anthropic_client=anthropic,
        tool_registry=tools
    )
    
    # Create and execute task
    print("Creating autonomous task...")
    task = AgentTask(
        task_id="autonomous_001",
        description="Analyze the architecture of Otto Universal and suggest improvements",
        goal="Provide actionable recommendations",
        max_steps=10
    )
    
    print("Executing autonomously...\n")
    result = await agent.execute_task(task)
    
    print(f"Task Status: {result['status']}")
    print(f"Steps Taken: {result['steps_taken']}")
    print(f"Duration: {result.get('duration', 'N/A')} seconds")
    print(f"\nResult:")
    print(json.dumps(result.get('result', {}), indent=2))
    
    # Show thinking log
    if task.thinking_log:
        print(f"\nThinking Process:")
        for i, thought in enumerate(task.thinking_log, 1):
            print(f"{i}. {thought}")


async def demo_vision_capabilities():
    """Demonstrate vision capabilities."""
    print("\n" + "="*80)
    print("DEMO 4: Vision Capabilities")
    print("="*80 + "\n")
    
    print("Vision capabilities are enabled!")
    print("You can:")
    print("1. Analyze images")
    print("2. Extract text (OCR)")
    print("3. Understand visual context")
    print("4. Combine vision with reasoning")
    print("\nExample:")
    print("""
    chat = SuperIntelligentChat()
    response = await chat.chat(
        message="Analyze this product image",
        images=[{
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64_image_data
        }],
        use_vision=True
    )
    """)


async def demo_monitoring():
    """Demonstrate monitoring capabilities."""
    print("\n" + "="*80)
    print("DEMO 5: Monitoring & Observability")
    print("="*80 + "\n")
    
    from src.core.agent_health_monitor import get_health_monitor
    from src.core.agent_analytics import get_analytics
    
    # Get health status
    health_monitor = get_health_monitor()
    health = health_monitor.get_system_health()
    
    print("System Health:")
    print(json.dumps(health, indent=2, default=str))
    print()
    
    # Get analytics
    analytics = get_analytics()
    
    print("Available Analytics:")
    print("- Agent performance profiles")
    print("- Task execution history")
    print("- Bottleneck identification")
    print("- Cost forecasting")
    print("- Resource utilization")


async def main():
    """Run all demos."""
    print("\n" + "="*80)
    print("Otto Universal v2.0 - Quick Start Demos")
    print("="*80)
    
    demos = [
        ("Super Intelligent Chat", demo_super_intelligent_chat),
        ("Multi-Agent Crew", demo_agent_crew),
        ("Autonomous Task Execution", demo_autonomous_task),
        ("Vision Capabilities", demo_vision_capabilities),
        ("Monitoring & Observability", demo_monitoring),
    ]
    
    print("\nAvailable Demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"{i}. {name}")
    
    print("\nRunning all demos...\n")
    
    try:
        # Run demos
        # Note: Some demos are commented out to avoid API calls during testing
        
        # await demo_super_intelligent_chat()  # Requires API key
        # await demo_agent_crew()  # Requires API key
        # await demo_autonomous_task()  # Requires API key
        await demo_vision_capabilities()  # Just info, no API
        await demo_monitoring()  # System status
        
        print("\n" + "="*80)
        print("Demos Complete!")
        print("="*80)
        print("\nNext Steps:")
        print("1. Set your ANTHROPIC_API_KEY environment variable")
        print("2. Run: python quickstart_v2.py")
        print("3. Or start the server: python -c 'from src.api.main_v2 import app; import uvicorn; uvicorn.run(app, port=8000)'")
        print("4. Test the API: curl http://localhost:8000/api/v2/chat -X POST -H 'Content-Type: application/json' -d '{\"message\":\"Hello!\"}'")
        
    except Exception as e:
        print(f"\nError running demos: {e}")
        print("\nNote: Some demos require ANTHROPIC_API_KEY to be set")
        print("Export it with: export ANTHROPIC_API_KEY='your-key-here'")


if __name__ == "__main__":
    # Check for API key
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not set!")
        print("Some demos will be skipped.")
        print("To enable all demos, run:")
        print("  export ANTHROPIC_API_KEY='your-key-here'\n")
    
    asyncio.run(main())
