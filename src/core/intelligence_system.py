"""
Intelligence System - Enhanced Memory, Learning, and Self-Improvement
=====================================================================

A comprehensive system that makes Otto smarter through:
1. Entity Extraction - Auto-remember key facts from conversations
2. Failure Learning - Remember what caused errors and avoid repeating
3. Smart Fallbacks - Auto-retry with alternative tools/approaches
4. Workspace RAG - Search all generated content semantically
5. Self-Reflection - Analyze execution and improve future plans

This module brings all intelligence enhancements together.
"""

import logging
import json
import re
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from anthropic import Anthropic

logger = logging.getLogger(__name__)


# ============================================================================
# 1. ENTITY EXTRACTION - Auto-remember key facts
# ============================================================================

@dataclass
class ExtractedEntity:
    """A fact/entity extracted from conversation."""
    entity_type: str  # person, company, product, url, preference, price, style, etc.
    value: str
    context: str  # The sentence it was extracted from
    confidence: float = 0.9
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "conversation"  # conversation, execution, user_correction
    
    def to_dict(self) -> Dict:
        return asdict(self)


class EntityExtractor:
    """
    Extracts and manages entities/facts from conversations.
    Uses both regex patterns and LLM for intelligent extraction.
    """
    
    # Regex patterns for common entities
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
        "price": r'\$\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:dollars?|USD)',
        "phone": r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "file_path": r'/(?:files|Users|data)/[\w\-./]+\.\w+',
        "product_id": r'\b(?:product[_-]?id|sku)[:\s]*([A-Z0-9\-]+)',
        "api_key": r'\b(?:api[_-]?key|token)[:\s]*([A-Za-z0-9\-_]+)',
        "shopify_url": r'https?://[\w\-]+\.myshopify\.com[^\s]*',
        "printify_id": r'printify[_\s](?:product|shop)[_\s]?(?:id)?[:\s]*(\d+)',
    }
    
    # Keywords that indicate user preferences
    PREFERENCE_KEYWORDS = {
        "style": ["prefer", "like", "love", "want", "style", "aesthetic", "vibe"],
        "price": ["budget", "price", "cost", "spend", "afford"],
        "product": ["sell", "create", "make", "design", "product"],
    }
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        self.anthropic = anthropic_client
        self.extracted_entities: Dict[str, List[ExtractedEntity]] = {}
        self._load_persisted_entities()
    
    def _load_persisted_entities(self):
        """Load previously extracted entities from disk."""
        entity_file = Path("./data/intelligence/entities.json")
        if entity_file.exists():
            try:
                with open(entity_file) as f:
                    data = json.load(f)
                    for user_id, entities in data.items():
                        self.extracted_entities[user_id] = [
                            ExtractedEntity(**e) for e in entities
                        ]
                logger.info(f"Loaded {sum(len(e) for e in self.extracted_entities.values())} entities")
            except Exception as e:
                logger.error(f"Failed to load entities: {e}")
    
    def _save_persisted_entities(self):
        """Save extracted entities to disk."""
        entity_file = Path("./data/intelligence/entities.json")
        entity_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                user_id: [e.to_dict() for e in entities]
                for user_id, entities in self.extracted_entities.items()
            }
            with open(entity_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save entities: {e}")
    
    def extract_from_text(self, text: str, user_id: str = "default") -> List[ExtractedEntity]:
        """Extract entities from text using regex patterns."""
        entities = []
        
        for entity_type, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.lastindex else match.group(0)
                entity = ExtractedEntity(
                    entity_type=entity_type,
                    value=value,
                    context=text[max(0, match.start()-50):match.end()+50],
                    confidence=0.95
                )
                entities.append(entity)
        
        # Extract preferences using keywords
        lower_text = text.lower()
        for pref_type, keywords in self.PREFERENCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in lower_text:
                    # Extract the sentence containing the keyword
                    sentences = text.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            entity = ExtractedEntity(
                                entity_type=f"preference_{pref_type}",
                                value=sentence.strip(),
                                context=sentence,
                                confidence=0.7
                            )
                            entities.append(entity)
                            break
        
        # Store entities
        if user_id not in self.extracted_entities:
            self.extracted_entities[user_id] = []
        self.extracted_entities[user_id].extend(entities)
        self._save_persisted_entities()
        
        return entities
    
    async def extract_with_llm(self, text: str, user_id: str = "default") -> List[ExtractedEntity]:
        """Use LLM to extract structured entities from text."""
        if not self.anthropic:
            return self.extract_from_text(text, user_id)
        
        # First do regex extraction
        entities = self.extract_from_text(text, user_id)
        
        # Then use LLM for semantic extraction
        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system="""Extract key facts/entities from the user's message. Return JSON array of objects with:
- entity_type: person_name, company, product_name, brand, style_preference, price_point, target_audience, goal, deadline
- value: the extracted value
- confidence: 0.0-1.0

Focus on ACTIONABLE information Otto should remember. Skip generic/obvious facts.""",
                messages=[{"role": "user", "content": f"Extract entities from: {text}"}]
            )
            
            # Parse LLM response
            content = response.content[0].text
            # Find JSON in response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                llm_entities = json.loads(json_match.group())
                for e in llm_entities:
                    entity = ExtractedEntity(
                        entity_type=e.get("entity_type", "unknown"),
                        value=e.get("value", ""),
                        context=text[:100],
                        confidence=e.get("confidence", 0.8),
                        source="llm_extraction"
                    )
                    entities.append(entity)
                    if user_id not in self.extracted_entities:
                        self.extracted_entities[user_id] = []
                    self.extracted_entities[user_id].append(entity)
                
                self._save_persisted_entities()
                
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {e}")
        
        return entities
    
    def get_user_entities(self, user_id: str = "default") -> List[ExtractedEntity]:
        """Get all entities for a user."""
        return self.extracted_entities.get(user_id, [])
    
    def get_relevant_entities(self, query: str, user_id: str = "default", limit: int = 10) -> List[ExtractedEntity]:
        """Get entities relevant to a query."""
        entities = self.get_user_entities(user_id)
        if not entities:
            return []
        
        # Score entities by relevance
        query_lower = query.lower()
        scored = []
        for entity in entities:
            score = 0
            if entity.value.lower() in query_lower:
                score += 2
            if any(word in entity.value.lower() for word in query_lower.split()):
                score += 1
            if entity.entity_type in query_lower:
                score += 0.5
            if score > 0:
                scored.append((entity, score))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]


