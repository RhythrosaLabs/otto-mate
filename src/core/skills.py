"""
Skills & Plugin Ecosystem

Plugin system for extending Otto capabilities, similar to OpenClaw's ClawHub.
Plugins can add new skills, tools, and integrations.
"""

import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """Skill categories"""
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    MEDIA = "media"
    ANALYTICS = "analytics"
    BUSINESS = "business"
    CUSTOM = "custom"


@dataclass
class SkillMetadata:
    """Metadata for a skill/plugin"""
    id: str
    name: str
    version: str
    description: str
    author: str
    category: SkillCategory
    tags: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)  # Dependencies
    config_schema: Optional[Dict[str, Any]] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None


class BaseSkill(ABC):
    """
    Base class for all Otto skills/plugins
    
    Skills extend Otto's capabilities with new tools and actions.
    """
    
    @property
    @abstractmethod
    def metadata(self) -> SkillMetadata:
        """Return skill metadata"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]):
        """Initialize skill with configuration"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Clean up skill resources"""
        pass
    
    def get_tools(self) -> Dict[str, Callable]:
        """
        Return dictionary of tool functions this skill provides
        
        Example:
            return {
                "send_email": self.send_email,
                "create_calendar_event": self.create_event
            }
        """
        return {}
    
    def get_commands(self) -> Dict[str, Callable]:
        """
        Return dictionary of slash commands this skill provides
        
        Example:
            return {
                "/email": self.email_command,
                "/calendar": self.calendar_command
            }
        """
        return {}


