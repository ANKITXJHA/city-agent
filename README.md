# 🏙️ City Agent

An AI agent that fetches **live weather** and **latest news** for any city, built with LangChain and Streamlit. The agent never runs a tool on its own: **every tool call needs your approval** in the UI (human-in-the-loop).

## Demo

<!-- Add your demo video/GIF here. See the note in the "Adding the demo" section below. -->
Demo video: [_Video_](https://www.linkedin.com/posts/ankitjha21_ai-langchain-aiagents-ugcPost-7517119815833284608-fRSZ/?highlightedUpdateUrn=urn%3Ali%3Aactivity%3A7517119853372194816&highlightedUpdateType=SOCIAL_SHARE&origin=SOCIAL_SHARE&utm_source=share&utm_medium=member_desktop&rcm=ACoAAFIioswB0tx3wF9xEcbdRnvf1FE6dSHuWA4)

## Features

- **Weather tool**: current temperature, feels-like, humidity and conditions via the OpenWeather API
- **News tool**: latest news on any city or topic via the Tavily API
- **Human-in-the-loop approval**: the agent pauses before each tool call, and you choose Approve or Deny in the UI. A denied call is reported back to the LLM, which then explains to you that it could not proceed
- **Conversation memory**: follow-ups like "now show me the news there" work, because the history is stored per conversation thread
- **Error handling**: wrong city names, API errors and timeouts return readable messages instead of crashing the app

## Tech stack

| Part | Tool |
| --- | --- |
| LLM | Groq (`openai/gpt-oss-120b`) |
| Agent framework | LangChain `create_agent` + LangGraph |
| Approval flow | `HumanInTheLoopMiddleware` + `InMemorySaver` checkpointer |
| Weather data | OpenWeather API |
| News search | Tavily API |
| UI | Streamlit |

## How it works

1. You send a message, for example "Noida weather and news".
2. The LLM decides which tools it needs and prepares the tool calls.
3. The middleware **interrupts** the agent and the UI shows each call with its arguments.
4. You approve or deny each call. Deny is the default choice, as a safe default.
5. Approved tools run, results go back to the LLM, and it writes the final answer.

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/ANKITXJHA/city-agent.git
cd city-agent
```

**2. Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your API keys**

Copy the example file and fill in your own keys:

```bash
cp .env.example .env          # On Windows: copy .env.example .env
```

| Key | Where to get it |
| --- | --- |
| `GROQ_API_KEY` | https://console.groq.com/keys |
| `OPENWEATHER_API_KEY` | https://home.openweathermap.org/api_keys |
| `TAVILY_API_KEY` | https://app.tavily.com |

> A new OpenWeather key can take 1-2 hours to activate. A `401` error at the start is normal.

**5. Run the app**

```bash
streamlit run app.py
```

## Example prompts

- "What's the weather in Noida?"
- "Give me the weather and latest news for Delhi"
- "Now show me AI news in India" (tests conversation memory)

Try denying one tool call to see how the agent reacts.

## Project structure

```
city-agent/
├── app.py              # Streamlit app: tools, agent, approval UI
├── requirements.txt    # Python dependencies
├── .env.example        # Template for API keys
├── .gitignore          # Keeps .env out of Git
└── README.md
```

## Limitations

- Memory uses `InMemorySaver`, so history is lost when the app restarts
- Weather shows only current conditions (no forecast)
- News quality depends on Tavily search results

## Ideas for next steps

- Add a RAG tool so the agent can answer questions from documents
- Add a 5-day forecast tool
- Use a persistent checkpointer (SQLite or Postgres) for long-term memory

## Security

API keys are loaded from environment variables. Never commit your `.env` file. If a key is ever pushed by mistake, delete it from the provider's dashboard and create a new one.

## Author

**Ankit Kumar Jha**
[GitHub](https://github.com/ANKITXJHA) · [LinkedIn](https://linkedin.com/in/ankitjha21ya)