# ============================================================================
# 2. FAILURE LEARNING - Remember and avoid errors
# ============================================================================

@dataclass
class FailureRecord:
    """Records a failure for learning."""
    tool_name: str
    error_type: str  # parameter_error, api_error, rate_limit, validation_error
    error_message: str
    parameters: Dict[str, Any]
    fix_applied: Optional[str] = None
    fix_worked: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    occurrences: int = 1
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @property
    def signature(self) -> str:
        """Unique signature for this type of failure."""
        param_keys = sorted(self.parameters.keys()) if self.parameters else []
        return hashlib.md5(f"{self.tool_name}:{self.error_type}:{':'.join(param_keys)}".encode()).hexdigest()[:12]


class FailureLearner:
    """
    Learns from failures to prevent repeating the same mistakes.
    Tracks what parameters/conditions cause errors and suggests fixes.
    """
    
    def __init__(self):
        self.failures: Dict[str, FailureRecord] = {}  # signature -> record
        self.successful_fixes: Dict[str, Dict] = {}  # tool:error_pattern -> fix
        self._load_failure_history()
    
    def _load_failure_history(self):
        """Load failure history from disk."""
        failure_file = Path("./data/intelligence/failures.json")
        if failure_file.exists():
            try:
                with open(failure_file) as f:
                    data = json.load(f)
                    for sig, record in data.get("failures", {}).items():
                        self.failures[sig] = FailureRecord(**record)
                    self.successful_fixes = data.get("fixes", {})
                logger.info(f"Loaded {len(self.failures)} failure records, {len(self.successful_fixes)} fixes")
            except Exception as e:
                logger.error(f"Failed to load failure history: {e}")
    
    def _save_failure_history(self):
        """Save failure history to disk."""
        failure_file = Path("./data/intelligence/failures.json")
        failure_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "failures": {sig: r.to_dict() for sig, r in self.failures.items()},
                "fixes": self.successful_fixes
            }
            with open(failure_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save failure history: {e}")
    
    def record_failure(
        self,
        tool_name: str,
        error_message: str,
        parameters: Dict[str, Any],
        error_type: str = "unknown"
    ) -> FailureRecord:
        """Record a new failure."""
        # Classify error type if not provided
        if error_type == "unknown":
            error_type = self._classify_error(error_message)
        
        record = FailureRecord(
            tool_name=tool_name,
            error_type=error_type,
            error_message=error_message[:500],  # Truncate long errors
            parameters=self._sanitize_params(parameters)
        )
        
        # Check if we've seen this before
        if record.signature in self.failures:
            self.failures[record.signature].occurrences += 1
            self.failures[record.signature].timestamp = datetime.now().isoformat()
        else:
            self.failures[record.signature] = record
        
        self._save_failure_history()
        logger.info(f"Recorded failure: {tool_name} - {error_type}")
        return record
    
    def record_fix(
        self,
        tool_name: str,
        error_pattern: str,
        fix: Dict[str, Any],
        worked: bool
    ):
        """Record whether a fix worked."""
        key = f"{tool_name}:{error_pattern}"
        if worked:
            self.successful_fixes[key] = {
                "fix": fix,
                "success_count": self.successful_fixes.get(key, {}).get("success_count", 0) + 1,
                "last_success": datetime.now().isoformat()
            }
        self._save_failure_history()
    
    def _classify_error(self, error_message: str) -> str:
        """Classify an error into a category."""
        error_lower = error_message.lower()
        
        if "rate limit" in error_lower or "too many requests" in error_lower:
            return "rate_limit"
        elif "invalid" in error_lower and "parameter" in error_lower:
            return "parameter_error"
        elif "style must be one of" in error_lower:
            return "style_validation"
        elif "not found" in error_lower:
            return "not_found"
        elif "unauthorized" in error_lower or "api key" in error_lower:
            return "auth_error"
        elif "timeout" in error_lower:
            return "timeout"
        elif "unexpected keyword argument" in error_lower:
            return "parameter_mismatch"
        elif "missing" in error_lower and ("required" in error_lower or "parameter" in error_lower):
            return "missing_parameter"
        else:
            return "unknown"
    
    def _sanitize_params(self, params: Dict) -> Dict:
        """Remove sensitive data from parameters."""
        sanitized = {}
        sensitive_keys = {"api_key", "token", "password", "secret", "key"}
        for k, v in params.items():
            if any(s in k.lower() for s in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 200:
                sanitized[k] = v[:200] + "..."
            else:
                sanitized[k] = v
        return sanitized
    
    def get_known_fix(self, tool_name: str, error_message: str) -> Optional[Dict]:
        """Get a known fix for an error pattern."""
        error_type = self._classify_error(error_message)
        key = f"{tool_name}:{error_type}"
        
        if key in self.successful_fixes:
            return self.successful_fixes[key]["fix"]
        
        # Check for partial matches
        for fix_key, fix_data in self.successful_fixes.items():
            if fix_key.startswith(tool_name) and fix_data.get("success_count", 0) > 2:
                return fix_data["fix"]
        
        return None
    
    def should_skip_tool(self, tool_name: str) -> Tuple[bool, str]:
        """Check if a tool has too many failures and should be skipped."""
        recent_failures = 0
        for record in self.failures.values():
            if record.tool_name == tool_name:
                # Check if failure is recent (last 24 hours)
                try:
                    failure_time = datetime.fromisoformat(record.timestamp)
                    if datetime.now() - failure_time < timedelta(hours=24):
                        recent_failures += record.occurrences
                except:
                    pass
        
        if recent_failures >= 10:
            return True, f"Tool {tool_name} has {recent_failures} recent failures"
        return False, ""
    
    def get_failure_summary(self, tool_name: Optional[str] = None) -> Dict:
        """Get a summary of failures."""
        summary = {"total": 0, "by_type": {}, "by_tool": {}}
        
        for record in self.failures.values():
            if tool_name and record.tool_name != tool_name:
                continue
            
            summary["total"] += record.occurrences
            
            if record.error_type not in summary["by_type"]:
                summary["by_type"][record.error_type] = 0
            summary["by_type"][record.error_type] += record.occurrences
            
            if record.tool_name not in summary["by_tool"]:
                summary["by_tool"][record.tool_name] = 0
            summary["by_tool"][record.tool_name] += record.occurrences
        
        return summary


# ============================================================================
# 3. SMART FALLBACKS - Alternative approaches when tools fail
# ============================================================================

class SmartFallbackSystem:
    """
    Manages intelligent fallback strategies when tools fail.
    Learns which alternatives work best for different scenarios.
    """
    
    # Static fallback chains for common tools
    FALLBACK_CHAINS = {
        # Image generation fallbacks
        "replicate_create_product_design": [
            {"tool": "generate_tshirt_design", "param_map": {"description": "prompt"}},
            {"tool": "generate_image", "param_map": {"description": "prompt"}},
            {"tool": "replicate_smart_generate", "param_map": {"description": "prompt", "task_type": "image"}},
        ],
        "generate_tshirt_design": [
            {"tool": "replicate_create_product_design", "param_map": {"prompt": "description"}},
            {"tool": "generate_image", "param_map": {}},
        ],
        "generate_image": [
            {"tool": "replicate_smart_generate", "param_map": {"task_type": "image"}},
            {"tool": "replicate_create_product_design", "param_map": {"prompt": "description"}},
        ],
        
        # Printify fallbacks
        "printify_create_tshirt": [
            {"tool": "printify_create_product", "param_map": {"product_type": "tshirt"}},
        ],
        "printify_create_mug": [
            {"tool": "printify_create_product", "param_map": {"product_type": "mug"}},
        ],
        
        # Search fallbacks
        "search_web": [
            {"tool": "browse_url", "param_map": {"query": "url"}},
        ],
        
        # Video fallbacks
        "replicate_create_video": [
            {"tool": "replicate_smart_generate", "param_map": {"task_type": "video"}},
        ],
    }
    
    # Parameter transformations for common errors
    PARAMETER_FIXES = {
        "style_validation": {
            "recraft": {
                "style_map": {
                    "vector": "digital_illustration/2d_art_poster",
                    "vector_illustration": "digital_illustration/2d_art_poster",
                    "illustration": "digital_illustration",
                    "cartoon": "digital_illustration/infantile_sketch",
                    "cute": "digital_illustration/infantile_sketch",
                    "kawaii": "digital_illustration/infantile_sketch",
                    "realistic": "realistic_image",
                    "photo": "realistic_image",
                    "pixel": "digital_illustration/pixel_art",
                    "hand_drawn": "digital_illustration/hand_drawn",
                    "3d": "digital_illustration/handmade_3d",
                }
            }
        },
        "parameter_mismatch": {
            "common_renames": {
                "prompt": ["description", "text", "input"],
                "description": ["prompt", "text", "content"],
                "image_url": ["url", "image", "source_url", "design_url"],
                "url": ["image_url", "source", "link"],
            }
        }
    }
    
    def __init__(self, failure_learner: FailureLearner):
        self.failure_learner = failure_learner
        self.fallback_success_rates: Dict[str, Dict] = {}
        self._load_success_rates()
    
    def _load_success_rates(self):
        """Load fallback success rates from disk."""
        rates_file = Path("./data/intelligence/fallback_rates.json")
        if rates_file.exists():
            try:
                with open(rates_file) as f:
                    self.fallback_success_rates = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load fallback rates: {e}")
    
    def _save_success_rates(self):
        """Save fallback success rates to disk."""
        rates_file = Path("./data/intelligence/fallback_rates.json")
        rates_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(rates_file, 'w') as f:
                json.dump(self.fallback_success_rates, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save fallback rates: {e}")
    
    def get_fallback_chain(self, tool_name: str) -> List[Dict]:
        """Get the fallback chain for a tool, sorted by success rate."""
        chain = self.FALLBACK_CHAINS.get(tool_name, [])
        
        # Sort by success rate
        def get_success_rate(fallback):
            key = f"{tool_name}->{fallback['tool']}"
            stats = self.fallback_success_rates.get(key, {})
            attempts = stats.get("attempts", 0)
            successes = stats.get("successes", 0)
            return successes / attempts if attempts > 0 else 0.5
        
        return sorted(chain, key=get_success_rate, reverse=True)
    
    def get_parameter_fix(
        self,
        tool_name: str,
        error_message: str,
        parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get a parameter fix for an error."""
        error_type = self.failure_learner._classify_error(error_message)
        
        if error_type == "style_validation":
            # Fix style parameter
            if "style" in parameters:
                style = parameters["style"]
                style_map = self.PARAMETER_FIXES["style_validation"]["recraft"]["style_map"]
                if style.lower() in style_map:
                    fixed = parameters.copy()
                    fixed["style"] = style_map[style.lower()]
                    return fixed
                elif style not in style_map.values():
                    # Use default
                    fixed = parameters.copy()
                    fixed["style"] = "digital_illustration/2d_art_poster"
                    return fixed
        
        elif error_type == "parameter_mismatch":
            # Try to rename parameters
            renames = self.PARAMETER_FIXES["parameter_mismatch"]["common_renames"]
            fixed = parameters.copy()
            
            for param, value in parameters.items():
                if param in renames:
                    # Try alternative names
                    for alt in renames[param]:
                        if alt not in fixed:
                            fixed[alt] = value
                            del fixed[param]
                            return fixed
        
        return None
    
    def record_fallback_result(self, original_tool: str, fallback_tool: str, success: bool):
        """Record the result of using a fallback."""
        key = f"{original_tool}->{fallback_tool}"
        if key not in self.fallback_success_rates:
            self.fallback_success_rates[key] = {"attempts": 0, "successes": 0}
        
        self.fallback_success_rates[key]["attempts"] += 1
        if success:
            self.fallback_success_rates[key]["successes"] += 1
        
        self._save_success_rates()
    
    def transform_parameters(
        self,
        parameters: Dict[str, Any],
        param_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """Transform parameters according to a mapping."""
        transformed = {}
        
        for key, value in parameters.items():
            if key in param_map:
                new_key = param_map[key]
                transformed[new_key] = value
            else:
                transformed[key] = value
        
        # Add any fixed parameters from the map
        for key, value in param_map.items():
            if key not in parameters and not any(v == value for v in param_map.values()):
                # This is a fixed value, not a rename
                if isinstance(value, str) and value not in transformed:
                    transformed[key] = value
        
        return transformed


# ============================================================================
# 4. WORKSPACE RAG - Semantic search over generated content
# ============================================================================

class WorkspaceIndexer:
    """
    Indexes and searches all workspace content semantically.
    Enables Otto to remember and reference past work.
    """
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        import chromadb
        from chromadb.config import Settings
        
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Collection for workspace files
        self.workspace = self.client.get_or_create_collection(
            name="workspace_index",
            metadata={"description": "Indexed workspace content"}
        )
        
        # Collection for generated outputs
        self.outputs = self.client.get_or_create_collection(
            name="generated_outputs",
            metadata={"description": "Generated content tracking"}
        )
        
        logger.info("Workspace Indexer initialized")
    
    def index_file(
        self,
        file_path: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Index a file's content for semantic search."""
        file_id = hashlib.md5(file_path.encode()).hexdigest()
        
        # Chunk content if too long
        chunks = self._chunk_content(content, max_chars=2000)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_id}_{i}"
            self.workspace.upsert(
                documents=[chunk],
                metadatas=[{
                    "file_path": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "indexed_at": datetime.now().isoformat(),
                    **(metadata or {})
                }],
                ids=[chunk_id]
            )
        
        logger.info(f"Indexed file: {file_path} ({len(chunks)} chunks)")
        return file_id
    
    def index_output(
        self,
        tool_name: str,
        output: Any,
        prompt: str = "",
        metadata: Optional[Dict] = None
    ) -> str:
        """Index a tool's output for future reference."""
        output_id = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(output).encode()).hexdigest()[:8]}"
        
        # Create searchable document
        doc_parts = [f"Tool: {tool_name}"]
        if prompt:
            doc_parts.append(f"Prompt: {prompt}")
        
        if isinstance(output, dict):
            # Extract key information
            if output.get("url"):
                doc_parts.append(f"Output URL: {output['url']}")
            if output.get("file_path"):
                doc_parts.append(f"File: {output['file_path']}")
            if output.get("title"):
                doc_parts.append(f"Title: {output['title']}")
            if output.get("description"):
                doc_parts.append(f"Description: {output['description']}")
            if output.get("content"):
                doc_parts.append(f"Content: {str(output['content'])[:500]}")
        else:
            doc_parts.append(f"Output: {str(output)[:500]}")
        
        document = "\n".join(doc_parts)
        
        self.outputs.add(
            documents=[document],
            metadatas=[{
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat(),
                "has_url": bool(output.get("url") if isinstance(output, dict) else False),
                "has_file": bool(output.get("file_path") if isinstance(output, dict) else False),
                **(metadata or {})
            }],
            ids=[output_id]
        )
        
        logger.info(f"Indexed output: {output_id}")
        return output_id
    
    def search_workspace(
        self,
        query: str,
        n_results: int = 5,
        file_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Search indexed workspace content."""
        where_filter = None
        if file_types:
            where_filter = {"file_type": {"$in": file_types}}
        
        try:
            results = self.workspace.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            matches = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    matches.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i]
                    })
            
            return matches
        except Exception as e:
            logger.error(f"Workspace search failed: {e}")
            return []
    
    def search_outputs(
        self,
        query: str,
        tool_name: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Search generated outputs."""
        where_filter = None
        if tool_name:
            where_filter = {"tool_name": tool_name}
        
        try:
            results = self.outputs.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            matches = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    matches.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i]
                    })
            
            return matches
        except Exception as e:
            logger.error(f"Output search failed: {e}")
            return []
    
    def _chunk_content(self, content: str, max_chars: int = 2000) -> List[str]:
        """Split content into chunks."""
        if len(content) <= max_chars:
            return [content]
        
        chunks = []
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_stats(self) -> Dict:
        """Get indexer statistics."""
        return {
            "workspace_items": self.workspace.count(),
            "output_items": self.outputs.count()
        }


