import os
from fastapi import FastAPI, HTTPException
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from google.cloud import storage

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

# Function to save response to Google Cloud Storage
def save_to_gcs(bucket_name, file_name, content):
    try:
        client = storage.Client()
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_string(content)
        return True
    except Exception as e:
        print(f"Failed to save to GCS: {str(e)}")
        return False

# API endpoint to handle queries
@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        state = {"messages": [HumanMessage(content=request.query)]}
        response = agent.invoke(state)
        content = response['messages'][-1].content
        # Format response as a list of strings
        formatted = [line.strip('- ').strip() for line in content.split('\n') if line.strip()]
        # Save to GCS
        bucket_name = "polytechnic-b89d6-chatbot-storage"
        file_name = f"response_{request.query[:10]}_{os.urandom(4).hex()}.txt"
        save_to_gcs(bucket_name, file_name, str(formatted))
        return {"response": formatted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/")
async def health():
    return {"status": "Chatbot is running"}
