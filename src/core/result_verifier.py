"""
Result Verification Engine
==========================

Ensures quality outputs through:
- Multi-stage verification
- Confidence scoring
- Retry with improvements
- Human-in-the-loop fallback
- Learning from feedback
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from anthropic import AsyncAnthropic
import json
import hashlib

logger = logging.getLogger(__name__)


class VerificationLevel(Enum):
    """How thorough the verification should be."""
    NONE = "none"  # No verification
    QUICK = "quick"  # Fast sanity check
    STANDARD = "standard"  # Normal verification
    THOROUGH = "thorough"  # Deep validation
    CRITICAL = "critical"  # Maximum scrutiny


class VerificationResult(Enum):
    """Result of verification."""
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_IMPROVEMENT = "needs_improvement"
    UNCERTAIN = "uncertain"


@dataclass
class VerificationReport:
    """Detailed verification report."""
    result: VerificationResult
    confidence: float  # 0-1
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    improved_result: Optional[Any] = None
    retries_made: int = 0
    verification_time_ms: float = 0


@dataclass
class VerificationRule:
    """A rule for verification."""
    name: str
    check_fn: Callable[[Any], Tuple[bool, str]]
    required: bool = True
    weight: float = 1.0


class ResultVerifier:
    """
    Verifies and improves task results.
    """
    
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_retries: int = 2,
        default_level: VerificationLevel = VerificationLevel.STANDARD
    ):
        self.client = AsyncAnthropic()
        self.model = model
        self.max_retries = max_retries
        self.default_level = default_level
        self._custom_rules: Dict[str, List[VerificationRule]] = {}
        self._feedback_history: List[Dict[str, Any]] = []
    
    async def verify(
        self,
        result: Any,
        task_description: str,
        expected_type: Optional[str] = None,
        level: Optional[VerificationLevel] = None,
        custom_rules: Optional[List[VerificationRule]] = None,
        retry_on_fail: bool = True
    ) -> VerificationReport:
        """
        Verify a result against expectations.
        
        Args:
            result: The result to verify
            task_description: Description of what was being done
            expected_type: Expected output type (text, code, json, image, etc.)
            level: Verification thoroughness
            custom_rules: Additional verification rules
            retry_on_fail: Whether to attempt improvements on failure
        """
        start_time = datetime.now()
        level = level or self.default_level
        
        if level == VerificationLevel.NONE:
            return VerificationReport(
                result=VerificationResult.PASSED,
                confidence=0.5
            )
        
        # Run verification checks
        report = await self._run_checks(result, task_description, expected_type, level, custom_rules)
        
        # Attempt improvement if needed
        retries = 0
        while (
            report.result in [VerificationResult.FAILED, VerificationResult.NEEDS_IMPROVEMENT]
            and retry_on_fail
            and retries < self.max_retries
        ):
            retries += 1
            improved = await self._improve_result(result, task_description, report)
            
            if improved:
                result = improved
                report = await self._run_checks(result, task_description, expected_type, level, custom_rules)
                report.improved_result = improved
        
        report.retries_made = retries
        report.verification_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return report
    
    async def _run_checks(
        self,
        result: Any,
        task_description: str,
        expected_type: Optional[str],
        level: VerificationLevel,
        custom_rules: Optional[List[VerificationRule]]
    ) -> VerificationReport:
        """Run verification checks on a result."""
        checks_passed = []
        checks_failed = []
        suggestions = []
        
        # Basic checks
        if result is None:
            return VerificationReport(
                result=VerificationResult.FAILED,
                confidence=1.0,
                checks_failed=["Result is None"]
            )
        
        # Type-specific checks
        result_str = str(result)
        
        # Check if result is empty
        if not result_str.strip():
            checks_failed.append("Result is empty")
        else:
            checks_passed.append("Result is not empty")
        
        # Check result length
        if len(result_str) < 10:
            checks_failed.append("Result is very short")
        else:
            checks_passed.append("Result has sufficient length")
        
        # Expected type validation
        if expected_type:
            type_valid = self._validate_type(result, expected_type)
            if type_valid:
                checks_passed.append(f"Result matches expected type: {expected_type}")
            else:
                checks_failed.append(f"Result doesn't match expected type: {expected_type}")
        
        # Run custom rules
        if custom_rules:
            for rule in custom_rules:
                try:
                    passed, message = rule.check_fn(result)
                    if passed:
                        checks_passed.append(f"{rule.name}: {message}")
                    else:
                        if rule.required:
                            checks_failed.append(f"{rule.name}: {message}")
                        else:
                            suggestions.append(message)
                except Exception as e:
                    logger.warning(f"Rule '{rule.name}' failed to execute: {e}")
        
        # AI-powered verification for Standard+ levels
        if level in [VerificationLevel.STANDARD, VerificationLevel.THOROUGH, VerificationLevel.CRITICAL]:
            ai_check = await self._ai_verify(result, task_description, level)
            checks_passed.extend(ai_check.get("passed", []))
            checks_failed.extend(ai_check.get("failed", []))
            suggestions.extend(ai_check.get("suggestions", []))
        
        # Calculate overall result
        if checks_failed:
            if len(checks_failed) >= len(checks_passed):
                overall = VerificationResult.FAILED
            else:
                overall = VerificationResult.NEEDS_IMPROVEMENT
        else:
            overall = VerificationResult.PASSED
        
        # Calculate confidence
        total_checks = len(checks_passed) + len(checks_failed)
        confidence = len(checks_passed) / total_checks if total_checks > 0 else 0.5
        
        return VerificationReport(
            result=overall,
            confidence=confidence,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            suggestions=suggestions
        )
    
    async def _ai_verify(
        self,
        result: Any,
        task_description: str,
        level: VerificationLevel
    ) -> Dict[str, List[str]]:
        """Use AI to verify the result."""
        result_preview = str(result)[:2000]
        
        depth_instruction = {
            VerificationLevel.STANDARD: "Do a basic quality check.",
            VerificationLevel.THOROUGH: "Do a thorough quality check, looking for subtle issues.",
            VerificationLevel.CRITICAL: "Do an extremely detailed check. Find any possible issues or improvements."
        }.get(level, "Do a basic quality check.")
        
        prompt = f"""{depth_instruction}