# ============================================================================
# 5. SELF-REFLECTION - Analyze and improve execution
# ============================================================================

@dataclass
class ExecutionReflection:
    """Reflection on a completed execution."""
    execution_id: str
    original_request: str
    steps_completed: int
    steps_total: int
    success: bool
    duration_seconds: float
    
    # Analysis
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    root_causes: List[str] = field(default_factory=list)
    
    # Improvements
    suggestions: List[str] = field(default_factory=list)
    parameter_learnings: Dict[str, Any] = field(default_factory=dict)
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SelfReflectionSystem:
    """
    Analyzes execution results to improve future performance.
    Learns from both successes and failures.
    """
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        self.anthropic = anthropic_client
        self.reflections: List[ExecutionReflection] = []
        self.learned_patterns: Dict[str, Any] = {}
        self._load_reflections()
    
    def _load_reflections(self):
        """Load previous reflections from disk."""
        reflection_file = Path("./data/intelligence/reflections.json")
        if reflection_file.exists():
            try:
                with open(reflection_file) as f:
                    data = json.load(f)
                    self.reflections = [ExecutionReflection(**r) for r in data.get("reflections", [])]
                    self.learned_patterns = data.get("patterns", {})
                logger.info(f"Loaded {len(self.reflections)} reflections")
            except Exception as e:
                logger.error(f"Failed to load reflections: {e}")
    
    def _save_reflections(self):
        """Save reflections to disk."""
        reflection_file = Path("./data/intelligence/reflections.json")
        reflection_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "reflections": [r.to_dict() for r in self.reflections[-100:]],  # Keep last 100
                "patterns": self.learned_patterns
            }
            with open(reflection_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save reflections: {e}")
    
    async def reflect_on_execution(
        self,
        request: str,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]],
        duration: float
    ) -> ExecutionReflection:
        """
        Analyze an execution and learn from it.
        """
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Basic analysis
        total_steps = len(plan.get("steps", []))
        successful_steps = sum(1 for r in results if r.get("status") == "success")
        overall_success = successful_steps == total_steps and total_steps > 0
        
        # Identify what worked and what failed
        what_worked = []
        what_failed = []
        root_causes = []
        
        for result in results:
            tool = result.get("tool", "unknown")
            if result.get("status") == "success":
                what_worked.append(f"{tool}: completed successfully")
            else:
                error = result.get("result", {}).get("error", "unknown error")
                what_failed.append(f"{tool}: {error[:100]}")
                
                # Analyze root cause
                if "style must be one of" in error:
                    root_causes.append(f"Invalid style parameter for {tool}")
                elif "rate limit" in error.lower():
                    root_causes.append(f"Rate limit hit for {tool}")
                elif "not found" in error.lower():
                    root_causes.append(f"Resource not found in {tool}")
                elif "parameter" in error.lower():
                    root_causes.append(f"Parameter issue in {tool}")
        
        # Create reflection
        reflection = ExecutionReflection(
            execution_id=execution_id,
            original_request=request[:200],
            steps_completed=successful_steps,
            steps_total=total_steps,
            success=overall_success,
            duration_seconds=duration,
            what_worked=what_worked,
            what_failed=what_failed,
            root_causes=root_causes
        )
        
        # Use LLM for deeper analysis if available
        if self.anthropic and not overall_success:
            try:
                suggestions = await self._get_llm_suggestions(request, results)
                reflection.suggestions = suggestions
            except Exception as e:
                logger.warning(f"LLM reflection failed: {e}")
        
        # Learn patterns
        self._extract_patterns(reflection, plan, results)
        
        # Store
        self.reflections.append(reflection)
        self._save_reflections()
        
        logger.info(f"Reflection complete: {successful_steps}/{total_steps} successful")
        return reflection
    
    async def _get_llm_suggestions(
        self,
        request: str,
        results: List[Dict]
    ) -> List[str]:
        """Get improvement suggestions from LLM."""
        failures = [r for r in results if r.get("status") != "success"]
        if not failures:
            return []
        
        failure_summary = "\n".join([
            f"- {r.get('tool')}: {r.get('result', {}).get('error', 'unknown')[:100]}"
            for r in failures[:5]
        ])
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system="You're an expert at debugging AI agent systems. Give 2-3 specific, actionable suggestions.",
            messages=[{
                "role": "user",
                "content": f"User requested: {request[:200]}\n\nFailures:\n{failure_summary}\n\nHow can we prevent these failures next time?"
            }]
        )
        
        # Parse suggestions
        content = response.content[0].text
        suggestions = [s.strip() for s in content.split('\n') if s.strip() and not s.startswith('#')]
        return suggestions[:5]
    
    def _extract_patterns(
        self,
        reflection: ExecutionReflection,
        plan: Dict,
        results: List[Dict]
    ):
        """Extract reusable patterns from execution."""
        # Learn successful tool combinations
        if reflection.success:
            tools_used = [s.get("tool") for s in plan.get("steps", [])]
            tool_chain = "->".join(tools_used)
            
            if tool_chain not in self.learned_patterns:
                self.learned_patterns[tool_chain] = {
                    "success_count": 0,
                    "example_request": reflection.original_request
                }
            self.learned_patterns[tool_chain]["success_count"] += 1
        
        # Learn parameter patterns that work
        for i, result in enumerate(results):
            if result.get("status") == "success":
                step = plan.get("steps", [])[i] if i < len(plan.get("steps", [])) else {}
                tool = step.get("tool", "")
                params = step.get("parameters", {})
                
                # Store successful parameters (sanitized)
                param_key = f"{tool}_params"
                if param_key not in self.learned_patterns:
                    self.learned_patterns[param_key] = []
                
                # Add if unique enough
                param_summary = {k: type(v).__name__ for k, v in params.items()}
                if param_summary not in self.learned_patterns[param_key]:
                    self.learned_patterns[param_key].append(param_summary)
    
    def get_suggestions_for_task(self, task_description: str) -> List[str]:
        """Get suggestions based on past learnings."""
        suggestions = []
        
        # Find similar past executions
        for reflection in self.reflections[-50:]:  # Last 50
            if any(word in reflection.original_request.lower() 
                   for word in task_description.lower().split()[:5]):
                if reflection.suggestions:
                    suggestions.extend(reflection.suggestions)
                if not reflection.success and reflection.root_causes:
                    suggestions.append(f"Avoid: {reflection.root_causes[0]}")
        
        return list(set(suggestions))[:5]
    
    def get_successful_patterns(self) -> List[str]:
        """Get patterns that have worked multiple times."""
        return [
            pattern for pattern, data in self.learned_patterns.items()
            if isinstance(data, dict) and data.get("success_count", 0) >= 3
        ]


