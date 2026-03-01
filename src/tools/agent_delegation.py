"""
Agent Delegation Tools
======================

Tools that enable Otto to delegate tasks to specialized subagents.
These tools provide intelligent task routing and multi-agent collaboration.
"""

import logging
from typing import Any, Dict, Optional, List
from ..core.enhanced_agent_delegation import (
    get_delegation_manager,
    SPECIALIZED_AGENTS,
    AgentSpecialization,
    TaskAnalyzer
)

logger = logging.getLogger(__name__)


class AgentDelegationTools:
    """
    Tools for delegating tasks to specialized AI agents.
    
    These tools enable Otto to:
    - Route tasks to the most appropriate specialized agent
    - Coordinate multi-agent collaboration
    - Execute complex workflows with expert agents
    """
    
    def __init__(self, anthropic_client: Any = None, tool_registry: Any = None):
        self.anthropic = anthropic_client
        self.tool_registry = tool_registry
        self.task_analyzer = TaskAnalyzer()
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all agent delegation tools."""
        return [
            {
                "name": "delegate_to_specialist",
                "description": """Delegate a task to a specialized AI agent for expert execution.
                
This tool routes tasks to domain experts:
- Content Writer - for articles, blog posts, descriptions
- Copywriter - for headlines, ads, marketing copy
- Social Media Manager - for social posts, engagement
- Image Creator - for AI image generation
- Video Producer - for AI video creation
- Code Developer - for programming tasks
- Data Analyst - for data analysis and insights
- Market Researcher - for market/competitor research
- E-commerce Expert - for product listings, store management
- Browser Operator - for web scraping, automation
- Project Manager - for planning and coordination
- Automation Engineer - for workflows and automations

