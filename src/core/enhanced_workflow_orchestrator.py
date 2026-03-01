"""
Enhanced Workflow Orchestrator - Otto Universal
================================================

Master orchestrator implementing the complete workflow from the diagram:

Otto (orchestrator)
  ↓
Task Interpretation
  ↓
Passing (strict validation)
  ↓
Task Delegation
  ↓
Agents Creation
  ↓
┌──────────────┬──────────────┐
│ Specialties  │    Tools     │
│ Skills       │  AI Models   │
│ Features     │  (Integr.)   │
└──────────────┴──────────────┘
  ↓
Task performance + completion
  ↓
Results

This enforces MODALITY → MODEL selection throughout.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from anthropic import Anthropic

# Import our new systems
from .modality_system import (
    get_modality_detector,
    get_modality_mapper,
    Modality,
    ModalityRequirement
)
from .langchain_task_interpreter import (
    get_task_interpreter,
    InterpretedTask,
    TaskComplexity
)
from .crewai_delegation import (
    get_crew_delegator,
    DelegationResult,
    AgentRole
)

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStage:
    """A stage in the workflow execution."""
    stage_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, completed, failed
    output: Any = None
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.now() - self.started_at).total_seconds()


@dataclass
class WorkflowResult:
    """Complete result from workflow execution."""
    success: bool
    final_output: Any
    
    # Workflow stages
    stages: List[WorkflowStage]
    
    # Detected components
    detected_modalities: List[ModalityRequirement]
    interpreted_task: Optional[InterpretedTask]
    modality_model_mapping: Dict[str, str]
    
    # Delegation results
    delegation_result: Optional[DelegationResult]
    
    # Metrics
    total_duration: float
    quality_score: float
    
    # Metadata
    workflow_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "final_output": self.final_output,
            "stages": [
                {
                    "stage": s.stage_name,
                    "status": s.status,
                    "duration": s.duration
                } for s in self.stages
            ],
            "detected_modalities": [m.modality.value for m in self.detected_modalities],
            "modality_model_mapping": self.modality_model_mapping,
            "quality_score": self.quality_score,
            "total_duration": self.total_duration,
            "timestamp": self.timestamp.isoformat()
        }


class EnhancedWorkflowOrchestrator:
    """
    Master orchestrator implementing the complete workflow.
    
    Workflow:
    1. Task Interpretation (LangChain-style)
    2. Modality Detection (MODALITY → MODEL)
    3. Task Parsing & Validation
    4. Task Delegation (CrewAI-style)
    5. Agent Creation & Execution
    6. Result Synthesis
    7. Quality Validation
    
    Key Principle: Modality determines model, not the other way around.
    """
    
    def __init__(
        self,
        anthropic_client: Anthropic,
        tool_registry: Any,
        config: Optional[Dict[str, Any]] = None
    ):
        self.anthropic = anthropic_client
        self.tool_registry = tool_registry
        self.config = config or {}
        
        # Initialize subsystems
        self.modality_detector = get_modality_detector(anthropic_client)
        self.modality_mapper = get_modality_mapper(config)
        self.task_interpreter = get_task_interpreter(anthropic_client)
        self.crew_delegator = get_crew_delegator(anthropic_client, tool_registry, config)
        
        # Execution tracking
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.workflow_history: List[WorkflowResult] = []
        
        logger.info("Enhanced Workflow Orchestrator initialized")
        logger.info("  → Modality-first selection: ENABLED")
        logger.info("  → LangChain interpretation: ENABLED")
        logger.info("  → CrewAI delegation: ENABLED")
    
    async def execute_workflow(
        self,
        user_request: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None
    ) -> WorkflowResult:
        """
        Execute complete workflow from user request to final result.
        
        Args:
            user_request: Raw user input
            session_id: Optional session identifier
            context: Additional context (user prefs, history, etc.)
            callback: Optional callback for streaming updates
            
        Returns:
            WorkflowResult with complete execution details
        """
        import uuid
        
        workflow_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        stages: List[WorkflowStage] = []
        context = context or {}
        
        logger.info(f"[{workflow_id}] Starting workflow: {user_request[:100]}...")
        
        if callback:
            await callback({
                "type": "workflow_started",
                "workflow_id": workflow_id,
                "request": user_request
            })
        
        try:
            # ================================================================
            # STAGE 1: Task Interpretation (LangChain)
            # ================================================================
            stage = WorkflowStage("task_interpretation", datetime.now())
            stages.append(stage)
            
            logger.info(f"[{workflow_id}] Stage 1: Task Interpretation")
            if callback:
                await callback({"type": "stage_started", "stage": "task_interpretation"})
            
            interpreted_task = await self.task_interpreter.interpret_task(
                user_request, context
            )
            
            stage.completed_at = datetime.now()
            stage.status = "completed"
            stage.output = interpreted_task
            
            logger.info(f"[{workflow_id}] Task interpreted: {interpreted_task.task_type.value}")
            if callback:
                await callback({
                    "type": "stage_completed",
                    "stage": "task_interpretation",
                    "task_type": interpreted_task.task_type.value,
                    "complexity": interpreted_task.complexity.value
                })
            
            # ================================================================
            # STAGE 2: Modality Detection (MODALITY → MODEL)
            # ================================================================
            stage = WorkflowStage("modality_detection", datetime.now())
            stages.append(stage)
            
            logger.info(f"[{workflow_id}] Stage 2: Modality Detection")
            if callback:
                await callback({"type": "stage_started", "stage": "modality_detection"})
            
            detected_modalities = await self.modality_detector.detect_modalities(
                user_request, context
            )
            
            stage.completed_at = datetime.now()
            stage.status = "completed"
            stage.output = detected_modalities
            
            logger.info(f"[{workflow_id}] Modalities detected: "
                       f"{[m.modality.value for m in detected_modalities]}")
            if callback:
                await callback({
                    "type": "stage_completed",
                    "stage": "modality_detection",
                    "modalities": [m.modality.value for m in detected_modalities]
                })
            
            # ================================================================
            # STAGE 3: Model Selection (MODALITY → MODEL mapping)
            # ================================================================
            stage = WorkflowStage("model_selection", datetime.now())
            stages.append(stage)
            
            logger.info(f"[{workflow_id}] Stage 3: Model Selection (Modality → Model)")
            if callback:
                await callback({"type": "stage_started", "stage": "model_selection"})
            
            modality_model_mapping = self.modality_mapper.select_models_for_requirements(
                detected_modalities, context, user_request
            )
            
            stage.completed_at = datetime.now()
            stage.status = "completed"
            stage.output = modality_model_mapping
            
            logger.info(f"[{workflow_id}] Model mapping:")
            for modality, model in modality_model_mapping.items():
                logger.info(f"  {modality.value} → {model}")
            
            if callback:
                await callback({
                    "type": "stage_completed",
                    "stage": "model_selection",
                    "mapping": {k.value: v for k, v in modality_model_mapping.items()}
                })
            
            # ================================================================
            # STAGE 4: Task Validation & Parsing
            # ================================================================
            stage = WorkflowStage("task_validation", datetime.now())
            stages.append(stage)
            
            logger.info(f"[{workflow_id}] Stage 4: Task Validation")
            if callback:
                await callback({"type": "stage_started", "stage": "task_validation"})
            
            validation_result = await self._validate_task_execution_plan(
                interpreted_task,
                detected_modalities,
                modality_model_mapping
            )
            
            stage.completed_at = datetime.now()
            stage.status = "completed" if validation_result["valid"] else "failed"
            stage.output = validation_result
            
            if not validation_result["valid"]:
                logger.error(f"[{workflow_id}] Task validation failed: "
                           f"{validation_result.get('issues')}")
                
                return WorkflowResult(
                    success=False,
                    final_output={"error": "Task validation failed", 
                                 "issues": validation_result.get("issues")},
                    stages=stages,
                    detected_modalities=detected_modalities,
                    interpreted_task=interpreted_task,
                    modality_model_mapping={k.value: v for k, v in modality_model_mapping.items()},
                    delegation_result=None,
                    total_duration=(datetime.now() - start_time).total_seconds(),
                    quality_score=0.0,
                    workflow_id=workflow_id
                )
            
            logger.info(f"[{workflow_id}] Task validated successfully")
            if callback:
                await callback({
                    "type": "stage_completed",
                    "stage": "task_validation",
                    "valid": True
                })
            
            # ================================================================
            # STAGE 5: Task Delegation (CrewAI-style)
            # ================================================================
            stage = WorkflowStage("task_delegation", datetime.now())
            stages.append(stage)
            
            logger.info(f"[{workflow_id}] Stage 5: Task Delegation")
            if callback:
                await callback({"type": "stage_started", "stage": "task_delegation"})
            
            delegation_result = await self.crew_delegator.delegate_task(
                interpreted_task,
                {k.value: v for k, v in modality_model_mapping.items()},
                callback
            )
            
            stage.completed_at = datetime.now()
            stage.status = "completed" if delegation_result.success else "failed"
            stage.output = delegation_result
            
            if not delegation_result.success:
                logger.error(f"[{workflow_id}] Task delegation failed")
                
                return WorkflowResult(
                    success=False,
                    final_output={"error": "Task execution failed"},
                    stages=stages,
                    detected_modalities=detected_modalities,
                    interpreted_task=interpreted_task,
                    modality_model_mapping={k.value: v for k, v in modality_model_mapping.items()},
                    delegation_result=delegation_result,
                    total_duration=(datetime.now() - start_time).total_seconds(),
                    quality_score=delegation_result.quality_score,
                    workflow_id=workflow_id
                )
            
            logger.info(f"[{workflow_id}] Task delegation completed, quality: "
                       f"{delegation_result.quality_score:.2f}")
            if callback:
                await callback({
                    "type": "stage_completed",
                    "stage": "task_delegation",
                    "quality_score": delegation_result.quality_score
                })
            
            # ================================================================
            # STAGE 6: Result Finalization
            # ================================================================
            stage = WorkflowStage("result_finalization", datetime.now())
            stages.append(stage)
            
            final_output = delegation_result.final_output
            
            stage.completed_at = datetime.now()
            stage.status = "completed"
            stage.output = final_output
            
            # ================================================================
            # Complete Workflow
            # ================================================================
            total_duration = (datetime.now() - start_time).total_seconds()
            
            workflow_result = WorkflowResult(
                success=True,
                final_output=final_output,
                stages=stages,
                detected_modalities=detected_modalities,
                interpreted_task=interpreted_task,
                modality_model_mapping={k.value: v for k, v in modality_model_mapping.items()},
                delegation_result=delegation_result,
                total_duration=total_duration,
                quality_score=delegation_result.quality_score,
                workflow_id=workflow_id
            )
            
            # Track workflow
            self.workflow_history.append(workflow_result)
            if len(self.workflow_history) > 1000:
                self.workflow_history = self.workflow_history[-1000:]
            
            logger.info(f"[{workflow_id}] Workflow completed successfully in {total_duration:.1f}s")
            logger.info(f"[{workflow_id}] Quality score: {delegation_result.quality_score:.2f}")
            
            if callback:
                await callback({
                    "type": "workflow_completed",
                    "workflow_id": workflow_id,
                    "success": True,
                    "duration": total_duration,
                    "quality_score": delegation_result.quality_score
                })
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"[{workflow_id}] Workflow failed: {e}", exc_info=True)
            
            # Mark current stage as failed
            if stages and stages[-1].status == "in_progress":
                stages[-1].status = "failed"
                stages[-1].error = str(e)
                stages[-1].completed_at = datetime.now()
            
            workflow_result = WorkflowResult(
                success=False,
                final_output={"error": str(e)},
                stages=stages,
                detected_modalities=[],
                interpreted_task=None,
                modality_model_mapping={},
                delegation_result=None,
                total_duration=(datetime.now() - start_time).total_seconds(),
                quality_score=0.0,
                workflow_id=workflow_id
            )
            
            if callback:
                await callback({
                    "type": "workflow_failed",
                    "workflow_id": workflow_id,
                    "error": str(e)
                })
            
            return workflow_result
    
    async def _validate_task_execution_plan(
        self,
        task: InterpretedTask,
        modalities: List[ModalityRequirement],
        model_mapping: Dict[Modality, str]
    ) -> Dict[str, Any]:
        """
        Validate that the execution plan is complete and correct.
        
        Ensures MODALITY → MODEL enforcement is working.
        """
        issues = []
        
        # Check modalities are recognized
        if not modalities:
            issues.append("No modalities detected")
        
        # Check modalities have model mappings
        for req in modalities:
            if req.modality not in model_mapping:
                issues.append(f"No model mapped for modality: {req.modality.value}")
        
        # Check task has steps
        if not task.steps:
            issues.append("No execution steps defined")
        
        # Check success criteria exist
        if not task.success_criteria:
            issues.append("No success criteria defined")
        
        valid = len(issues) == 0
        
        return {
            "valid": valid,
            "issues": issues,
            "confidence": 0.9 if valid else 0.3
        }
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get statistics about workflow execution."""
        if not self.workflow_history:
            return {"total_workflows": 0}
        
        successful = [w for w in self.workflow_history if w.success]
        
        avg_duration = sum(w.total_duration for w in self.workflow_history) / len(self.workflow_history)
        avg_quality = sum(w.quality_score for w in successful) / len(successful) if successful else 0
        
        # Count modalities used
        modality_usage = {}
        for workflow in self.workflow_history:
            for modality in workflow.detected_modalities:
                mod_name = modality.modality.value
                modality_usage[mod_name] = modality_usage.get(mod_name, 0) + 1
        
        return {
            "total_workflows": len(self.workflow_history),
            "successful": len(successful),
            "success_rate": len(successful) / len(self.workflow_history),
            "avg_duration": avg_duration,
            "avg_quality_score": avg_quality,
            "modality_usage": modality_usage
        }


# =============================================================================
# Singleton Access
# =============================================================================

_orchestrator: Optional[EnhancedWorkflowOrchestrator] = None


def get_enhanced_orchestrator(
    anthropic_client: Anthropic,
    tool_registry: Any,
    config: Optional[Dict[str, Any]] = None
) -> EnhancedWorkflowOrchestrator:
    """Get or create the enhanced workflow orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancedWorkflowOrchestrator(
            anthropic_client,
            tool_registry,
            config
        )
    return _orchestrator


def reset_enhanced_orchestrator():
    """Reset the orchestrator (for testing)."""
    global _orchestrator
    _orchestrator = None
