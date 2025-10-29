import os, json, re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

def get_batch(batch_size=20):
    """Ask LLM for a batch of words + hints."""
    prompt = (
        "Return a JSON array of simple English nouns and short factual hints. "
        f"Example: [{{'word':'apple','hint':'Edible fruit that grows on trees'}}]. "
        f"Include {batch_size} items, each lowercase, 3–10 letters, no spaces, truthful hints ≤12 words."
    )
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":"Output strict JSON only."},
                  {"role":"user","content":prompt}],
        temperature=0.4,
    )
    txt = re.sub(r"^```json|```$", "", r.choices[0].message.content.strip(), flags=re.MULTILINE)
    try:
        arr = json.loads(txt)
    except Exception:
        arr = [{"word": "apple", "hint": "Edible fruit that grows on trees"}]
    clean = []
    for i in arr:
        w = re.sub(r"[^a-z]", "", str(i.get("word", "")).lower())
        if 3 <= len(w) <= 10:
            clean.append({"word": w, "hint": i.get("hint", "Everyday object.")})
    return clean

def react(win, word, guess):
    role = "win" if win else "lose"
    prompt = (
        f"Role: {role}. "
        f"If win: short congrats ≤10 words. "
        f"If lose: playful 'uh no' ≤10 words. "
        f"Secret='{word}', Guess='{guess}'. Output text only."
    )
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":"Be ultra brief."},
                  {"role":"user","content":prompt}],
        temperature=0.7,
    )
    return r.choices[0].message.content.strip()

def play():
    print("🐊 Crocodile — multi-word edition. Type 'quit' to exit.")
    words = get_batch(20)
    i = 0
    while True:
        if i >= len(words):
            print("\n🆕 Fetching more words...\n")
            words = get_batch(20)
            i = 0
        word, hint = words[i]["word"], words[i]["hint"]
        i += 1

        print(f"\n🤖 New word! (Hint: {hint} | starts with '{word[0]}', {len(word)} letters)")
        while True:
            g = input("Your guess: ").strip().lower()
            if g in ("quit","exit"):
                print("Bye! 👋")
                return
            if g == word:
                print("LLM:", react(True, word, g))
            else:
                print("LLM:", react(False, word, g))
            again = input("Play again with next word? (y/n): ").strip().lower()
            if again not in ("y","yes"):
                print("Bye! 👋")
                return
            else:
                break  # move to next word

if __name__ == "__main__":
    try:
        play()
    except KeyboardInterrupt:
        print("\nBye!")

