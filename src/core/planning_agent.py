"""
Planning Agent - Task Decomposition and Strategy
=================================================

This agent analyzes user requests and creates execution plans.
It figures out WHAT needs to be done and HOW to do it.
"""

import logging
from typing import Any, Dict, List
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class PlanningAgent:
    """
    Agent responsible for understanding requests and creating execution plans.
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        
    async def create_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze request and create execution plan.
        
        Args:
            context: Dict containing message, memories, available_tools
            
        Returns:
            Dict with plan details including steps and strategy
        """
        message = context["message"]
        available_tools = context.get("available_tools", [])
        memories = context.get("memories", [])
        
        # Format available tools for AI
        tools_description = self._format_tools(available_tools)
        memory_context = self._format_memories(memories)
        
        # Create planning prompt
        prompt = f"""You are Otto's Planning Agent. Analyze the user's request and create an execution plan.

User Request: {message}

Available Tools:
{tools_description}

Recent Context:
{memory_context}

TASK: Create a plan to fulfill the user's request.

Response Format (JSON):
{{
    "intent": "brief description of what user wants",
    "requires_tools": true/false,
    "steps": [
        {{
            "tool": "tool_name",
            "description": "what this step does",
            "parameters": {{"param": "value"}},
            "depends_on": []  // list of previous step indices
        }}
    ],
    "strategy": "explanation of approach",
    "estimated_time": "rough time estimate"
}}

If no tools needed (simple conversation), return {{"requires_tools": false}}.

Examples:

Request: "Generate a t-shirt design with mountains"
Plan:
{{
    "intent": "Generate product design",
    "requires_tools": true,
    "steps": [
        {{
            "tool": "generate_image",
            "description": "Create mountain t-shirt design",
            "parameters": {{
                "prompt": "t-shirt graphic design, mountain landscape, minimalist style",
                "model": "flux-fast"
            }},
            "depends_on": []
        }}
    ],
    "strategy": "Use fast image generation model for quick iteration",
    "estimated_time": "10-15 seconds"
}}

Request: "Create a complete campaign for eco-friendly water bottles"
Plan:
{{
    "intent": "Full marketing campaign generation",
    "requires_tools": true,
    "steps": [
        {{
            "tool": "generate_campaign_strategy",
            "description": "Create marketing strategy",
            "parameters": {{"product": "eco-friendly water bottles"}},
            "depends_on": []
        }},
        {{
            "tool": "generate_product_designs",
            "description": "Create 5 product designs",
            "parameters": {{
                "theme": "eco-friendly",
                "product": "water bottle",
                "count": 5
            }},
            "depends_on": [0]
        }},
        {{
            "tool": "create_mockups",
            "description": "Generate product mockups",
            "parameters": {{"designs": "from_step_1"}},
            "depends_on": [1]
        }},
        {{
            "tool": "generate_video_ad",
            "description": "Create 30-second video ad",
            "parameters": {{"product": "eco water bottle", "duration": 30}},
            "depends_on": [2]
        }},
        {{
            "tool": "write_content",
            "description": "Generate social media content",
            "parameters": {{"platform": "all", "product": "eco water bottle"}},
            "depends_on": [1, 3]
        }}
    ],
    "strategy": "Sequential execution with dependencies - strategy first, then designs, mockups, video, and finally written content",
    "estimated_time": "5-7 minutes"
}}

Now create a plan for the user's request."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON from response
            import json
            plan_text = response.content[0].text
            
            # Extract JSON from markdown code blocks if present
            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(plan_text)
            
            logger.info(f"Created plan: {plan.get('intent', 'unknown')}")
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}", exc_info=True)
            # Return simple plan on failure
            return {
                "intent": message,
                "requires_tools": False,
                "error": str(e)
            }
    
    def _format_tools(self, tools: List[Dict[str, Any]]) -> str:
        """Format available tools for AI consumption."""
        if not tools:
            return "No tools available"
        
        formatted = []
        for tool in tools[:50]:  # Limit to avoid token overflow
            formatted.append(
                f"- {tool['name']}: {tool.get('description', 'N/A')}"
            )
        
        return "\\n".join(formatted)
    
    def _format_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for context."""
        if not memories:
            return "No previous context"
        
        formatted = []
        for mem in memories[:5]:
            formatted.append(f"- {mem.get('content', 'N/A')}")
        
        return "\\n".join(formatted)