# ============================================================================
# UNIFIED INTELLIGENCE SYSTEM
# ============================================================================

class IntelligenceSystem:
    """
    Unified system that combines all intelligence capabilities.
    This is the main interface for enhanced Otto intelligence.
    """
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        self.anthropic = anthropic_client
        
        # Initialize all subsystems
        self.entity_extractor = EntityExtractor(anthropic_client)
        self.failure_learner = FailureLearner()
        self.fallback_system = SmartFallbackSystem(self.failure_learner)
        self.workspace_indexer = WorkspaceIndexer()
        self.reflection_system = SelfReflectionSystem(anthropic_client)
        
        logger.info("Intelligence System initialized")
    
    # -------------------- Entity Extraction --------------------
    
    async def extract_entities(self, text: str, user_id: str = "default") -> List[ExtractedEntity]:
        """Extract entities from text."""
        return await self.entity_extractor.extract_with_llm(text, user_id)
    
    def get_user_context(self, user_id: str = "default") -> str:
        """Get formatted context from extracted entities."""
        entities = self.entity_extractor.get_user_entities(user_id)
        if not entities:
            return ""
        
        # Group by type
        by_type: Dict[str, List[str]] = {}
        for e in entities[-30:]:  # Last 30 entities
            if e.entity_type not in by_type:
                by_type[e.entity_type] = []
            if e.value not in by_type[e.entity_type]:
                by_type[e.entity_type].append(e.value)
        
        # Format
        parts = ["=== REMEMBERED CONTEXT ==="]
        for entity_type, values in by_type.items():
            parts.append(f"{entity_type}: {', '.join(values[:5])}")
        
        return "\n".join(parts)
    
    # -------------------- Failure Learning --------------------
    
    def record_failure(
        self,
        tool_name: str,
        error_message: str,
        parameters: Dict[str, Any]
    ) -> FailureRecord:
        """Record a tool failure for learning."""
        return self.failure_learner.record_failure(tool_name, error_message, parameters)
    
    def get_known_fix(self, tool_name: str, error_message: str) -> Optional[Dict]:
        """Get a known fix for an error."""
        return self.failure_learner.get_known_fix(tool_name, error_message)
    
    def record_fix_result(
        self,
        tool_name: str,
        error_pattern: str,
        fix: Dict,
        worked: bool
    ):
        """Record whether a fix worked."""
        self.failure_learner.record_fix(tool_name, error_pattern, fix, worked)
    
    # -------------------- Smart Fallbacks --------------------
    
    def get_fallback_options(self, tool_name: str) -> List[Dict]:
        """Get fallback tools for a failed tool."""
        return self.fallback_system.get_fallback_chain(tool_name)
    
    def get_parameter_fix(
        self,
        tool_name: str,
        error_message: str,
        parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get a parameter fix for an error."""
        return self.fallback_system.get_parameter_fix(tool_name, error_message, parameters)
    
    def record_fallback_result(self, original: str, fallback: str, success: bool):
        """Record fallback result for learning."""
        self.fallback_system.record_fallback_result(original, fallback, success)
    
    # -------------------- Workspace RAG --------------------
    
    def index_file(self, file_path: str, content: str, metadata: Optional[Dict] = None):
        """Index a file for semantic search."""
        return self.workspace_indexer.index_file(file_path, content, metadata)
    
    def index_output(self, tool_name: str, output: Any, prompt: str = ""):
        """Index a tool output for future reference."""
        return self.workspace_indexer.index_output(tool_name, output, prompt)
    
    def search_workspace(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search workspace content."""
        return self.workspace_indexer.search_workspace(query, n_results)
    
    def search_past_outputs(self, query: str, tool_name: Optional[str] = None, n_results: int = 5) -> List[Dict]:
        """Search past tool outputs."""
        return self.workspace_indexer.search_outputs(query, tool_name, n_results)
    
    # -------------------- Self-Reflection --------------------
    
    async def reflect_on_execution(
        self,
        request: str,
        plan: Dict,
        results: List[Dict],
        duration: float
    ) -> ExecutionReflection:
        """Analyze execution and learn from it."""
        return await self.reflection_system.reflect_on_execution(
            request, plan, results, duration
        )
    
    def get_task_suggestions(self, task: str) -> List[str]:
        """Get suggestions for a task based on past learnings."""
        return self.reflection_system.get_suggestions_for_task(task)
    
    # -------------------- Stats & Utilities --------------------
    
    def get_stats(self) -> Dict:
        """Get intelligence system statistics."""
        return {
            "entities": sum(len(e) for e in self.entity_extractor.extracted_entities.values()),
            "failures_recorded": len(self.failure_learner.failures),
            "fixes_learned": len(self.failure_learner.successful_fixes),
            "workspace_indexed": self.workspace_indexer.get_stats(),
            "reflections": len(self.reflection_system.reflections),
            "patterns_learned": len(self.reflection_system.learned_patterns)
        }
    
    def get_enhanced_context(
        self,
        query: str,
        user_id: str = "default"
    ) -> str:
        """
        Get comprehensive enhanced context for a query.
        Combines entities, workspace search, and past learnings.
        """
        context_parts = []
        
        # User entities
        user_context = self.get_user_context(user_id)
        if user_context:
            context_parts.append(user_context)
        
        # Relevant past outputs
        past_outputs = self.search_past_outputs(query, n_results=3)
        if past_outputs:
            context_parts.append("\n=== RELEVANT PAST WORK ===")
            for output in past_outputs:
                context_parts.append(f"• {output['content'][:150]}...")
        
        # Task suggestions
        suggestions = self.get_task_suggestions(query)
        if suggestions:
            context_parts.append("\n=== LEARNINGS ===")
            for s in suggestions[:3]:
                context_parts.append(f"• {s}")
        
        return "\n".join(context_parts)


# Singleton instance
_intelligence_system: Optional[IntelligenceSystem] = None


def get_intelligence_system(anthropic_client: Optional[Anthropic] = None) -> IntelligenceSystem:
    """Get or create the intelligence system singleton."""
    global _intelligence_system
    if _intelligence_system is None:
        _intelligence_system = IntelligenceSystem(anthropic_client)
    return _intelligence_system
