"""
Super Planning Agent - Autonomous Task Solving
==============================================

An intelligent agent that can break down complex tasks, adapt strategies,
recover from failures, and find creative solutions to any problem.
"""

import logging
import json
import re
from typing import Any, Dict, List, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class SuperPlanningAgent:
    """
    Hyper-intelligent planning agent with:
    - Multi-strategy problem decomposition
    - Adaptive plan modification
    - Failure recovery and retries
    - Code generation for novel problems
    - Model discovery for AI tasks
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        
        # System capabilities description
        self.capabilities_prompt = """You are Otto's SUPER Planning Agent - an extremely capable autonomous system.

YOUR SUPERPOWERS:
1. ACCESS TO ANY REPLICATE AI MODEL - Search 'replicate_search_models' to find any AI model, then run it with 'replicate_run_model'
2. CODE EXECUTION - Write and execute Python code with 'execute_python' to solve ANY computational problem
3. FILE CREATION - Create any file (scripts, configs, data) with 'create_file'
4. SHELL COMMANDS - Run any shell command with 'execute_shell'
5. WEB RESEARCH - Search and browse the web with research tools
6. DATA PROCESSING - Transform and analyze data with 'process_json' and 'convert_format'

PLANNING PHILOSOPHY:
- If a direct tool doesn't exist, WRITE CODE to accomplish the task
- If you need an AI model, SEARCH for it on Replicate and use it
- NEVER say you can't do something - find a creative solution
- For complex tasks, BREAK DOWN into multiple steps with dependencies
- If something might fail, plan a FALLBACK approach