class SkillRegistry:
    """
    Central registry for all skills/plugins
    
    Manages skill lifecycle, discovery, and invocation.
    """
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills: Dict[str, BaseSkill] = {}
        self.tools: Dict[str, Callable] = {}
        self.commands: Dict[str, Callable] = {}
    
    async def discover_skills(self):
        """Discover and load all skills from skills directory"""
        logger.info(f"🔍 Discovering skills in {self.skills_dir}")
        
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return
        
        # Scan for Python modules
        for skill_path in self.skills_dir.glob("*"):
            if skill_path.is_dir() and (skill_path / "__init__.py").exists():
                await self._load_skill(skill_path.name)
    
    async def _load_skill(self, module_name: str):
        """Load a single skill module"""
        try:
            # Import module
            module = importlib.import_module(f"skills.{module_name}")
            
            # Find BaseSkill subclasses
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                    # Instantiate skill
                    skill = obj()
                    metadata = skill.metadata
                    
                    # Check dependencies
                    if not self._check_dependencies(metadata.requires):
                        logger.warning(f"❌ Skipping {metadata.name}: missing dependencies")
                        continue
                    
                    # Initialize skill
                    config = self._load_skill_config(metadata.id)
                    await skill.initialize(config)
                    
                    # Register skill
                    self.skills[metadata.id] = skill
                    
                    # Register tools
                    for tool_name, tool_func in skill.get_tools().items():
                        self.tools[tool_name] = tool_func
                    
                    # Register commands
                    for cmd_name, cmd_func in skill.get_commands().items():
                        self.commands[cmd_name] = cmd_func
                    
                    logger.info(f"✅ Loaded skill: {metadata.name} v{metadata.version}")
        
        except Exception as e:
            logger.error(f"Failed to load skill {module_name}: {e}")
    
    def _check_dependencies(self, requires: List[str]) -> bool:
        """Check if all required dependencies are installed"""
        for dependency in requires:
            try:
                importlib.import_module(dependency)
            except ImportError:
                logger.warning(f"Missing dependency: {dependency}")
                return False
        return True
    
    def _load_skill_config(self, skill_id: str) -> Dict[str, Any]:
        """Load skill configuration from config file"""
        import json
        
        config_path = self.skills_dir / skill_id / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}
    
    async def install_skill(self, skill_id: str, source: str):
        """
        Install skill from Git repository or marketplace
        
        Args:
            skill_id: Unique skill identifier
            source: Git URL or marketplace ID
        """
        logger.info(f"📦 Installing skill: {skill_id} from {source}")
        
        try:
            import subprocess
            
            # Clone repository
            skill_path = self.skills_dir / skill_id
            
            if source.startswith(("http://", "https://", "git@")):
                # Git repository
                subprocess.run(
                    ["git", "clone", source, str(skill_path)],
                    check=True
                )
            else:
                # Marketplace (future: download from ClawHub-style registry)
                logger.warning("Marketplace not implemented yet")
                return
            
            # Install dependencies
            requirements = skill_path / "requirements.txt"
            if requirements.exists():
                subprocess.run(
                    ["pip", "install", "-r", str(requirements)],
                    check=True
                )
            
            # Load skill
            await self._load_skill(skill_id)
            
            logger.info(f"✅ Installed skill: {skill_id}")
        
        except Exception as e:
            logger.error(f"Failed to install skill {skill_id}: {e}")
    
    async def uninstall_skill(self, skill_id: str):
        """Uninstall a skill"""
        if skill_id in self.skills:
            # Shutdown skill
            await self.skills[skill_id].shutdown()
            
            # Unregister
            del self.skills[skill_id]
            
            # Remove directory
            import shutil
            skill_path = self.skills_dir / skill_id
            if skill_path.exists():
                shutil.rmtree(skill_path)
            
            logger.info(f"✅ Uninstalled skill: {skill_id}")
    
    def get_skill(self, skill_id: str) -> Optional[BaseSkill]:
        """Get skill by ID"""
        return self.skills.get(skill_id)
    
    def list_skills(self) -> List[SkillMetadata]:
        """List all registered skills"""
        return [skill.metadata for skill in self.skills.values()]
    
    async def invoke_tool(self, tool_name: str, **kwargs) -> Any:
        """Invoke a tool function"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        return await self.tools[tool_name](**kwargs)
    
    async def invoke_command(self, command: str, args: str) -> str:
        """Invoke a slash command"""
        if command not in self.commands:
            return f"Unknown command: {command}"
        
        return await self.commands[command](args)
    
    async def shutdown_all(self):
        """Shutdown all skills"""
        for skill in self.skills.values():
            try:
                await skill.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down skill: {e}")


# Example skill implementations


class EmailSkill(BaseSkill):
    """Example skill: Email integration"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            id="email",
            name="Email",
            version="1.0.0",
            description="Send and manage emails",
            author="Otto Team",
            category=SkillCategory.COMMUNICATION,
            tags=["email", "communication"],
            requires=["aiosmtplib"]
        )
    
    async def initialize(self, config: Dict[str, Any]):
        self.smtp_host = config.get("smtp_host")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        logger.info("📧 Email skill initialized")
    
    async def shutdown(self):
        logger.info("📧 Email skill shutdown")
    
    def get_tools(self) -> Dict[str, Callable]:
        return {
            "send_email": self.send_email,
            "read_inbox": self.read_inbox
        }
    
    async def send_email(self, to: str, subject: str, body: str) -> str:
        """Send an email"""
        import aiosmtplib
        from email.message import EmailMessage
        
        message = EmailMessage()
        message["From"] = self.username
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        
        await aiosmtplib.send(
            message,
            hostname=self.smtp_host,
            port=self.smtp_port,
            username=self.username,
            password=self.password,
            start_tls=True
        )
        
        return f"✅ Email sent to {to}"
    
    async def read_inbox(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Read recent emails from inbox"""
        # Implementation would use IMAP
        return []


class CalendarSkill(BaseSkill):
    """Example skill: Calendar integration"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            id="calendar",
            name="Calendar",
            version="1.0.0",
            description="Manage calendar events",
            author="Otto Team",
            category=SkillCategory.PRODUCTIVITY,
            tags=["calendar", "scheduling"],
            requires=["google-api-python-client"]
        )
    
    async def initialize(self, config: Dict[str, Any]):
        self.calendar_id = config.get("calendar_id", "primary")
        logger.info("📅 Calendar skill initialized")
    
    async def shutdown(self):
        logger.info("📅 Calendar skill shutdown")
    
    def get_tools(self) -> Dict[str, Callable]:
        return {
            "create_event": self.create_event,
            "list_events": self.list_events
        }
    
    async def create_event(self, title: str, start: str, end: str) -> str:
        """Create a calendar event"""
        # Implementation would use Google Calendar API
        return f"✅ Event created: {title}"
    
    async def list_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """List upcoming events"""
        # Implementation would use Google Calendar API
        return []
