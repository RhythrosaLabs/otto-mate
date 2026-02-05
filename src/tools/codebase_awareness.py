"""
Otto Codebase Awareness
=======================

Enables Otto to understand its own codebase structure and functionality.
This self-awareness helps Otto make better decisions and understand its capabilities.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from .core import tool, ToolBase

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# OTTO'S SELF-KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════

OTTO_ARCHITECTURE = {
    "name": "Otto Universal AI",
    "version": "2.0",
    "description": "Autonomous AI assistant with full business automation capabilities",
    
    "core_components": {
        "agent_orchestrator": {
            "path": "src/core/agent_orchestrator.py",
            "purpose": "Main brain - coordinates all agents, handles chat, executes tools",
            "key_methods": ["process_message", "execute_tool", "plan_and_execute"]
        },
        "super_planning_agent": {
            "path": "src/core/super_planning_agent.py", 
            "purpose": "Creates detailed execution plans from user requests",
            "key_methods": ["create_plan", "decompose_task"]
        },
        "execution_agent": {
            "path": "src/core/execution_agent.py",
            "purpose": "Executes tool calls with smart retry and error recovery",
            "key_methods": ["execute_step", "handle_error"]
        },
        "verifier_agent": {
            "path": "src/core/verifier_agent.py",
            "purpose": "Validates results and ensures quality",
            "key_methods": ["verify_result", "check_success"]
        },
        "memory_agent": {
            "path": "src/core/memory_agent.py",
            "purpose": "Manages conversation history and long-term memory via ChromaDB",
            "key_methods": ["store_message", "recall", "get_session_history"]
        },
        "intelligence_system": {
            "path": "src/core/intelligence_system.py",
            "purpose": "Advanced reasoning, entity extraction, failure learning",
            "key_methods": ["extract_entities", "learn_from_failure"]
        }
    },
    
    "tool_categories": {
        "printify": {
            "path": "src/tools/printify.py",
            "tools": [
                "printify_create_product",
                "printify_smart_create_product",
                "printify_upload_image",
                "printify_list_products",
                "printify_publish_product",
                "printify_get_mockups"
            ],
            "purpose": "Print-on-demand product creation and management"
        },
        "shopify": {
            "path": "src/tools/shopify.py",
            "tools": ["shopify_create_product", "shopify_update_product", "shopify_list_products"],
            "purpose": "E-commerce store management"
        },
        "replicate": {
            "path": "src/tools/replicate_universal.py",
            "tools": ["replicate_smart_generate", "replicate_run_model", "replicate_search_models"],
            "purpose": "AI model execution - images, video, audio, 3D, text"
        },
        "video_generation": {
            "path": "src/tools/video_generation.py",
            "tools": ["generate_ai_video", "generate_ken_burns_video", "add_audio_to_video"],
            "purpose": "Video creation with 15+ AI models"
        },
        "browser": {
            "path": "src/tools/browser.py",
            "tools": ["browse_url", "search_web", "screenshot_page"],
            "purpose": "Web browsing and automation"
        },
        "content": {
            "path": "src/tools/content.py",
            "tools": ["write_article", "generate_social_post", "create_blog"],
            "purpose": "Content creation and copywriting"
        },
        "file_storage": {
            "path": "src/tools/file_storage.py",
            "tools": ["save_file", "read_file", "list_files", "delete_file"],
            "purpose": "File management and storage"
        },
        "code_execution": {
            "path": "src/tools/code_execution.py",
            "tools": ["execute_python", "execute_shell"],
            "purpose": "Safe code execution in sandbox"
        },
        "scheduler": {
            "path": "src/tools/scheduler.py",
            "tools": ["schedule_task", "list_scheduled_tasks", "cancel_task"],
            "purpose": "Cron-like task scheduling"
        },
        "youtube": {
            "path": "src/tools/youtube.py",
            "tools": ["youtube_upload_video", "youtube_search"],
            "purpose": "YouTube integration"
        }
    },
    
    "databases": {
        "sqlite": {
            "path": "data/otto.db",
            "purpose": "Structured data - conversations, projects, tasks, assets, API usage",
            "tables": ["conversations", "messages", "projects", "tasks", "generated_assets", "api_usage", "product_records"]
        },
        "chromadb": {
            "path": "data/chroma/",
            "purpose": "Vector database for semantic memory and recall"
        }
    },
    
    "api_layer": {
        "main": "src/api/main.py",
        "routes": [
            "src/api/agents.py",
            "src/api/files.py",
            "src/api/settings.py",
            "src/api/workflows.py",
            "src/api/projects.py",
            "src/api/conversations.py"
        ]
    },
    
    "web_interface": {
        "main_chat": "src/web/chat.html",
        "settings": "src/web/settings.html",
        "onboarding": "src/web/onboarding.html"
    },
    
    "skills_system": {
        "path": "skills/",
        "categories": [
            "business_operations",
            "content_creation", 
            "ecommerce_automation",
            "video_production",
            "social_media_marketing",
            "research_analysis"
        ]
    }
}

OTTO_CAPABILITIES = {
    "content_generation": [
        "Generate images with 20+ AI models (Flux, SDXL, Ideogram, etc.)",
        "Create videos with 15+ models (Kling, Luma, Veo, Sora)",
        "Generate 3D models from text or images",
        "Create music and audio with AI",
        "Write articles, blogs, social posts, ad copy"
    ],
    "ecommerce": [
        "Create products on Printify (100+ product types)",
        "Manage Shopify store (products, orders, discounts)",
        "Auto-sync Printify to Shopify",
        "Generate product mockups and descriptions"
    ],
    "automation": [
        "Schedule recurring tasks with cron expressions",
        "Execute multi-step workflows",
        "Browser automation for web tasks",
        "Email campaigns and social posting"
    ],
    "research": [
        "Web search and browsing",
        "Competitive analysis",
        "Trend research",
        "Data analysis and visualization"
    ],
    "code": [
        "Execute Python code safely",
        "Run shell commands",
        "Analyze and edit files",
        "Generate code solutions"
    ]
}


class CodebaseAwareness(ToolBase):
    """Otto's self-awareness and codebase knowledge."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or Path(__file__).parent.parent.parent)
        self.src_root = self.project_root / "src"
    
    @tool(
        name="otto_get_architecture",
        description="Get Otto's architecture overview - understand how Otto works internally",
        category="meta"
    )
    async def get_architecture(self) -> Dict[str, Any]:
        """Get Otto's architecture information."""
        return {
            "architecture": OTTO_ARCHITECTURE,
            "capabilities_summary": OTTO_CAPABILITIES,
            "project_root": str(self.project_root)
        }
    
    @tool(
        name="otto_get_capabilities",
        description="Get a summary of what Otto can do",
        category="meta"
    )
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get Otto's capabilities."""
        return OTTO_CAPABILITIES
    
    @tool(
        name="otto_find_relevant_code",
        description="Find relevant code files for a given task or capability",
        category="meta"
    )
    async def find_relevant_code(self, query: str) -> Dict[str, Any]:
        """
        Find code files relevant to a query.
        
        Args:
            query: What capability or feature to find (e.g., "video generation", "printify", "scheduling")
        """
        query_lower = query.lower()
        relevant_files = []
        
        # Search in tool categories
        for category, info in OTTO_ARCHITECTURE["tool_categories"].items():
            if query_lower in category or any(query_lower in tool.lower() for tool in info.get("tools", [])):
                relevant_files.append({
                    "category": category,
                    "path": info["path"],
                    "purpose": info["purpose"],
                    "tools": info.get("tools", [])
                })
        
        # Search in core components
        for component, info in OTTO_ARCHITECTURE["core_components"].items():
            if query_lower in component or query_lower in info["purpose"].lower():
                relevant_files.append({
                    "component": component,
                    "path": info["path"],
                    "purpose": info["purpose"]
                })
        
        return {
            "query": query,
            "relevant_files": relevant_files,
            "total_found": len(relevant_files)
        }
    
    @tool(
        name="otto_read_source_file",
        description="Read a source file from Otto's codebase",
        category="meta"
    )
    async def read_source_file(
        self, 
        file_path: str,
        start_line: int = 1,
        end_line: int = 100
    ) -> Dict[str, Any]:
        """
        Read a source file from the codebase.
        
        Args:
            file_path: Relative path from project root (e.g., "src/tools/printify.py")
            start_line: Starting line number (1-based)
            end_line: Ending line number
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if not full_path.is_file():
            return {"error": f"Not a file: {file_path}"}
        
        # Security check - only allow reading from project
        try:
            full_path.resolve().relative_to(self.project_root.resolve())
        except ValueError:
            return {"error": "Access denied - path outside project"}
        
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            start_idx = max(0, start_line - 1)
            end_idx = min(total_lines, end_line)
            
            content = ''.join(lines[start_idx:end_idx])
            
            return {
                "file_path": file_path,
                "total_lines": total_lines,
                "lines_read": f"{start_line}-{end_idx}",
                "content": content
            }
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}
    
    @tool(
        name="otto_list_tools",
        description="List all available tools by category",
        category="meta"
    )
    async def list_tools(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List available tools.
        
        Args:
            category: Optional category filter (printify, shopify, replicate, etc.)
        """
        if category:
            category_lower = category.lower()
            if category_lower in OTTO_ARCHITECTURE["tool_categories"]:
                return OTTO_ARCHITECTURE["tool_categories"][category_lower]
            return {"error": f"Unknown category: {category}"}
        
        return OTTO_ARCHITECTURE["tool_categories"]
    
    @tool(
        name="otto_get_database_info",
        description="Get information about Otto's databases",
        category="meta"
    )
    async def get_database_info(self) -> Dict[str, Any]:
        """Get database configuration and structure."""
        return OTTO_ARCHITECTURE["databases"]
    
    @tool(
        name="otto_explain_error",
        description="Get help understanding and fixing an error based on Otto's codebase knowledge",
        category="meta"
    )
    async def explain_error(self, error_message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Explain an error and suggest fixes.
        
        Args:
            error_message: The error message to explain
            context: Additional context about what was being done
        """
        error_lower = error_message.lower()
        
        suggestions = []
        relevant_files = []
        
        # Common error patterns and fixes
        if "print_provider_id" in error_lower or "blueprint_id" in error_lower:
            suggestions.append("Use printify_smart_create_product instead of printify_create_product")
            suggestions.append("Specify product_type as a string (e.g., 'journal', 'phone case') and IDs will be auto-resolved")
            relevant_files.append("src/tools/printify.py")
        
        if "rate limit" in error_lower:
            suggestions.append("Wait and retry - Otto has automatic retry with exponential backoff")
            suggestions.append("Consider using the scheduler to spread out API calls")
        
        if "api key" in error_lower or "unauthorized" in error_lower:
            suggestions.append("Check API keys in settings")
            suggestions.append("Verify the service is properly configured")
            relevant_files.append("src/utils/config.py")
        
        if "replicate" in error_lower:
            suggestions.append("Check Replicate API token")
            suggestions.append("Model may have changed - use replicate_search_models to find alternatives")
            relevant_files.append("src/tools/replicate_universal.py")
        
        return {
            "error": error_message,
            "context": context,
            "suggestions": suggestions,
            "relevant_files": relevant_files,
            "general_advice": "Check Otto's logs at logs/otto.log for detailed error traces"
        }


def get_codebase_awareness() -> CodebaseAwareness:
    """Get the codebase awareness instance."""
    return CodebaseAwareness()
