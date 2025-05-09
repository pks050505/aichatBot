import os
from fastapi import FastAPI, HTTPException
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel


# Initialize FastAPI app
app = FastAPI()

# Set up API keys
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

# Initialize LLM and tools
groq_llm = ChatGroq(model='llama-3.3-70b-versatile')
search_tool = TavilySearchResults(max_results=2)

# System prompt
system_prompt = """
You are a smart, friendly, and concise AI chatbot. Use the provided search tool to fetch up-to-date information for questions about trends, news, or recent events. Structure your responses clearly with bullet points when summarizing information.
"""

# Create agent
agent = create_react_agent(
    model=groq_llm,
    tools=[search_tool],
    state_modifier=system_prompt,
)

# Pydantic model for request body
class QueryRequest(BaseModel):
    query: str

# API endpoint to handle queries
@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        state = {"messages": [HumanMessage(content=request.query)]}
        response = agent.invoke(state)
        return {"response": response['messages'][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/")
async def health():
    return {"status": "Chatbot is running"}
