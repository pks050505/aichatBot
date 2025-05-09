import streamlit as st
import requests

st.title("AI Chatbot")
query = st.text_input("Ask a question:", placeholder="e.g., Tell me about crypto market trends")
if st.button("Submit"):
    with st.spinner("Fetching response..."):
        try:
            response = requests.post(
                "https://aichatbot-16909439193.asia-south1.run.app/chat",
                json={"query": query}
            )
            if response.status_code == 200:
                st.success("Response received!")
                st.json(response.json())
            else:
                st.error(f"Error: {response.text}")
        except Exception as e:
            st.error(f"Failed to connect: {str(e)}")