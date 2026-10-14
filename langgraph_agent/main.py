from querybot_agent.workflow_manager import WorkflowManager
from querybot_agent.agent import QueryBotAgent
from dotenv import load_dotenv

load_dotenv('.env')

# For deployment on LangGraph Cloud
graph = WorkflowManager().compile_graph()

def main():
    """Main entry point for the Enhanced QueryBot agent."""
    print("🚀QueryBot LangGraph Agent is ready!")


if __name__ == "__main__":
    main()