AUTONOMOUS PROBLEM SOLVING:
1. Understand what the user REALLY wants (the end goal)
2. Identify ALL possible approaches to achieve it
3. Choose the MOST LIKELY to succeed
4. Plan BACKUP strategies if primary fails
5. Include VERIFICATION steps to confirm success"""

    async def create_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an intelligent, adaptive execution plan.
        """
        message = context["message"]
        available_tools = context.get("available_tools", [])
        memories = context.get("memories", [])
        
        # Categorize tools
        tools_by_category = self._categorize_tools(available_tools)
        tools_description = self._format_tools_enhanced(available_tools, tools_by_category)
        memory_context = self._format_memories(memories)
        
        prompt = f"""{self.capabilities_prompt}

=== CURRENT REQUEST ===
User Message: {message}

=== AVAILABLE TOOLS BY CATEGORY ===
{tools_description}

=== RECENT CONTEXT ===
{memory_context}

=== YOUR TASK ===
Create a comprehensive execution plan. Think step by step:

1. What is the user's END GOAL?
2. What's the BEST approach to achieve it?
3. What tools do I need? If a tool doesn't exist, can I use code/AI models?
4. What could go wrong? Plan for it.
5. How do I verify success?

=== RESPONSE FORMAT (JSON) ===
{{
    "intent": "Clear description of user's goal",
    "approach": "High-level strategy explanation",
    "requires_tools": true,
    "steps": [
        {{
            "tool": "tool_name",
            "description": "What this step accomplishes",
            "parameters": {{}},
            "depends_on": [],
            "fallback": "Optional alternative if this fails",
            "critical": true/false
        }}
    ],
    "verification": "How to confirm success",
    "estimated_time": "Time estimate",
    "success_criteria": "What defines success",
    "notes": "Any important considerations"
}}

=== SPECIAL CAPABILITIES ===

For ANY AI generation task (images, video, audio, 3D, text):
1. First use "replicate_search_models" to find the best model
2. Then use "replicate_get_model_info" to understand inputs
3. Finally use "replicate_run_model" with correct parameters

For data/computation tasks:
1. Use "execute_python" with code that solves the problem
2. Include error handling in the code
3. Print results so they're captured

For file operations:
1. Use "create_file" to write any content
2. Use "read_file" to read existing files
3. Use "execute_shell" for complex file operations

For tasks with no direct tool:
1. Think: Can I write Python code to do this?
2. Think: Is there an AI model that could help?
3. Think: Can I combine multiple tools creatively?

=== EXAMPLE COMPLEX PLANS ===

Request: "Generate a husky t-shirt design"
Plan:
{{
    "intent": "Create a husky-themed t-shirt design",
    "approach": "Use smart image generation with t-shirt-optimized prompts",
    "requires_tools": true,
    "steps": [
        {{
            "tool": "replicate_smart_generate",
            "description": "Generate husky design optimized for t-shirt printing",
            "parameters": {{
                "description": "Adorable husky dog face illustration, vector art style, high contrast, no background, centered composition, t-shirt design ready, clean lines, professional quality",
                "content_type": "image",
                "style": "vector illustration",
                "quality": "best"
            }},
            "depends_on": [],
            "critical": true,
            "fallback": "Try flux_schnell model directly if smart_generate fails"
        }}
    ],
    "verification": "Check that output contains image URL",
    "estimated_time": "15-30 seconds",
    "success_criteria": "High-quality husky design image URL returned"
}}

Request: "Analyze my sales data and create visualizations"
Plan:
{{
    "intent": "Analyze sales data and generate charts",
    "approach": "Use Python code execution to process data and create visualizations",
    "requires_tools": true,
    "steps": [
        {{
            "tool": "execute_python",
            "description": "Load, analyze data and generate statistics + charts",
            "parameters": {{
                "code": "import json\\nimport pandas as pd\\nimport matplotlib.pyplot as plt\\n\\n# Your analysis code here\\nprint(json.dumps(results))"
            }},
            "depends_on": [],
            "critical": true
        }},
        {{
            "tool": "create_file",
            "description": "Save analysis report",
            "parameters": {{
                "filename": "sales_analysis.md",
                "content": "# Sales Analysis Report\\n..."
            }},
            "depends_on": [0]
        }}
    ],
    "verification": "Report file created with insights",
    "estimated_time": "1-2 minutes"
}}

Now create your plan for: "{message}"

Return ONLY valid JSON."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            plan_text = response.content[0].text
            plan = self._parse_json_response(plan_text)
            
            # Validate and enhance plan
            plan = self._validate_plan(plan, available_tools)
            
            logger.info(f"Created super plan: {plan.get('intent', 'unknown')}")
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}", exc_info=True)
            # Return a fallback plan that tries to help
            return self._create_fallback_plan(message, str(e))
    
    async def adapt_plan(
        self,
        original_plan: Dict[str, Any],
        failed_step: int,
        error: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt a plan after a step fails.
        """
        prompt = f"""A step in the execution plan failed. Create an adapted plan to still achieve the goal.

Original Intent: {original_plan.get('intent', 'unknown')}

Failed Step #{failed_step}: {original_plan.get('steps', [{}])[failed_step] if failed_step < len(original_plan.get('steps', [])) else 'unknown'}

Error: {error}

Available Tools: {[t['name'] for t in context.get('available_tools', [])[:30]]}

Create a NEW plan that:
1. Works around the failed step
2. Uses alternative approaches
3. Still achieves the user's goal

Return valid JSON with same format as original plan."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_json_response(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Plan adaptation failed: {e}")
            return {"requires_tools": False, "error": str(e)}
    
    def _categorize_tools(self, tools: List[Dict]) -> Dict[str, List[str]]:
        """Categorize tools by type."""
        categories = {}
        for tool in tools:
            cat = tool.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool["name"])
        return categories
    
    def _format_tools_enhanced(self, tools: List[Dict], by_category: Dict) -> str:
        """Format tools in a more useful way for the AI."""
        output = []
        
        for category, tool_names in by_category.items():
            output.append(f"\n### {category.upper()}")
            for tool in tools:
                if tool["name"] in tool_names:
                    desc = tool.get("description", "No description")[:100]
                    output.append(f"  - {tool['name']}: {desc}")
        
        # Highlight key capabilities
        output.append("\n### KEY CAPABILITIES")
        output.append("  - replicate_*: Search/run ANY AI model on Replicate")
        output.append("  - execute_python: Run any Python code")
        output.append("  - execute_shell: Run any shell command")
        output.append("  - create_file/read_file: File operations")
        output.append("  - search_web/browse_url: Web research")
        
        return "\n".join(output)
    
    def _format_memories(self, memories: List[Dict]) -> str:
        """Format memories for context."""
        if not memories:
            return "No previous context"
        return "\n".join([f"- {m.get('content', '')[:100]}" for m in memories[:5]])
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from AI response, handling markdown formatting."""
        # Try to extract JSON from various formats
        text = text.strip()
        
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
        
        # Find JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            text = match.group()
        
        return json.loads(text.strip())
    
    def _validate_plan(self, plan: Dict, available_tools: List[Dict]) -> Dict:
        """Validate and enhance the plan."""
        tool_names = {t["name"] for t in available_tools}
        
        # Ensure required fields
        plan.setdefault("requires_tools", bool(plan.get("steps")))
        plan.setdefault("intent", "Execute user request")
        plan.setdefault("steps", [])
        
        # Validate steps reference existing tools
        for step in plan.get("steps", []):
            tool_name = step.get("tool", "")
            if tool_name and tool_name not in tool_names:
                # Tool doesn't exist - maybe it can be done with code?
                step["note"] = f"Tool '{tool_name}' not found, may need fallback"
        
        return plan
    
    def _create_fallback_plan(self, message: str, error: str) -> Dict:
        """Create a fallback plan when planning fails."""
        return {
            "intent": message,
            "requires_tools": False,
            "error": f"Planning failed: {error}",
            "fallback_response": True,
            "steps": []
        }


# Enhanced Planning Agent export (replaces old one)
PlanningAgent = SuperPlanningAgent
