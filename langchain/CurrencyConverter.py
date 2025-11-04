from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from .env or environment
API_KEY = os.getenv("APILAYER_API_KEY")

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency using APILayer Exchange Rates Data API."""
    if not API_KEY:
        return "❌ Missing API key. Please set APILAYER_API_KEY in your .env file."

    url = "https://api.apilayer.com/exchangerates_data/convert"
    headers = {"apikey": API_KEY}
    params = {
        "amount": amount,
        "from": from_currency.upper(),
        "to": to_currency.upper(),
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            result = data["result"]
            rate = data["info"]["rate"]
            date = data["date"]
            pretty_date = datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y")
            return (
                f"According to APILayer Marketplace, "
                f"{amount:g} {from_currency.upper()} = {result:,.2f} {to_currency.upper()} "
                f"(Rate: {rate:.4f}, Date: {pretty_date})"
            )
        else:
            return f"⚠️ API Error: {data.get('error', {}).get('info', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return f"🌐 Network error: {e}"
    except Exception as e:
        return f"⚠️ Error: {e}"

# Create chat model
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# Create agent with the tool
agent = create_agent(
    model,
    tools=[convert_currency],
    system_prompt=(
        "You are a helpful currency conversion assistant.\n\n"
        "When the user asks a question like 'How much is 100$ in baht?' or "
        "'How much is 100 USD in yen?', do the following:\n"
        "1. Identify the amount, source currency, and target currency.\n"
        "2. Use the convert_currency tool to get real-time rates.\n"
        "3. Respond with a friendly, concise conversion summary.\n\n"
        "If the question isn’t about currency conversion, politely say you only handle that."
    ),
)

print("💱 Currency Converter Assistant")
print("Ask things like:")
print(" • How much is 100$ in baht?")
print(" • How much is 100 USD in yen?")
print(" • Convert 50 EUR to GBP")
print("Type 'exit' to quit.\n")

# Interactive chat loop
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["exit", "quit", "q"]:
        print("👋 Goodbye!")
        break
    if not user_input:
        continue

    print("\n🤖 Assistant: ", end="")
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            content = getattr(last, "content", None) or last.get("content", None)
            print(content or str(last))
        else:
            print(result)
    except Exception as e:
        print(f"Error: {e}")
    print()