"""
Enhanced Inter-Agent Communication System
==========================================

Provides a robust message bus and coordination protocol for agents.

Features:
- Message passing between agents
- Event-driven architecture
- Request/response patterns
- Pub/sub for broadcasts
- Agent collaboration protocols
- State synchronization
"""

import logging
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of inter-agent messages."""
    REQUEST = "request"  # Request/response pattern
    RESPONSE = "response"  # Response to a request
    EVENT = "event"  # One-way event notification
    BROADCAST = "broadcast"  # Broadcast to all agents
    COLLABORATION = "collaboration"  # Collaboration request
    HANDOFF = "handoff"  # Task handoff between agents
    STATUS_UPDATE = "status_update"  # Agent status update


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class AgentMessage:
    """Message passed between agents."""
    message_id: str
    message_type: MessageType
    from_agent: str
    to_agent: Optional[str]  # None for broadcasts
    priority: MessagePriority
    
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # For request/response
    correlation_id: Optional[str] = None  # Links request to response
    requires_response: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "priority": self.priority.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "correlation_id": self.correlation_id,
            "requires_response": self.requires_response
        }


@dataclass
class CollaborationRequest:
    """Request for agents to collaborate on a task."""
    collaboration_id: str
    initiator_agent: str
    participating_agents: List[str]
    task_description: str
    shared_context: Dict[str, Any]
    coordination_strategy: str  # "sequential", "parallel", "hierarchical"
    
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, active, completed, failed
    results: Dict[str, Any] = field(default_factory=dict)


class AgentMessageBus:
    """
    Central message bus for inter-agent communication.
    
    Features:
    - Message routing between agents
    - Pub/sub for events
    - Request/response pattern with timeout
    - Message priority queuing
    - Message history and replay
    """
    
    def __init__(self):
        # Message routing
        self.agents: Dict[str, 'AgentEndpoint'] = {}
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Message queues by agent
        self.message_queues: Dict[str, asyncio.Queue] = {}
        
        # Pending requests (for request/response pattern)
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # Event subscribers (topic -> subscribers)
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)
        
        # Message history
        self.message_history: List[AgentMessage] = []
        
        # Active collaborations
        self.collaborations: Dict[str, CollaborationRequest] = {}
        
        # Running state
        self._running = False
        
        logger.info("Agent Message Bus initialized")
    
    async def start(self):
        """Start the message bus."""
        self._running = True
        logger.info("Agent Message Bus started")
    
    async def stop(self):
        """Stop the message bus."""
        self._running = False
        logger.info("Agent Message Bus stopped")
    
    def register_agent(self, agent_id: str) -> 'AgentEndpoint':
        """Register an agent with the message bus."""
        if agent_id not in self.agents:
            self.message_queues[agent_id] = asyncio.Queue()
            endpoint = AgentEndpoint(agent_id, self)
            self.agents[agent_id] = endpoint
            logger.info(f"Agent registered: {agent_id}")
            return endpoint
        
        return self.agents[agent_id]
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.message_queues[agent_id]
            
            # Remove from subscribers
            for topic in list(self.subscribers.keys()):
                self.subscribers[topic].discard(agent_id)
            
            logger.info(f"Agent unregistered: {agent_id}")
    
    async def send_message(self, message: AgentMessage):
        """Send a message through the bus."""
        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]
        
        # Route message
        if message.message_type == MessageType.BROADCAST:
            await self._broadcast_message(message)
        elif message.to_agent:
            await self._route_to_agent(message)
        else:
            logger.warning(f"Message {message.message_id} has no recipient")
    
    async def _route_to_agent(self, message: AgentMessage):
        """Route message to a specific agent."""
        if message.to_agent not in self.message_queues:
            logger.error(f"Agent {message.to_agent} not found")
            return
        
        await self.message_queues[message.to_agent].put(message)
        logger.debug(f"Routed message {message.message_id} to {message.to_agent}")
    
    async def _broadcast_message(self, message: AgentMessage):
        """Broadcast message to all agents."""
        for agent_id in list(self.agents.keys()):
            if agent_id != message.from_agent:  # Don't send to sender
                await self.message_queues[agent_id].put(message)
        
        logger.debug(f"Broadcast message {message.message_id} to all agents")
    
    async def request(
        self,
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request and wait for response.
        
        Returns the response content or None if timeout.
        """
        correlation_id = str(uuid.uuid4())
        
        # Create future for response
        response_future = asyncio.Future()
        self.pending_requests[correlation_id] = response_future
        
        # Send request
        request_msg = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.REQUEST,
            from_agent=from_agent,
            to_agent=to_agent,
            priority=MessagePriority.NORMAL,
            content=content,
            correlation_id=correlation_id,
            requires_response=True
        )
        
        await self.send_message(request_msg)
        
        try:
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request from {from_agent} to {to_agent} timed out")
            return None
        finally:
            # Clean up
            self.pending_requests.pop(correlation_id, None)
    
    async def respond(
        self,
        to_agent: str,
        correlation_id: str,
        content: Dict[str, Any]
    ):
        """Send a response to a request."""
        # Check if there's a pending request
        if correlation_id in self.pending_requests:
            self.pending_requests[correlation_id].set_result(content)
        else:
            logger.warning(f"No pending request for correlation_id: {correlation_id}")
    
    def subscribe(self, agent_id: str, topic: str):
        """Subscribe an agent to a topic."""
        self.subscribers[topic].add(agent_id)
        logger.info(f"Agent {agent_id} subscribed to topic: {topic}")
    
    def unsubscribe(self, agent_id: str, topic: str):
        """Unsubscribe an agent from a topic."""
        self.subscribers[topic].discard(agent_id)
        logger.info(f"Agent {agent_id} unsubscribed from topic: {topic}")
    
    async def publish(self, from_agent: str, topic: str, content: Dict[str, Any]):
        """Publish an event to a topic."""
        subscribers = self.subscribers.get(topic, set())
        
        for subscriber_id in subscribers:
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.EVENT,
                from_agent=from_agent,
                to_agent=subscriber_id,
                priority=MessagePriority.NORMAL,
                content=content,
                metadata={"topic": topic}
            )
            await self.send_message(message)
        
        logger.debug(f"Published event to topic {topic} ({len(subscribers)} subscribers)")
    
    async def initiate_collaboration(
        self,
        initiator_agent: str,
        participating_agents: List[str],
        task_description: str,
        shared_context: Dict[str, Any],
        coordination_strategy: str = "sequential"
    ) -> str:
        """Initiate a collaboration between multiple agents."""
        collaboration_id = str(uuid.uuid4())
        
        collaboration = CollaborationRequest(
            collaboration_id=collaboration_id,
            initiator_agent=initiator_agent,
            participating_agents=participating_agents,
            task_description=task_description,
            shared_context=shared_context,
            coordination_strategy=coordination_strategy
        )
        
        self.collaborations[collaboration_id] = collaboration
        
        # Notify all participants
        for agent_id in participating_agents:
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.COLLABORATION,
                from_agent=initiator_agent,
                to_agent=agent_id,
                priority=MessagePriority.HIGH,
                content={
                    "collaboration_id": collaboration_id,
                    "task_description": task_description,
                    "shared_context": shared_context,
                    "coordination_strategy": coordination_strategy,
                    "participants": participating_agents
                }
            )
            await self.send_message(message)
        
        collaboration.status = "active"
        logger.info(f"Collaboration initiated: {collaboration_id}")
        
        return collaboration_id
    
    def get_collaboration(self, collaboration_id: str) -> Optional[CollaborationRequest]:
        """Get collaboration details."""
        return self.collaborations.get(collaboration_id)
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100
    ) -> List[AgentMessage]:
        """Get message history with optional filtering."""
        filtered = self.message_history
        
        if agent_id:
            filtered = [
                m for m in filtered
                if m.from_agent == agent_id or m.to_agent == agent_id
            ]
        
        if message_type:
            filtered = [m for m in filtered if m.message_type == message_type]
        
        return filtered[-limit:]


