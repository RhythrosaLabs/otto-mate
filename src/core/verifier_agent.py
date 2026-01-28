"""
Verifier Agent - Result Validation and Self-Correction
=======================================================

The Verifier Agent ensures quality and correctness of execution results.
This is a critical component of the agent loop: Plan → Execute → Verify

Key Responsibilities:
- Validate tool execution results against success criteria
- Detect errors, inconsistencies, or incomplete outputs
- Suggest corrections and improvements
- Calculate confidence scores
- Trigger re-execution when needed

Best Practices from Anthropic Agent SDK:
- Always verify before finalizing
- Check against original goals
- Validate data integrity
- Ensure business rules are met
"""

import logging
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of verification check."""
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_CORRECTION = "needs_correction"
    INCOMPLETE = "incomplete"
    REQUIRES_RETRY = "requires_retry"


@dataclass
class VerificationResult:
    """Result of a verification check."""
    status: VerificationStatus
    confidence: float  # 0.0 to 1.0
    issues: List[str]
    corrections: List[Dict[str, Any]]
    reasoning: str
    passed_checks: List[str]
    failed_checks: List[str]


class VerifierAgent:
    """
    Agent responsible for verifying execution results and ensuring quality.
    
    This agent runs after execution to check if:
    1. The task was completed successfully
    2. All success criteria are met
    3. Results are valid and usable
    4. No errors or inconsistencies exist
    5. Business rules and constraints are satisfied
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        self.verification_history = []
    
    async def verify_execution(
        self,
        task_description: str,
        success_criteria: List[str],
        execution_results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        Verify execution results against success criteria.
        
        Args:
            task_description: What the task was supposed to do
            success_criteria: List of criteria that must be met
            execution_results: Results from the execution agent
            context: Additional context for verification
            
        Returns:
            VerificationResult with status and details
        """
        logger.info(f"Verifying execution: {task_description[:100]}")
        
        # Build verification prompt
        prompt = self._build_verification_prompt(
            task_description,
            success_criteria,
            execution_results,
            context
        )
        
        # Get Claude's verification analysis
        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent verification
                system="""You are a meticulous verification agent. Your job is to:
1. Check if execution results meet all success criteria
2. Identify any errors, inconsistencies, or incomplete work
3. Suggest specific corrections if needed
4. Rate confidence in the results (0.0-1.0)
5. Decide if retry or correction is needed

Be thorough but fair. Provide actionable feedback.""",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse verification response
            verification = self._parse_verification_response(response.content[0].text)
            
            # Store in history
            self.verification_history.append({
                "task": task_description,
                "result": verification,
                "timestamp": str(datetime.now())
            })
            
            logger.info(f"Verification complete: {verification.status.value}")
            return verification
            
        except Exception as e:
            logger.error(f"Verification failed: {e}", exc_info=True)
            # Default to cautious verification on error
            return VerificationResult(
                status=VerificationStatus.REQUIRES_RETRY,
                confidence=0.0,
                issues=[f"Verification error: {str(e)}"],
                corrections=[],
                reasoning="Unable to verify due to error",
                passed_checks=[],
                failed_checks=["verification_process"]
            )
    
    async def verify_batch(
        self,
        tasks: List[Dict[str, Any]],
        results: List[Dict[str, Any]]
    ) -> List[VerificationResult]:
        """
        Verify multiple execution results at once.
        
        Useful for workflow verification where multiple steps need checking.
        """
        verifications = []
        
        for task, result in zip(tasks, results):
            verification = await self.verify_execution(
                task_description=task.get("description", ""),
                success_criteria=task.get("success_criteria", []),
                execution_results=result,
                context=task.get("context")
            )
            verifications.append(verification)
        
        return verifications
    
    def _build_verification_prompt(
        self,
        task: str,
        criteria: List[str],
        results: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build detailed verification prompt for Claude."""
        
        criteria_text = "\n".join([f"- {c}" for c in criteria]) if criteria else "- Task completed successfully"
        
        # Safely format results for prompt
        results_text = json.dumps(results, indent=2, default=str)[:2000]
        context_text = json.dumps(context, indent=2, default=str)[:1000] if context else "No additional context"
        
        return f"""Verify the following task execution:

TASK: {task}

SUCCESS CRITERIA:
{criteria_text}

EXECUTION RESULTS:
{results_text}

CONTEXT:
{context_text}

Please verify if:
1. All success criteria are met
2. Results are valid and complete
3. No errors or inconsistencies exist
4. Data is properly formatted
5. Business rules are satisfied

Respond in JSON format:
{{
    "status": "passed|failed|needs_correction|incomplete|requires_retry",
    "confidence": 0.95,
    "passed_checks": ["criterion 1", "criterion 2"],
    "failed_checks": ["criterion 3"],
    "issues": ["issue 1", "issue 2"],
    "corrections": [
        {{
            "issue": "description",
            "fix": "what needs to be done",
            "priority": "high|medium|low"
        }}
    ],
    "reasoning": "Your detailed analysis of why you reached this conclusion"
}}"""
    
    def _parse_verification_response(self, response_text: str) -> VerificationResult:
        """Parse Claude's verification response into structured result."""
        
        import re
        from datetime import datetime
        
        try:
            # Extract JSON from response
            match = re.search(r'\{[\s\S]*\}', response_text)
            if not match:
                raise ValueError("No JSON found in response")
            
            data = json.loads(match.group())
            
            # Map string status to enum
            status_map = {
                "passed": VerificationStatus.PASSED,
                "failed": VerificationStatus.FAILED,
                "needs_correction": VerificationStatus.NEEDS_CORRECTION,
                "incomplete": VerificationStatus.INCOMPLETE,
                "requires_retry": VerificationStatus.REQUIRES_RETRY
            }
            
            status = status_map.get(
                data.get("status", "failed").lower(),
                VerificationStatus.FAILED
            )
            
            return VerificationResult(
                status=status,
                confidence=float(data.get("confidence", 0.5)),
                issues=data.get("issues", []),
                corrections=data.get("corrections", []),
                reasoning=data.get("reasoning", ""),
                passed_checks=data.get("passed_checks", []),
                failed_checks=data.get("failed_checks", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse verification response: {e}")
            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=0.0,
                issues=[f"Parse error: {str(e)}"],
                corrections=[],
                reasoning="Failed to parse verification",
                passed_checks=[],
                failed_checks=["parsing"]
            )
    
    async def apply_corrections(
        self,
        original_task: str,
        execution_results: Dict[str, Any],
        corrections: List[Dict[str, Any]],
        tool_registry: Any
    ) -> Dict[str, Any]:
        """
        Apply suggested corrections to fix issues.
        
        This can re-execute tools with corrected parameters or
        apply post-processing fixes.
        """
        logger.info(f"Applying {len(corrections)} corrections")
        
        corrected_results = dict(execution_results)
        
        for correction in corrections:
            if correction.get("priority") == "high":
                logger.info(f"Applying correction: {correction.get('issue')}")
                # Correction logic would go here
                # This could involve re-running tools with fixed parameters
        
        return corrected_results
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get summary of all verifications performed."""
        
        if not self.verification_history:
            return {"total": 0}
        
        total = len(self.verification_history)
        passed = sum(1 for v in self.verification_history 
                    if v["result"].status == VerificationStatus.PASSED)
        
        avg_confidence = sum(v["result"].confidence for v in self.verification_history) / total
        
        return {
            "total_verifications": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "average_confidence": avg_confidence,
            "common_issues": self._get_common_issues()
        }
    
    def _get_common_issues(self) -> List[str]:
        """Extract most common issues from history."""
        
        from collections import Counter
        
        all_issues = []
        for v in self.verification_history:
            all_issues.extend(v["result"].issues)
        
        if not all_issues:
            return []
        
        common = Counter(all_issues).most_common(5)
        return [issue for issue, count in common]
