from google.adk.agents import Agent
from google.adk.tools import google_search

search_agent = Agent(
    
   name="basic_search_agent",
   model="gemini-2.0-flash-exp", # Google AI Studios
   #model="gemini-2.0-flash-live-preview-04-09" # Vertex AI Studio

   description="Agent to answer questions using Google Search.",

   instruction="You are an expert researcher. You always stick to the facts.",

   tools=[google_search]
)