The system automatically selects the best agent based on the task, or you can specify one.""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The task to delegate to a specialist agent"
                        },
                        "preferred_specialist": {
                            "type": "string",
                            "description": "Optional: specific specialist to use (content_writer, copywriter, image_creator, video_producer, code_developer, data_analyst, market_researcher, ecommerce_expert, browser_operator, project_manager, automation_engineer)",
                            "enum": [
                                "content_writer", "copywriter", "social_media_manager",
                                "image_creator", "video_producer", "code_developer",
                                "data_analyst", "market_researcher", "ecommerce_expert",
                                "browser_operator", "project_manager", "automation_engineer"
                            ]
                        },
                        "context": {
                            "type": "object",
                            "description": "Optional context to provide the specialist"
                        },
                        "allow_collaboration": {
                            "type": "boolean",
                            "description": "Allow multiple specialists to collaborate on complex tasks",
                            "default": True
                        }
                    },
                    "required": ["task"]
                },
                "category": "agent_delegation",
                "handler": self.delegate_to_specialist
            },
            {
                "name": "get_task_recommendation",
                "description": """Analyze a task and get recommendations for which specialist agent(s) should handle it.
                
Returns the best-matched specialists with match scores and whether collaboration is recommended.""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The task to analyze"
                        }
                    },
                    "required": ["task"]
                },
                "category": "agent_delegation",
                "handler": self.get_task_recommendation
            },
            {
                "name": "list_available_specialists",
                "description": "List all available specialist agents and their capabilities.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "category": "agent_delegation",
                "handler": self.list_available_specialists
            },
            {
                "name": "run_collaborative_task",
                "description": """Execute a complex task using multiple collaborating specialist agents.
                
This is ideal for multi-domain tasks that benefit from different expertises:
- "Create a marketing campaign" → Copywriter + Designer + Social Media Manager
- "Build and launch a product" → Developer + E-commerce Expert + Content Writer
- "Research and create content" → Researcher + Content Writer + SEO Specialist""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The complex task requiring multiple specialists"
                        },
                        "specialists": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional: specific specialists to include in the team"
                        },
                        "context": {
                            "type": "object",
                            "description": "Shared context for all specialists"
                        }
                    },
                    "required": ["task"]
                },
                "category": "agent_delegation",
                "handler": self.run_collaborative_task
            }
        ]
    
    async def delegate_to_specialist(
        self,
        task: str,
        preferred_specialist: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        allow_collaboration: bool = True
    ) -> Dict[str, Any]:
        """
        Delegate a task to a specialized agent.
        """
        try:
            delegation_manager = get_delegation_manager(
                anthropic_client=self.anthropic,
                tool_registry=self.tool_registry
            )
            
            # Convert string to enum if specified
            preferred_agent = None
            if preferred_specialist:
                try:
                    preferred_agent = AgentSpecialization(preferred_specialist)
                except ValueError:
                    pass
            
            result = await delegation_manager.delegate(
                task_text=task,
                context=context,
                preferred_agent=preferred_agent,
                allow_collaboration=allow_collaboration
            )
            
            return {
                "success": result.success,
                "specialist": result.agent.value,
                "result": result.result,
                "duration_seconds": result.duration_seconds,
                "steps_taken": result.steps_taken,
                "collaborated_with": [a.value for a in result.delegated_to] if result.delegated_to else [],
                "errors": result.errors if result.errors else None
            }
            
        except Exception as e:
            logger.error(f"Delegation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_task_recommendation(self, task: str) -> Dict[str, Any]:
        """
        Analyze a task and recommend the best specialist(s).
        """
        try:
            analysis = self.task_analyzer.analyze(task)
            
            recommendations = []
            for agent, score in analysis.suggested_agents[:3]:
                profile = SPECIALIZED_AGENTS.get(agent)
                if profile:
                    recommendations.append({
                        "specialist": agent.value,
                        "name": profile.name,
                        "match_score": round(score, 2),
                        "capabilities": profile.capabilities[:3]
                    })
            
            return {
                "success": True,
                "task_type": analysis.task_type,
                "complexity": analysis.complexity,
                "domains": analysis.domains,
                "requires_collaboration": analysis.requires_collaboration,
                "estimated_steps": analysis.estimated_steps,
                "recommendations": recommendations,
                "best_match": recommendations[0] if recommendations else None
            }
            
        except Exception as e:
            logger.error(f"Task analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_available_specialists(self) -> Dict[str, Any]:
        """
        List all available specialist agents.
        """
        specialists = []
        
        for spec, profile in SPECIALIZED_AGENTS.items():
            specialists.append({
                "id": spec.value,
                "name": profile.name,
                "description": profile.description,
                "expertise": profile.expertise_keywords[:5],
                "capabilities": profile.capabilities,
                "preferred_tools": profile.preferred_tools[:3]
            })
        
        # Group by category
        categories = {
            "creative": ["content_writer", "copywriter", "social_media_manager", "seo_specialist", "brand_strategist"],
            "visual": ["image_creator", "video_producer", "ui_designer", "graphic_designer"],
            "technical": ["code_developer", "code_reviewer", "system_architect", "data_analyst", "api_integrator"],
            "research": ["market_researcher", "competitor_analyst", "trend_spotter", "data_miner"],
            "business": ["project_manager", "product_strategist", "marketing_specialist", "ecommerce_expert", "automation_engineer"],
            "operations": ["browser_operator", "file_manager", "communications_agent", "calendar_scheduler"],
            "meta": ["task_orchestrator", "quality_assurer", "context_gatherer"]
        }
        
        return {
            "success": True,
            "total_specialists": len(specialists),
            "specialists": specialists,
            "categories": categories
        }
    
    async def run_collaborative_task(
        self,
        task: str,
        specialists: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a collaborative task with multiple specialists.
        """
        try:
            delegation_manager = get_delegation_manager(
                anthropic_client=self.anthropic,
                tool_registry=self.tool_registry
            )
            
            # Force collaboration
            result = await delegation_manager.delegate(
                task_text=task,
                context=context,
                allow_collaboration=True
            )
            
            return {
                "success": result.success,
                "collaborative": True,
                "primary_specialist": result.agent.value,
                "team": [a.value for a in result.delegated_to] if result.delegated_to else [],
                "result": result.result,
                "duration_seconds": result.duration_seconds,
                "steps_taken": result.steps_taken
            }
            
        except Exception as e:
            logger.error(f"Collaborative task failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


def get_agent_delegation_tools(
    anthropic_client: Any = None,
    tool_registry: Any = None
) -> AgentDelegationTools:
    """Get the agent delegation tools instance."""
    return AgentDelegationTools(
        anthropic_client=anthropic_client,
        tool_registry=tool_registry
    )
