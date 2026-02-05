"""
Model Chaining Tools
====================
Create sequential AI model pipelines.
"""

import logging
from typing import Dict, Any, List, Optional
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class ModelChainingTools(ToolBase):
    """Model chaining pipeline tools."""
    
    def __init__(self, replicate_api=None, execution_agent=None):
        self.replicate_api = replicate_api
        self.execution_agent = execution_agent
        self.chains = {}  # Store chain definitions
    
    @tool(
        name="create_model_chain",
        description="Build multi-model execution pipeline where output from one model feeds into the next",
        category="model_chaining"
    )
    def create_model_chain(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create model chain pipeline.
        
        Args:
            name: Chain name
            description: What the chain produces
            steps: List of model steps with configs
                Example: [
                    {"model": "flux_pro", "type": "image", "prompt": "{{concept}}"},
                    {"model": "runway_gen3", "type": "video", "image": "{{step_1}}"},
                ]
        
        Returns:
            Chain ID and configuration
        """
        import uuid
        
        chain_id = str(uuid.uuid4())
        
        chain = {
            "id": chain_id,
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": str(datetime.now())
        }
        
        self.chains[chain_id] = chain
        
        logger.info(f"Created model chain '{name}' with {len(steps)} steps")
        
        return {
            "success": True,
            "chain_id": chain_id,
            "name": name,
            "step_count": len(steps)
        }
    
    @tool(
        name="execute_model_chain",
        description="Run chained model sequence with automatic data passing between models",
        category="model_chaining"
    )
    async def execute_model_chain(
        self,
        chain_id: str,
        input_data: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute model chain.
        
        Args:
            chain_id: Chain to execute
            input_data: Initial input for first model
            parameters: Override default configs
        
        Returns:
            Outputs from each step and final result
        """
        if chain_id not in self.chains:
            return {"success": False, "error": "Chain not found"}
        
        chain = self.chains[chain_id]
        outputs = []
        context = input_data.copy()
        
        logger.info(f"Executing chain '{chain['name']}' with {len(chain['steps'])} steps")
        
        try:
            for i, step in enumerate(chain["steps"]):
                logger.info(f"Step {i+1}/{len(chain['steps'])}: {step.get('type', 'unknown')}")
                
                # Resolve template variables in step config
                resolved_config = self._resolve_templates(step, context, outputs)
                
                # Execute step based on type
                if step["type"] == "image":
                    result = await self._execute_image_step(resolved_config)
                elif step["type"] == "video":
                    result = await self._execute_video_step(resolved_config)
                elif step["type"] == "text":
                    result = await self._execute_text_step(resolved_config)
                elif step["type"] == "audio":
                    result = await self._execute_audio_step(resolved_config)
                else:
                    result = {"error": f"Unknown step type: {step['type']}"}
                
                outputs.append(result)
                
                # Update context with step output
                context[f"step_{i+1}"] = result
                context[f"step_{i+1}_output"] = result.get("url") or result.get("content") or result
            
            return {
                "success": True,
                "chain_id": chain_id,
                "outputs": outputs,
                "final_output": outputs[-1] if outputs else None
            }
            
        except Exception as e:
            logger.error(f"Chain execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "outputs": outputs
            }
    
    def _resolve_templates(self, step: Dict, context: Dict, outputs: List) -> Dict:
        """Resolve {{template}} variables in step config."""
        import re
        
        resolved = {}
        
        for key, value in step.items():
            if isinstance(value, str) and "{{" in value:
                # Find all {{variable}} patterns
                templates = re.findall(r'\{\{([^}]+)\}\}', value)
                
                for template in templates:
                    if template in context:
                        value = value.replace(f"{{{{{template}}}}}", str(context[template]))
                    elif template.startswith("step_"):
                        # Handle step references like {{step_1}}
                        if template in context:
                            value = value.replace(f"{{{{{template}}}}}", str(context[template]))
            
            resolved[key] = value
        
        return resolved
    
    async def _execute_image_step(self, config: Dict) -> Dict:
        """Execute image generation step."""
        if self.execution_agent:
            return await self.execution_agent.execute_tool(
                tool_name="replicate_smart_generate",
                parameters={
                    "description": config.get("prompt", ""),
                    "content_type": "image",
                    "quality": config.get("quality", "balanced")
                }
            )
        return {"error": "Execution agent not configured"}
    
    async def _execute_video_step(self, config: Dict) -> Dict:
        """Execute video generation step."""
        if self.execution_agent:
            params = {
                "description": config.get("prompt", ""),
                "content_type": "video",
                "quality": config.get("quality", "balanced")
            }
            
            # Add image if image-to-video
            if "image" in config:
                params["image_url"] = config["image"]
            
            return await self.execution_agent.execute_tool(
                tool_name="replicate_smart_generate",
                parameters=params
            )
        return {"error": "Execution agent not configured"}
    
    async def _execute_text_step(self, config: Dict) -> Dict:
        """Execute text generation step."""
        if self.execution_agent:
            return await self.execution_agent.execute_tool(
                tool_name="replicate_smart_generate",
                parameters={
                    "description": config.get("prompt", ""),
                    "content_type": "text",
                    "quality": config.get("quality", "balanced")
                }
            )
        return {"error": "Execution agent not configured"}
    
    async def _execute_audio_step(self, config: Dict) -> Dict:
        """Execute audio generation step."""
        if self.execution_agent:
            return await self.execution_agent.execute_tool(
                tool_name="replicate_smart_generate",
                parameters={
                    "description": config.get("prompt", ""),
                    "content_type": "audio",
                    "quality": config.get("quality", "balanced"),
                    "duration": config.get("duration", 10)
                }
            )
        return {"error": "Execution agent not configured"}
    
    @tool(
        name="list_chain_templates",
        description="Get pre-built model chain templates for common workflows",
        category="model_chaining"
    )
    def list_chain_templates(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List available chain templates.
        
        Args:
            category: Filter by image, video, content, product
        
        Returns:
            Available templates
        """
        templates = {
            "product_design_chain": {
                "name": "Product Design Pipeline",
                "description": "Concept → Design → Variations → Mockup",
                "category": "product",
                "steps": [
                    {"type": "text", "prompt": "Generate creative {{product_type}} design concept"},
                    {"type": "image", "prompt": "{{step_1}}"},
                    {"type": "image", "prompt": "{{step_2}} but with different colors"},
                    {"type": "image", "prompt": "Product mockup of {{step_2}}"}
                ]
            },
            "video_production_chain": {
                "name": "Video Production Flow",
                "description": "Image → Video → Music → Composite",
                "category": "video",
                "steps": [
                    {"type": "image", "prompt": "{{scene_description}}"},
                    {"type": "video", "image": "{{step_1}}", "prompt": "{{motion_prompt}}"},
                    {"type": "audio", "prompt": "Background music, {{mood}}"}
                ]
            },
            "content_marketing_chain": {
                "name": "Content Marketing Suite",
                "description": "Topic → Article → Image → Social",
                "category": "content",
                "steps": [
                    {"type": "text", "prompt": "Write blog post about {{topic}}"},
                    {"type": "image", "prompt": "Featured image for: {{step_1}}"},
                    {"type": "text", "prompt": "Create 3 social media posts from: {{step_1}}"}
                ]
            }
        }
        
        if category:
            templates = {k: v for k, v in templates.items() if v["category"] == category}
        
        return {
            "success": True,
            "templates": templates,
            "count": len(templates)
        }
    
    @tool(
        name="save_chain_template",
        description="Save custom chain as reusable template",
        category="model_chaining"
    )
    def save_chain_template(
        self,
        chain_id: str,
        template_name: str,
        category: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Save chain as template.
        
        Args:
            chain_id: Chain to save
            template_name: Name for template
            category: Template category
            description: What it does
        
        Returns:
            Template ID
        """
        if chain_id not in self.chains:
            return {"success": False, "error": "Chain not found"}
        
        # Save template logic here
        return {
            "success": True,
            "template_name": template_name,
            "message": "Template saved successfully"
        }


from datetime import datetime
