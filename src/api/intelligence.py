"""
Intelligence API Router
=======================

Exposes enhanced reasoning, verification, and tool composition capabilities.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ReasoningStrategyEnum(str, Enum):
    direct = "direct"
    chain_of_thought = "chain_of_thought"
    decomposition = "decomposition"
    adversarial = "adversarial"
    consensus = "consensus"


class ReasonRequest(BaseModel):
    """Request for enhanced reasoning."""
    query: str = Field(..., description="The problem or question to solve")
    context: Optional[str] = Field(None, description="Additional context")
    strategy: Optional[ReasoningStrategyEnum] = Field(None, description="Force a specific strategy")
    include_steps: bool = Field(False, description="Include detailed reasoning steps")


class ReasonResponse(BaseModel):
    """Response from enhanced reasoning."""
    success: bool
    answer: str
    confidence: float
    strategy_used: str
    problem_type: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    alternatives: Optional[List[str]] = None
    duration_ms: float


class VerifyRequest(BaseModel):
    """Request for result verification."""
    result: Any = Field(..., description="The result to verify")
    task_description: str = Field(..., description="Description of what was being done")
    expected_type: Optional[str] = Field(None, description="Expected output type")
    level: Optional[str] = Field("standard", description="Verification level: quick, standard, thorough, critical")


class VerifyResponse(BaseModel):
    """Response from verification."""
    success: bool
    result: str  # passed, failed, needs_improvement
    confidence: float
    checks_passed: List[str]
    checks_failed: List[str]
    suggestions: List[str]
    improved_result: Optional[Any] = None


class ChainPlanRequest(BaseModel):
    """Request to plan a tool chain."""
    goal: str = Field(..., description="What to accomplish")
    context: Optional[Dict[str, Any]] = Field(None, description="Context data")
    available_tools: Optional[List[str]] = Field(None, description="Limit to specific tools")


class ChainExecuteRequest(BaseModel):
    """Request to execute a tool chain."""
    chain_id: str = Field(..., description="Chain ID from planning")


class PluginActionRequest(BaseModel):
    """Request for plugin actions."""
    plugin_id: str = Field(..., description="Plugin identifier")
    action: str = Field(..., description="Action: enable, disable, configure")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration data")


# ============================================================================
# Enhanced Reasoning Endpoints
# ============================================================================

@router.post("/reason", response_model=ReasonResponse)
async def enhanced_reason(request: ReasonRequest):
    """
    Apply enhanced multi-strategy reasoning to solve a problem.
    
    The system will:
    1. Detect the problem type
    2. Select the optimal reasoning strategy
    3. Execute with chain-of-thought when needed
    4. Self-critique and refine if confidence is low
    """
    try:
        from ..core.enhanced_reasoning import get_reasoner, ReasoningStrategy
        
        reasoner = get_reasoner()
        
        # Map strategy enum
        strategy = None
        if request.strategy:
            strategy = ReasoningStrategy[request.strategy.upper()]
        
        result = await reasoner.reason(
            query=request.query,
            context=request.context,
            strategy=strategy,
            require_steps=request.include_steps
        )
        
        steps = None
        if request.include_steps and result.steps:
            steps = [
                {
                    "step": s.step_number,
                    "thought": s.thought,
                    "observation": s.observation,
                    "confidence": s.confidence
                }
                for s in result.steps
            ]
        
        return ReasonResponse(
            success=True,
            answer=result.answer,
            confidence=result.confidence,
            strategy_used=result.strategy_used.value,
            problem_type=result.problem_type.value if result.problem_type else None,
            steps=steps,
            alternatives=result.alternatives if result.alternatives else None,
            duration_ms=result.duration_ms
        )
        
    except Exception as e:
        logger.error(f"Reasoning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Result Verification Endpoints
# ============================================================================

@router.post("/verify", response_model=VerifyResponse)
async def verify_result(request: VerifyRequest):
    """
    Verify a result against expectations.
    
    Performs multi-stage verification including:
    - Type validation
    - Quality checks
    - AI-powered evaluation
    - Automatic improvement suggestions
    """
    try:
        from ..core.result_verifier import get_verifier, VerificationLevel
        
        verifier = get_verifier()
        
        # Map level
        level_map = {
            "quick": VerificationLevel.QUICK,
            "standard": VerificationLevel.STANDARD,
            "thorough": VerificationLevel.THOROUGH,
            "critical": VerificationLevel.CRITICAL
        }
        level = level_map.get(request.level or "standard", VerificationLevel.STANDARD)
        
        report = await verifier.verify(
            result=request.result,
            task_description=request.task_description,
            expected_type=request.expected_type,
            level=level
        )
        
        return VerifyResponse(
            success=True,
            result=report.result.value,
            confidence=report.confidence,
            checks_passed=report.checks_passed,
            checks_failed=report.checks_failed,
            suggestions=report.suggestions,
            improved_result=report.improved_result
        )
        
    except Exception as e:
        logger.error(f"Verification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Tool Composition Endpoints
# ============================================================================

@router.post("/chain/plan")
async def plan_tool_chain(request: ChainPlanRequest):
    """
    Plan a tool chain to accomplish a goal.
    
    Uses AI to determine the optimal sequence of tools
    and their parameters.
    """
    try:
        from ..core.tool_composer import get_composer
        
        composer = get_composer()
        chain = await composer.plan_chain(
            goal=request.goal,
            available_tools=request.available_tools,
            context=request.context
        )
        
        return {
            "success": True,
            "chain_id": chain.chain_id,
            "description": chain.description,
            "steps": [
                {
                    "tool_id": node.tool_id,
                    "tool_name": node.tool_name,
                    "parameters": node.parameters,
                    "depends_on": node.depends_on
                }
                for node in chain.nodes
            ]
        }
        
    except Exception as e:
        logger.error(f"Chain planning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chain/execute")
async def execute_tool_chain(request: ChainExecuteRequest):
    """
    Execute a planned tool chain.
    """
    try:
        from ..core.tool_composer import get_composer
        
        composer = get_composer()
        chain = composer.get_chain(request.chain_id)
        
        if not chain:
            raise HTTPException(status_code=404, detail=f"Chain '{request.chain_id}' not found")
        
        result = await composer.execute_chain(chain)
        
        return {
            "success": True,
            "chain_id": result.chain_id,
            "status": result.status.value,
            "progress": result.progress,
            "final_result": result.final_result,
            "steps": [
                {
                    "tool_id": node.tool_id,
                    "status": node.status.value,
                    "result": node.result,
                    "error": node.error,
                    "duration_ms": node.duration_ms
                }
                for node in result.nodes
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chain execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chain/{chain_id}")
async def get_chain_status(chain_id: str):
    """Get status of a tool chain."""
    try:
        from ..core.tool_composer import get_composer
        
        composer = get_composer()
        chain = composer.get_chain(chain_id)
        
        if not chain:
            raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not found")
        
        return {
            "success": True,
            "chain_id": chain.chain_id,
            "status": chain.status.value,
            "progress": chain.progress,
            "description": chain.description
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chain status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Plugin System Endpoints
# ============================================================================

@router.get("/plugins")
async def list_plugins():
    """List all available plugins."""
    try:
        from ..core.plugin_system import get_plugin_manager
        
        manager = get_plugin_manager()
        plugins = manager.get_plugins()
        
        return {
            "success": True,
            "plugins": [
                {
                    "id": p.id,
                    "name": p.metadata.name,
                    "version": p.metadata.version,
                    "description": p.metadata.description,
                    "type": p.metadata.plugin_type.value,
                    "status": p.status.value,
                    "author": p.metadata.author,
                    "provides_tools": p.metadata.provides_tools,
                    "tags": p.metadata.tags
                }
                for p in plugins
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing plugins: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/action")
async def plugin_action(request: PluginActionRequest):
    """Enable, disable, or configure a plugin."""
    try:
        from ..core.plugin_system import get_plugin_manager
        
        manager = get_plugin_manager()
        
        if request.action == "enable":
            success = await manager.load_plugin(request.plugin_id)
            return {"success": success, "message": f"Plugin '{request.plugin_id}' enabled"}
            
        elif request.action == "disable":
            success = await manager.unload_plugin(request.plugin_id)
            return {"success": success, "message": f"Plugin '{request.plugin_id}' disabled"}
            
        elif request.action == "configure":
            # TODO: Implement plugin configuration
            return {"success": True, "message": "Configuration updated"}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plugin action error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/create")
async def create_plugin(name: str, description: str, plugin_type: str = "tool"):
    """Create a new plugin scaffold."""
    try:
        from ..core.plugin_system import get_plugin_manager, PluginType
        
        manager = get_plugin_manager()
        
        type_map = {
            "tool": PluginType.TOOL,
            "integration": PluginType.INTEGRATION,
            "workflow": PluginType.WORKFLOW
        }
        ptype = type_map.get(plugin_type, PluginType.TOOL)
        
        path = await manager.create_plugin(name, description, ptype)
        
        return {
            "success": True,
            "message": f"Plugin scaffold created at {path}",
            "path": str(path)
        }
        
    except Exception as e:
        logger.error(f"Plugin creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plugins/tools")
async def list_plugin_tools():
    """List all tools from active plugins."""
    try:
        from ..core.plugin_system import get_plugin_manager
        
        manager = get_plugin_manager()
        tools = manager.get_all_tools()
        
        return {
            "success": True,
            "tools": [
                {
                    "name": name,
                    "plugin": info.get("plugin"),
                    "description": info.get("description", ""),
                    "category": info.get("category", "plugin")
                }
                for name, info in tools.items()
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing plugin tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Intelligence Stats
# ============================================================================

@router.get("/stats")
async def get_intelligence_stats():
    """Get statistics about the intelligence systems."""
    try:
        stats = {
            "reasoning": {
                "strategies_available": [
                    "direct", "chain_of_thought", "decomposition", 
                    "adversarial", "consensus"
                ],
                "problem_types": [
                    "factual", "analytical", "creative", 
                    "procedural", "debugging", "optimization"
                ]
            },
            "verification": {
                "levels": ["quick", "standard", "thorough", "critical"],
                "auto_improvement": True
            },
            "composition": {
                "templates": ["research_and_summarize", "generate_and_refine", "image_pipeline"]
            }
        }
        
        # Add plugin info if available
        try:
            from ..core.plugin_system import get_plugin_manager
            manager = get_plugin_manager()
            active = manager.get_active_plugins()
            stats["plugins"] = {
                "active_count": len(active),
                "tools_count": len(manager.get_all_tools())
            }
        except:
            stats["plugins"] = {"active_count": 0, "tools_count": 0}
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