class AgentEndpoint:
    """
    Endpoint for an agent to communicate via the message bus.
    """
    
    def __init__(self, agent_id: str, message_bus: AgentMessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
    
    async def send(
        self,
        to_agent: str,
        content: Dict[str, Any],
        message_type: MessageType = MessageType.EVENT,
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Send a message to another agent."""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            from_agent=self.agent_id,
            to_agent=to_agent,
            priority=priority,
            content=content
        )
        await self.message_bus.send_message(message)
    
    async def broadcast(
        self,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """Broadcast a message to all agents."""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.BROADCAST,
            from_agent=self.agent_id,
            to_agent=None,
            priority=priority,
            content=content
        )
        await self.message_bus.send_message(message)
    
    async def request(
        self,
        to_agent: str,
        content: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response."""
        return await self.message_bus.request(
            self.agent_id,
            to_agent,
            content,
            timeout
        )
    
    async def respond(self, correlation_id: str, content: Dict[str, Any]):
        """Respond to a request."""
        # Get the original request from history
        for msg in reversed(self.message_bus.message_history):
            if msg.correlation_id == correlation_id:
                await self.message_bus.respond(
                    msg.from_agent,
                    correlation_id,
                    content
                )
                return
        
        logger.warning(f"Could not find request for correlation_id: {correlation_id}")
    
    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        self.message_bus.subscribe(self.agent_id, topic)
    
    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic."""
        self.message_bus.unsubscribe(self.agent_id, topic)
    
    async def publish(self, topic: str, content: Dict[str, Any]):
        """Publish to a topic."""
        await self.message_bus.publish(self.agent_id, topic, content)
    
    async def receive(self, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Receive the next message."""
        try:
            queue = self.message_bus.message_queues[self.agent_id]
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                return await queue.get()
        except asyncio.TimeoutError:
            return None
    
    def on_message(self, message_type: MessageType, handler: Callable):
        """Register a message handler."""
        self.message_handlers[message_type].append(handler)
    
    async def start_listening(self):
        """Start listening for messages and dispatching to handlers."""
        while True:
            try:
                message = await self.receive(timeout=1.0)
                if message:
                    # Dispatch to handlers
                    handlers = self.message_handlers.get(message.message_type, [])
                    for handler in handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(message)
                            else:
                                handler(message)
                        except Exception as e:
                            logger.error(f"Handler error: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error in message loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)


# Singleton instance
_message_bus: Optional[AgentMessageBus] = None


def get_message_bus() -> AgentMessageBus:
    """Get the global message bus instance."""
    global _message_bus
    if _message_bus is None:
        _message_bus = AgentMessageBus()
    return _message_bus
