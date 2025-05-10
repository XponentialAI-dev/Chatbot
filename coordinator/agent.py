from rag.agent import rag_agent
from google_search.agent import search_agent
from google.adk.agents import LlmAgent

from pathlib import Path

def load_instructions() -> str:
    """Load prompt from prompts.md in the same directory"""
    prompt_path = Path(__file__).parent / "prompts.md"
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise RuntimeError(
            f"Prompt file not found at: {prompt_path}\n"
            "Please create a 'prompts.md' file in the coordinator directory."
        )

coordinator = LlmAgent(
    name="HelpDeskCoordinator",
    model="gemini-2.0-flash-exp",
    instruction=load_instructions(),
    description="Its cordinator agent which delegate task to search agent and rag agent",
    # allow_transfer=True is often implicit with sub_agents in AutoFlow
    sub_agents=[rag_agent, search_agent],
)