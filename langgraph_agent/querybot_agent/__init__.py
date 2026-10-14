"""
QueryBot Agent - A LangGraph-based SQL query and data visualization agent.
"""

from querybot_agent.agent import QueryBotAgent, ask_question
from querybot_agent.workflow_manager import WorkflowManager

__version__ = "0.1.0"
__all__ = ["QueryBotAgent", "ask_question", "WorkflowManager"]