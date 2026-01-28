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

CRITICAL RULE - TOOL PRIORITY ORDER:
1. ALWAYS use DIRECT TOOLS FIRST - check available tools before writing code
2. For IMAGE GENERATION: Use "generate_image" or "generate_tshirt_design" - NOT code!
3. For T-SHIRT DESIGNS: Use "generate_tshirt_design" which is optimized for apparel
4. Only use code execution for data processing, calculations, or when NO direct tool exists

YOUR SUPERPOWERS:
1. DIRECT IMAGE GENERATION - Use "generate_image" for any image, "generate_tshirt_design" for apparel designs
2. PRODUCT CREATION - Use "printify_create_tshirt" to make products on Printify
3. ACCESS TO ANY REPLICATE AI MODEL - "replicate_smart_generate" or "replicate_run_model" for specialized AI
4. CODE EXECUTION - ONLY use "execute_python" when no direct tool exists (data analysis, calculations)
5. FILE CREATION - Create any file with 'create_file'
6. WEB RESEARCH - Search and browse the web with research tools

PLANNING PHILOSOPHY:
- ALWAYS check if a direct tool exists before writing code
- For images: generate_image, generate_tshirt_design, replicate_smart_generate
- For products: printify_create_tshirt, printify_create_mug
- NEVER use execute_python for image generation - use the image tools!
- For complex tasks, BREAK DOWN into multiple steps with dependencies
- If something might fail, plan a FALLBACK approach

AUTONOMOUS PROBLEM SOLVING:
1. Understand what the user REALLY wants (the end goal)
2. Check AVAILABLE TOOLS for direct solutions first
3. Choose the SIMPLEST tool that accomplishes the task
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

For IMAGE GENERATION (ALWAYS use these first!):
1. "generate_image" - General purpose AI image generation (prompt required)
2. "generate_tshirt_design" - Optimized for apparel designs
3. "replicate_smart_generate" - For specialized/advanced generation
4. NEVER use execute_python for image generation!

For PRODUCT CREATION on Printify:
1. "printify_create_tshirt" - Create t-shirt with design image
2. "printify_create_mug" - Create mug with design image
3. "printify_upload_image" - Upload image first if needed

For data/computation tasks (appropriate for code):
1. Use "execute_python" with code that solves the problem
2. Include error handling in the code
3. Print results so they're captured

For file operations:
1. Use "create_file" to write any content
2. Use "read_file" to read existing files
3. Use "execute_shell" for complex file operations

For tasks with no direct tool:
1. First: Is there an existing tool? Check available_tools carefully!
2. Then: Can I use replicate_smart_generate for AI tasks?
3. Last resort: Write Python code only if truly necessary

=== EXAMPLE COMPLEX PLANS ===

Request: "Generate a husky t-shirt design"
Plan:
{{
    "intent": "Create a husky-themed t-shirt design",
    "approach": "Use generate_tshirt_design for apparel-optimized image generation",
    "requires_tools": true,
    "steps": [
        {{
            "tool": "generate_tshirt_design",
            "description": "Generate husky design optimized for t-shirt printing",
            "parameters": {{
                "prompt": "Adorable husky dog face illustration, vector art style, high contrast, centered composition, professional t-shirt design"
            }},
            "depends_on": [],
            "critical": true,
            "fallback": "Try generate_image if generate_tshirt_design fails"
        }}
    ],
    "verification": "Check that output contains image URL",
    "estimated_time": "15-30 seconds",
    "success_criteria": "High-quality husky design image URL returned"
}}

Request: "Create an image of a dancing turkey"
Plan:
{{
    "intent": "Generate an AI image of a dancing turkey",
    "approach": "Use generate_image tool directly - it's the fastest way to create images",
    "requires_tools": true,
    "steps": [
        {{
            "tool": "generate_image",
            "description": "Generate dancing turkey image using AI",
            "parameters": {{
                "prompt": "A happy cartoon turkey dancing, festive, fun, colorful, high quality illustration"
            }},
            "depends_on": [],
            "critical": true
        }}
    ],
    "verification": "Check that output contains image URL",
    "estimated_time": "10-20 seconds",
    "success_criteria": "Dancing turkey image URL returned"
}}

Request: "Analyze my sales data and create visualizations"
Plan:
{{
    "intent": "Analyze sales data and generate charts",
    "approach": "Use Python code execution for data processing - this is appropriate since it's a computation task",
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
