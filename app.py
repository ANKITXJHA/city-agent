from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import requests
import streamlit as st

from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from tavily import TavilyClient


# ---------------- Weather tool ----------------
@tool
def get_weather(city: str) -> str:
    """Get the current weather of a city.
    Input should be a city name, for example 'Noida' or 'Delhi'."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric",  # Temperature in Celsius
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        # OpenWeather returns 200 on success; anything else is an error
        if response.status_code != 200:
            return f"Error: {data.get('message', 'Could not fetch weather')}"

        return (
            f"Weather in {data['name']}: {data['weather'][0]['description']}. "
            f"Temperature: {data['main']['temp']}°C "
            f"(feels like {data['main']['feels_like']}°C). "
            f"Humidity: {data['main']['humidity']}%."
        )
    except requests.exceptions.RequestException as e:
        return f"Error: Could not fetch weather data ({e})."


# ---------------- Tavily news tool ----------------
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def get_news(query: str) -> str:
    """Get the latest news about a topic or a city.
    Input should be a search query, for example 'Noida news' or 'AI news India'."""
    try:
        result = tavily_client.search(
            query=query,
            topic="news",   # Search only in news sources
            max_results=3,  # Return at most 3 articles
        )

        articles = result.get("results", [])
        if not articles:
            return "No news found for this query."

        # Convert each article into a short text block for the LLM
        news_list = []
        for article in articles:
            news_list.append(
                f"Title: {article['title']}\n"
                f"Summary: {article['content']}\n"
                f"URL: {article['url']}"
            )

        return "\n\n".join(news_list)
    except Exception as e:
        return f"Error: Could not fetch news ({e})."


# ---------------- Agent setup (built once, reused across reruns) ----------------
@st.cache_resource
def build_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

    return create_agent(
        llm,
        tools=[get_weather, get_news],
        system_prompt="You are a helpful city assistant. Use the tools for live weather and news.",
        # Pause before every tool call so the user can approve or deny it in the UI
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"get_weather": True, "get_news": True},
            )
        ],
        # The checkpointer stores the conversation, which gives the agent memory
        checkpointer=InMemorySaver(),
    )


agent = build_agent()


# ---------------- Page and session state ----------------
st.set_page_config(page_title="City Agent", page_icon="🏙️")
st.title("🏙️ City Agent")
st.caption("Live weather and news. Every tool call needs your approval.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())  # One thread = one conversation
    st.session_state.chat = []       # Messages shown on screen
    st.session_state.pending = None  # Tool calls waiting for approval
    st.session_state.round = 0       # Used to give radio buttons fresh keys

config = {"configurable": {"thread_id": st.session_state.thread_id}}


def handle_result(result):
    """Either store the pending tool calls or show the final answer."""
    if "__interrupt__" in result:
        # The agent paused and is waiting for a human decision
        st.session_state.pending = result["__interrupt__"][0].value["action_requests"]
    else:
        st.session_state.pending = None
        st.session_state.chat.append(
            {"role": "assistant", "content": result["messages"][-1].content}
        )


# Sidebar: start a fresh conversation
with st.sidebar:
    if st.button("New chat"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat = []
        st.session_state.pending = None
        st.rerun()


# ---------------- Show chat history ----------------
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------------- Approval UI ----------------
if st.session_state.pending:
    with st.chat_message("assistant"):
        st.warning("The agent wants to call the following tool(s). Please review:")

        choices = []
        for i, action in enumerate(st.session_state.pending):
            st.markdown(f"**{action['name']}** with `{action['args']}`")
            choice = st.radio(
                "Decision",
                ["Approve", "Deny"],
                index=1,  # Deny is the safer default
                horizontal=True,
                key=f"decision_{st.session_state.round}_{i}",
            )
            choices.append(choice)

        if st.button("Submit decision"):
            # One decision per tool call, in the same order as the requests
            decisions = []
            for choice in choices:
                if choice == "Approve":
                    decisions.append({"type": "approve"})
                else:
                    decisions.append(
                        {"type": "reject", "message": "Tool call denied by user."}
                    )

            with st.spinner("Working..."):
                try:
                    result = agent.invoke(
                        Command(resume={"decisions": decisions}), config=config
                    )
                    handle_result(result)
                except Exception as e:
                    st.session_state.pending = None
                    st.error(f"Something went wrong: {e}")

            st.session_state.round += 1
            st.rerun()

# ---------------- Chat input (hidden while an approval is pending) ----------------
else:
    prompt = st.chat_input("Ask about weather or news, e.g. 'Noida weather and news'")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    config=config,
                )
                handle_result(result)
            except Exception as e:
                st.error(f"Something went wrong: {e}")

        st.rerun()
