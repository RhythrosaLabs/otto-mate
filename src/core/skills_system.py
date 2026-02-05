"""
Skills System - Dynamic skill loading and execution
===================================================

Loads skill definitions from SKILL.md files and makes them available to agents.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
import re

logger = logging.getLogger(__name__)


class Skill:
    """Represents a single skill with capabilities and workflows."""
    
    def __init__(self, name: str, path: str, content: str):
        self.name = name
        self.path = path
        self.raw_content = content
        
        # Parse skill definition
        self.description = self._extract_description()
        self.capabilities = self._extract_capabilities()
        self.tools_required = self._extract_tools()
        self.workflows = self._extract_workflows()
        self.best_practices = self._extract_best_practices()
        self.error_handling = self._extract_error_handling()
        self.dependencies = self._extract_dependencies()
        self.metadata = self._extract_metadata()
    
    def _extract_description(self) -> str:
        """Extract description from skill file."""
        match = re.search(r'## Description\n(.*?)\n\n##', self.raw_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_capabilities(self) -> List[str]:
        """Extract capabilities list."""
        match = re.search(r'## Capabilities\n(.*?)\n\n##', self.raw_content, re.DOTALL)
        if match:
            capabilities = []
            for line in match.group(1).split('\n'):
                if line.startswith('- **'):
                    cap = re.search(r'\*\*(.*?)\*\*', line)
                    if cap:
                        capabilities.append(cap.group(1))
            return capabilities
        return []
    
    def _extract_tools(self) -> List[str]:
        """Extract required tools."""
        match = re.search(r'## Tools Required\n(.*?)\n\n##', self.raw_content, re.DOTALL)
        if match:
            tools = []
            for line in match.group(1).split('\n'):
                if line.startswith('- `'):
                    tool = re.search(r'`(.*?)`', line)
                    if tool:
                        tools.append(tool.group(1))
            return tools
        return []
    
    def _extract_workflows(self) -> List[Dict[str, Any]]:
        """Extract workflow definitions."""
        workflows = []
        # Find all workflow code blocks
        workflow_pattern = r'### (.*?)\n```yaml\n(.*?)\n```'
        matches = re.finditer(workflow_pattern, self.raw_content, re.DOTALL)
        
        for match in matches:
            workflow_name = match.group(1).strip()
            workflow_yaml = match.group(2)
            
            try:
                workflow_data = yaml.safe_load(workflow_yaml)
                workflows.append({
                    'name': workflow_name,
                    'definition': workflow_data
                })
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse workflow {workflow_name}: {e}")
        
        return workflows
    
    def _extract_best_practices(self) -> List[str]:
        """Extract best practices."""
        match = re.search(r'## Best Practices\n(.*?)(?:\n\n##|\Z)', self.raw_content, re.DOTALL)
        if match:
            practices = []
            for line in match.group(1).split('\n'):
                if line.startswith('- '):
                    practices.append(line[2:].strip())
            return practices
        return []
    
    def _extract_error_handling(self) -> Dict[str, str]:
        """Extract error handling strategies."""
        match = re.search(r'## Error Handling\n(.*?)(?:\n\n##|\Z)', self.raw_content, re.DOTALL)
        if match:
            content = match.group(1)
            # Extract issue -> solution pairs
            error_patterns = re.finditer(r'### (.*?)\n(.*?)(?=\n###|\Z)', content, re.DOTALL)
            return {match.group(1).strip(): match.group(2).strip() for match in error_patterns}
        return {}
    
    def _extract_dependencies(self) -> List[str]:
        """Extract dependencies."""
        match = re.search(r'## Dependencies\n(.*?)(?:\n\n##|\Z)', self.raw_content, re.DOTALL)
        if match:
            deps = []
            for line in match.group(1).split('\n'):
                if line.startswith('- '):
                    deps.append(line[2:].strip())
            return deps
        return []
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata."""
        match = re.search(r'## Metadata\n(.*?)(?:\Z)', self.raw_content, re.DOTALL)
        if match:
            metadata = {}
            for line in match.group(1).split('\n'):
                if line.startswith('- **'):
                    key_val = re.search(r'\*\*(.*?)\*\*:\s*(.*)', line)
                    if key_val:
                        metadata[key_val.group(1).lower().replace(' ', '_')] = key_val.group(2)
            return metadata
        return {}
    
    def get_context_for_agent(self) -> str:
        """Get skill context formatted for agent prompt."""
        context = f"""
# Skill: {self.name}

## Description
{self.description}

## Capabilities
{chr(10).join(f'- {cap}' for cap in self.capabilities)}

## Required Tools
{chr(10).join(f'- {tool}' for tool in self.tools_required)}

## Available Workflows
{chr(10).join(f'- {wf["name"]}' for wf in self.workflows)}

## Best Practices
{chr(10).join(f'- {bp}' for bp in self.best_practices[:5])}  # Limit to top 5
"""
        return context
    
    def get_workflow(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get specific workflow definition."""
        for workflow in self.workflows:
            if workflow['name'].lower() == workflow_name.lower():
                return workflow['definition']
        return None
    
    def check_tool_availability(self, available_tools: List[str]) -> tuple[bool, List[str]]:
        """Check if required tools are available."""
        missing = [tool for tool in self.tools_required if tool not in available_tools]
        return len(missing) == 0, missing


class SkillsRegistry:
    """Central registry for all skills."""
    
    def __init__(self, skills_directory: Optional[str] = None):
        if skills_directory is None:
            # Default to skills/ in project root
            default_dir = Path(__file__).parent.parent.parent / "skills"
            skills_directory = str(default_dir)
        
        self.skills_directory = Path(skills_directory)
        self.skills: Dict[str, Skill] = {}
        self.load_skills()
    
    def load_skills(self):
        """Load all skills from skills directory."""
        if not self.skills_directory.exists():
            logger.warning(f"Skills directory not found: {self.skills_directory}")
            return
        
        logger.info(f"Loading skills from {self.skills_directory}")
        
        # Find all SKILL.md files
        skill_files = list(self.skills_directory.rglob("SKILL.md"))
        
        for skill_file in skill_files:
            try:
                # Skill name from parent directory
                skill_name = skill_file.parent.name
                
                # Read skill definition
                with open(skill_file, 'r') as f:
                    content = f.read()
                
                # Create skill object
                skill = Skill(skill_name, str(skill_file), content)
                self.skills[skill_name] = skill
                
                logger.info(f"Loaded skill: {skill_name} ({len(skill.capabilities)} capabilities, {len(skill.workflows)} workflows)")
                
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_file}: {e}")
        
        logger.info(f"Total skills loaded: {len(self.skills)}")
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a specific skill by name."""
        return self.skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """List all available skills."""
        return list(self.skills.keys())
    
    def find_skills_by_capability(self, capability_query: str) -> List[Skill]:
        """Find skills that match a capability query."""
        matching_skills = []
        query_lower = capability_query.lower()
        
        for skill in self.skills.values():
            # Check description
            if query_lower in skill.description.lower():
                matching_skills.append(skill)
                continue
            
            # Check capabilities
            for cap in skill.capabilities:
                if query_lower in cap.lower():
                    matching_skills.append(skill)
                    break
        
        return matching_skills
    
    def find_skills_by_tools(self, tools: List[str]) -> List[Skill]:
        """Find skills that use specific tools."""
        matching_skills = []
        
        for skill in self.skills.values():
            if any(tool in skill.tools_required for tool in tools):
                matching_skills.append(skill)
        
        return matching_skills
    
    def get_all_skills_context(self, max_skills: int = 10) -> str:
        """Get context for all skills to include in agent prompt."""
        context = "# Available Skills\n\n"
        
        for skill_name, skill in list(self.skills.items())[:max_skills]:
            context += f"## {skill_name}\n"
            context += f"{skill.description}\n"
            context += f"**Capabilities**: {', '.join(skill.capabilities[:3])}\n\n"
        
        if len(self.skills) > max_skills:
            context += f"\n... and {len(self.skills) - max_skills} more skills available.\n"
        
        return context
    
    def recommend_skill(self, task_description: str) -> Optional[Skill]:
        """Recommend the best skill for a task."""
        task_lower = task_description.lower()
        
        # Simple keyword matching for now
        keywords = {
            'ecommerce_automation': ['product', 'shop', 'store', 'printify', 'shopify', 'publish', 'inventory'],
            'product_design': ['design', 'image', 'create', 'mockup', 'tshirt', 'mug'],
            'social_media_marketing': ['social', 'post', 'instagram', 'facebook', 'twitter', 'marketing'],
            'research_analysis': ['research', 'market', 'competitor', 'analyze', 'trend'],
            'content_creation': ['content', 'blog', 'write', 'article', 'copy'],
            'data_analysis': ['data', 'analytics', 'metrics', 'report', 'analyze'],
            'seo_optimization': ['seo', 'search', 'optimize', 'keyword', 'ranking'],
            'web_automation': ['scrape', 'automate', 'browser', 'web', 'form'],
            'email_marketing': ['email', 'campaign', 'newsletter', 'subscriber']
        }
        
        # Score each skill
        skill_scores = {}
        for skill_name, skill_keywords in keywords.items():
            if skill_name in self.skills:
                score = sum(1 for kw in skill_keywords if kw in task_lower)
                if score > 0:
                    skill_scores[skill_name] = score
        
        # Return highest scoring skill
        if skill_scores:
            best_skill = max(skill_scores.items(), key=lambda x: x[1])[0]
            return self.skills[best_skill]
        
        return None
    
    def get_skills_summary(self) -> Dict[str, Any]:
        """Get summary of all skills."""
        return {
            'total_skills': len(self.skills),
            'skills': {
                name: {
                    'capabilities': len(skill.capabilities),
                    'workflows': len(skill.workflows),
                    'tools': len(skill.tools_required),
                    'domain': skill.metadata.get('domain', 'general')
                }
                for name, skill in self.skills.items()
            }
        }


# Global skills registry instance
_skills_registry: Optional[SkillsRegistry] = None

def get_skills_registry() -> SkillsRegistry:
    """Get the global skills registry instance."""
    global _skills_registry
    if _skills_registry is None:
        _skills_registry = SkillsRegistry()
    return _skills_registry
