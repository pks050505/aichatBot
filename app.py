import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from google.cloud import storage

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up API keys
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

# Validate API keys
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable not set")

# Initialize LLM and tools
groq_llm = ChatGroq(model='llama-3.3-70b-versatile', api_key=GROQ_API_KEY)
search_tool = TavilySearchResults(max_results=2, api_key=TAVILY_API_KEY)

# System prompt for crypto trading expert
system_prompt = """
You are a super cool crypto trading guru jo crypto ke baare mein sab kuch jaanta hai, aur market analysis mein expert hai. Tum ek 10 saal ke bacche ko Hindi aur English mix language mein samjha rahe ho, jaise ek mazedaar story ya video game ke through. Use super simple words, aur fun examples, jaise crypto ko digital toys ya game ke coins se compare karo. Use the provided search tool to get the latest crypto market data, trends, ya news. Keep answers short, clear, aur bullet points mein, taaki baccha easily samjhe. Avoid big words like 'blockchain' ya 'technical analysis', but if you use them, explain them like a fun game (e.g., blockchain is like a magic notebook jo sab records rakhta hai). Make every answer engaging, jaise ek adventure, aur compare crypto market to a bazaar jahan prices upar-neeche hote hain like toys in a shop. Example: "Bitcoin ek shiny coin hai jo internet par use hota hai, aur uska price badalta hai jaise khilone ka daam!"
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
        raise

# HTML UI for root endpoint
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Guru Chatbot 💰</title>
    <style>
        body {
            font-family: 'Comic Sans MS', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #e0f7fa;
            background-image: url('https://www.transparenttextures.com/patterns/45-degree-fabric-light.png');
        }
        h1 {
            text-align: center;
            color: #d81b60;
            font-size: 36px;
            text-shadow: 2px 2px #ffca28;
        }
        p {
            text-align: center;
            color: #4a148c;
            font-size: 18px;
        }
        .input-container {
            display: flex;
            margin-bottom: 20px;
            background-color: #fff176;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ffca28;
            border-radius: 8px;
            background-color: #ffffff;
            font-family: 'Comic Sans MS', Arial, sans-serif;
        }
        button {
            padding: 12px 25px;
            font-size: 16px;
            background-color: #d81b60;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            margin-left: 10px;
            transition: background-color 0.3s;
            font-family: 'Comic Sans MS', Arial, sans-serif;
        }
        button:hover {
            background-color: #ad1457;
        }
        #response {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            min-height: 120px;
            border: 2px dashed #ffca28;
        }
        #response ul {
            list-style-type: none;
            padding-left: 0;
        }
        #response li {
            padding: 10px;
            background-color: #f3e5f5;
            margin: 5px 0;
            border-radius: 5px;
            font-size: 16px;
            position: relative;
            padding-left: 40px;
        }
        #response li:before {
            content: '💎';
            position: absolute;
            left: 10px;
            font-size: 20px;
        }
        .error {
            color: #d32f2f;
            margin-top: 10px;
            font-size: 16px;
            text-align: center;
        }
        .loading {
            color: #0288d1;
            font-style: italic;
            text-align: center;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <h1>Crypto Guru Chatbot 💰</h1>
    <p>Hi, chhote trader! Pooche digital coins ke baare mein, jaise Bitcoin ya Ethereum! 💎</p>
    <div class="input-container">
        <input type="text" id="query" placeholder="e.g., Bitcoin kya hai? Ya market kaisa hai?">
        <button onclick="sendQuery()">Batao!</button>
    </div>
    <div id="response"></div>

    <script>
        async function sendQuery() {
            const queryInput = document.getElementById('query');
            const responseDiv = document.getElementById('response');
            const query = queryInput.value.trim();

            if (!query) {
                responseDiv.innerHTML = '<p class="error">Arre, koi sawaal toh pooch, chhote trader!</p>';
                return;
            }

            responseDiv.innerHTML = '<p class="loading">Thoda wait karo, jawab dhoond raha hoon... ⏳</p>';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query })
                });

                if (response.ok) {
                    const data = await response.json();
                    const items = data.response || [];
                    responseDiv.innerHTML = '<ul>' + items.map(item => `<li>${item}</li>`).join('') + '</ul>';
                } else {
                    const errorText = await response.text();
                    console.error('Fetch error:', errorText);
                    responseDiv.innerHTML = `<p class="error">Oops! Kuch gadbad ho gaya: ${errorText}</p>`;
                }
            } catch (error) {
                console.error('Network error:', error);
                responseDiv.innerHTML = `<p class="error">Connection mein problem: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
"""

# Root endpoint to serve UI
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(content=html_content)

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
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "Chatbot is running"}