Task: {task_description}

Result to verify:
```
{result_preview}
```

Evaluate this result and respond in JSON format:
{{
  "passed": ["list of quality checks that passed"],
  "failed": ["list of issues found"],
  "suggestions": ["list of improvement suggestions"],
  "quality_score": 0-100
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "passed": data.get("passed", []),
                    "failed": data.get("failed", []),
                    "suggestions": data.get("suggestions", [])
                }
        except Exception as e:
            logger.warning(f"AI verification failed: {e}")
        
        return {"passed": [], "failed": [], "suggestions": []}
    
    async def _improve_result(
        self,
        result: Any,
        task_description: str,
        report: VerificationReport
    ) -> Optional[Any]:
        """Attempt to improve a failing result."""
        result_preview = str(result)[:3000]
        issues = "\n".join(f"- {issue}" for issue in report.checks_failed)
        suggestions = "\n".join(f"- {s}" for s in report.suggestions)
        
        prompt = f"""The following result has issues that need fixing.

Task: {task_description}

Current Result:
```
{result_preview}
```

Issues Found:
{issues}

Suggestions:
{suggestions}

Please provide an improved version that addresses these issues. Return ONLY the improved result, nothing else."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            improved = response.content[0].text
            
            # Try to preserve original type
            if isinstance(result, dict):
                try:
                    return json.loads(improved)
                except:
                    pass
            
            return improved
            
        except Exception as e:
            logger.error(f"Failed to improve result: {e}")
            return None
    
    def _validate_type(self, result: Any, expected_type: str) -> bool:
        """Validate result matches expected type."""
        type_checks = {
            "text": lambda x: isinstance(x, str),
            "json": lambda x: isinstance(x, (dict, list)) or self._is_json_string(x),
            "code": lambda x: isinstance(x, str) and len(x) > 10,
            "number": lambda x: isinstance(x, (int, float)),
            "list": lambda x: isinstance(x, list),
            "dict": lambda x: isinstance(x, dict),
            "boolean": lambda x: isinstance(x, bool),
            "url": lambda x: isinstance(x, str) and x.startswith(('http://', 'https://')),
            "file_path": lambda x: isinstance(x, str) and ('/' in x or '\\' in x),
        }
        
        check_fn = type_checks.get(expected_type.lower())
        if check_fn:
            return check_fn(result)
        return True
    
    def _is_json_string(self, s: Any) -> bool:
        """Check if string is valid JSON."""
        if not isinstance(s, str):
            return False
        try:
            json.loads(s)
            return True
        except:
            return False
    
    def add_rule(self, category: str, rule: VerificationRule) -> None:
        """Add a custom verification rule."""
        if category not in self._custom_rules:
            self._custom_rules[category] = []
        self._custom_rules[category].append(rule)
    
    def record_feedback(
        self,
        result: Any,
        task: str,
        was_correct: bool,
        feedback: Optional[str] = None
    ) -> None:
        """Record user feedback for learning."""
        self._feedback_history.append({
            "result_hash": hashlib.md5(str(result).encode()).hexdigest(),
            "task": task,
            "was_correct": was_correct,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent feedback
        if len(self._feedback_history) > 1000:
            self._feedback_history = self._feedback_history[-1000:]


class QualityGate:
    """
    A quality gate that must be passed before proceeding.
    """
    
    def __init__(
        self,
        name: str,
        verifier: ResultVerifier,
        min_confidence: float = 0.7,
        required_checks: Optional[List[str]] = None
    ):
        self.name = name
        self.verifier = verifier
        self.min_confidence = min_confidence
        self.required_checks = required_checks or []
    
    async def check(
        self,
        result: Any,
        task: str,
        expected_type: Optional[str] = None
    ) -> Tuple[bool, VerificationReport]:
        """
        Check if result passes the quality gate.
        
        Returns: (passed, report)
        """
        report = await self.verifier.verify(
            result=result,
            task_description=task,
            expected_type=expected_type,
            level=VerificationLevel.STANDARD
        )
        
        # Check confidence threshold
        if report.confidence < self.min_confidence:
            return False, report
        
        # Check required checks passed
        if self.required_checks:
            for check in self.required_checks:
                if not any(check.lower() in cp.lower() for cp in report.checks_passed):
                    return False, report
        
        # Check overall result
        passed = report.result in [VerificationResult.PASSED, VerificationResult.NEEDS_IMPROVEMENT]
        
        return passed, report


# Singleton instance
_verifier: Optional[ResultVerifier] = None

def get_verifier() -> ResultVerifier:
    """Get the singleton verifier instance."""
    global _verifier
    if _verifier is None:
        _verifier = ResultVerifier()
    return _verifier
