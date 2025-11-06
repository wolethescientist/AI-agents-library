"""
Agent configuration and management module.

This module defines the AgentConfig dataclass for agent metadata and the
AgentManager service class for managing agent registry, validation, and retrieval.
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for a subject-specific AI agent.
    
    Attributes:
        id: Unique identifier for the agent
        name: Display name of the agent
        description: Brief description of the agent's purpose
        system_prompt: System-level prompt that defines agent behavior
        enabled: Whether the agent is currently active
    """
    id: str
    name: str
    description: str
    system_prompt: str
    enabled: bool = True
    
    def __post_init__(self):
        """Validate agent configuration after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Agent ID cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Agent name cannot be empty")
        if not self.system_prompt or not self.system_prompt.strip():
            raise ValueError("Agent system prompt cannot be empty")


# Agent registry with enhanced system prompts
AGENTS: dict[str, AgentConfig] = {
    "math": AgentConfig(
        id="math",
        name="Mathematics Agent",
        description="Ask me about any math topic - algebra, geometry, calculus, and more",
        system_prompt=(
            "You are an expert mathematics tutor with deep knowledge across all mathematical domains. "
            "Your role is to help students understand mathematical concepts clearly and build problem-solving skills. "
            "When answering questions:\n"
            "- Break down complex problems into manageable steps\n"
            "- Explain the reasoning behind each step\n"
            "- Use clear mathematical notation and formatting\n"
            "- Provide real-world examples when relevant\n"
            "- Encourage critical thinking by asking guiding questions\n"
            "- Be patient and supportive, adapting explanations to the student's level\n"
            "Always aim to build understanding, not just provide answers."
        ),
        enabled=True
    ),
    "english": AgentConfig(
        id="english",
        name="English Agent",
        description="Improve your grammar, writing, reading comprehension, and literature analysis",
        system_prompt=(
            "You are an experienced English language and literature tutor. "
            "Your expertise spans grammar, composition, reading comprehension, and literary analysis. "
            "When helping students:\n"
            "- Explain grammar rules clearly with examples\n"
            "- Provide constructive feedback on writing\n"
            "- Help develop critical reading and analysis skills\n"
            "- Discuss literary devices, themes, and author techniques\n"
            "- Encourage creative expression and clear communication\n"
            "- Adapt your vocabulary and explanations to the student's level\n"
            "Foster a love for language and literature while building practical skills."
        ),
        enabled=True
    ),
    "physics": AgentConfig(
        id="physics",
        name="Physics Agent",
        description="Understand motion, force, energy, and the fundamental laws of nature",
        system_prompt=(
            "You are a knowledgeable physics tutor passionate about helping students understand the natural world. "
            "Your expertise covers mechanics, thermodynamics, electromagnetism, optics, and modern physics. "
            "When teaching physics:\n"
            "- Connect abstract concepts to real-world phenomena and everyday experiences\n"
            "- Use diagrams and visual descriptions to illustrate concepts\n"
            "- Break down complex problems using systematic problem-solving approaches\n"
            "- Explain the physical intuition behind mathematical formulas\n"
            "- Highlight the beauty and elegance of physical laws\n"
            "- Encourage experimental thinking and curiosity\n"
            "Make physics accessible, engaging, and relevant to students' lives."
        ),
        enabled=True
    ),
    "chemistry": AgentConfig(
        id="chemistry",
        name="Chemistry Agent",
        description="Learn about chemical reactions, elements, compounds, and molecular interactions",
        system_prompt=(
            "You are an enthusiastic chemistry tutor with expertise in all areas of chemistry. "
            "You help students understand atoms, molecules, reactions, and the chemical nature of matter. "
            "When teaching chemistry:\n"
            "- Explain concepts at both macroscopic and molecular levels\n"
            "- Use analogies and real-world examples to clarify abstract ideas\n"
            "- Help visualize molecular structures and reaction mechanisms\n"
            "- Connect chemistry to everyday life and practical applications\n"
            "- Emphasize safety and proper chemical handling when relevant\n"
            "- Build understanding of periodic trends and chemical principles\n"
            "Make chemistry fascinating by revealing the molecular world around us."
        ),
        enabled=True
    ),
    "civic": AgentConfig(
        id="civic",
        name="Civic Education Agent",
        description="Learn about governance, citizenship, rights, responsibilities, and civic engagement",
        system_prompt=(
            "You are a knowledgeable civic education tutor dedicated to helping students understand "
            "government systems, civic responsibilities, and democratic participation. "
            "When teaching civic education:\n"
            "- Explain governmental structures and processes clearly\n"
            "- Discuss rights and responsibilities of citizens\n"
            "- Encourage critical thinking about civic issues\n"
            "- Present balanced perspectives on political topics\n"
            "- Connect historical context to current events\n"
            "- Promote informed and active citizenship\n"
            "- Use relevant examples from various democratic systems\n"
            "Empower students to become engaged, informed citizens who understand their role in society."
        ),
        enabled=True
    )
}


class AgentManager:
    """Service class for managing AI agent registry and operations.
    
    The AgentManager handles agent validation, retrieval, and listing operations.
    It ensures that only valid, enabled agents are accessible to the system.
    """
    
    def __init__(self, agents: Optional[dict[str, AgentConfig]] = None):
        """Initialize the AgentManager with agent configurations.
        
        Args:
            agents: Dictionary of agent configurations. If None, uses default AGENTS.
        
        Raises:
            ValueError: If agent validation fails
        """
        self.agents = self._validate_agents(agents or AGENTS)
        logger.info(f"AgentManager initialized with {len(self.agents)} agents")
    
    def _validate_agents(self, agents: dict[str, AgentConfig]) -> dict[str, AgentConfig]:
        """Validate agent configurations.
        
        Args:
            agents: Dictionary of agent configurations to validate
        
        Returns:
            Validated agent dictionary
        
        Raises:
            ValueError: If any agent configuration is invalid
        """
        if not agents:
            raise ValueError("Agent registry cannot be empty")
        
        validated = {}
        for agent_id, agent_config in agents.items():
            try:
                # Verify the agent_id matches the config id
                if agent_id != agent_config.id:
                    logger.warning(
                        f"Agent key '{agent_id}' does not match config id '{agent_config.id}'. "
                        f"Using config id."
                    )
                
                # Validate agent config (triggers __post_init__ validation)
                if not isinstance(agent_config, AgentConfig):
                    raise ValueError(f"Invalid agent config type for '{agent_id}'")
                
                validated[agent_config.id] = agent_config
                logger.debug(f"Validated agent: {agent_config.id} ({agent_config.name})")
                
            except Exception as e:
                logger.error(f"Failed to validate agent '{agent_id}': {e}")
                raise ValueError(f"Invalid agent configuration for '{agent_id}': {e}")
        
        return validated
    
    def get_agent(self, agent_id: str) -> AgentConfig:
        """Retrieve an agent by ID.
        
        Args:
            agent_id: The unique identifier of the agent
        
        Returns:
            The AgentConfig for the requested agent
        
        Raises:
            KeyError: If the agent is not found or is disabled
        """
        if agent_id not in self.agents:
            available = ", ".join(self.list_agent_ids())
            raise KeyError(
                f"Agent '{agent_id}' not found. Available agents: {available}"
            )
        
        agent = self.agents[agent_id]
        
        if not agent.enabled:
            raise KeyError(f"Agent '{agent_id}' is currently disabled")
        
        return agent
    
    def list_agents(self, include_disabled: bool = False) -> list[dict]:
        """List all agents with their metadata.
        
        Args:
            include_disabled: Whether to include disabled agents in the list
        
        Returns:
            List of agent metadata dictionaries
        """
        agents_list = []
        
        for agent in self.agents.values():
            if not include_disabled and not agent.enabled:
                continue
            
            agents_list.append({
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "enabled": agent.enabled
            })
        
        return agents_list
    
    def list_agent_ids(self, include_disabled: bool = False) -> list[str]:
        """List all agent IDs.
        
        Args:
            include_disabled: Whether to include disabled agents
        
        Returns:
            List of agent IDs
        """
        if include_disabled:
            return list(self.agents.keys())
        
        return [
            agent_id for agent_id, agent in self.agents.items()
            if agent.enabled
        ]
    
    def is_agent_available(self, agent_id: str) -> bool:
        """Check if an agent is available (exists and is enabled).
        
        Args:
            agent_id: The agent ID to check
        
        Returns:
            True if the agent exists and is enabled, False otherwise
        """
        return agent_id in self.agents and self.agents[agent_id].enabled
    
    def get_agent_count(self, include_disabled: bool = False) -> int:
        """Get the total number of agents.
        
        Args:
            include_disabled: Whether to include disabled agents in the count
        
        Returns:
            Number of agents
        """
        if include_disabled:
            return len(self.agents)
        
        return sum(1 for agent in self.agents.values() if agent.enabled)
