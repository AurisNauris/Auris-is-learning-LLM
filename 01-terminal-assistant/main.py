import os
import time
import json
from dotenv import load_dotenv
from openai import OpenAI

# loads the .env where API keys sit etc
# note that .env should be always in .gitignore
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TRANSCRIPT_PATH = "01-terminal-assistant/transcript.json"
SUMMARY_PATH = "01-terminal-assistant/memory-summary.txt"

MODEL = "gpt-4o-mini"
INSTRUCTIONS = "You are a helpful programming tutor. Be concise, clear, and practical."
MAX_MESSAGES_IN_CONTEX = 10 # simple trimming, send las 10 messages

def load_transcript():
    if os.path.exists(TRANSCRIPT_PATH):
        with open(TRANSCRIPT_PATH, 'r') as f:
            transcript = json.load(f)
        print(f"Loaded existing transcript with {len(transcript)} messages")
        return transcript
    return []

def save_transcript(transcript):
    with open(TRANSCRIPT_PATH, 'w') as f:
        json.dump(transcript, f, indent=2)

def save_summary(summary_text):
    with open(SUMMARY_PATH, 'w') as f:
        f.write(summary_text)

def load_summary():
    if os.path.exists(SUMMARY_PATH):
        with open(SUMMARY_PATH, 'r') as f:
            return f.read().strip()
    return ""

def clear_summary():
    if os.path.exists(SUMMARY_PATH):
        os.remove(SUMMARY_PATH)

def session_summary(transcript, summary_text):
    if not transcript:
        return "No previous session found."
    else:
        message_count = len(transcript)
        turn_count = message_count // 2

        last_message = transcript[-1]
        last_role = last_message["role"]
        last_content = last_message["content"].strip().replace("\n", " ")

        if len(last_content) > 80:
            last_content = last_content[:77] + "..."
        
        transcript_info = {
            f"Loaded {message_count} messages.",
            f"({turn_count} completed turns)",
            f"Last {last_role} message: {last_content}"
        }
    
    summary_info = "Summary memory loaded." if summary_text else "No summary memmory yet."
    return f"{transcript_info} {summary_info}"

def build_instructions(summary_text):
    if not summary_text:
        return INSTRUCTIONS
    
    return (
        f"{INSTRUCTIONS}\n"
        "Here is a summary of important prior context from earlier parts of our conversation: \n"
        f"{summary_text}\n\n"
        "Use this summary when relevant, but do not mention it unless asked."
    )

def print_history(transcript):
    if not transcript:
        print("No history yet.\n")
        return
    
    print("\n-----Transcript hisotry-----")
    for i, message in enumerate(transcript, start=1):
        content = message.get("content").strip().replace("\n", " ")
        if len(content) > 100:
            content = content[:97] + "..."
        print(f"|{i:02d}| {message.get('role')}: {content}")
    
    print("-"*10)
    print()

def build_model_input(transcript, new_user_message):
    recent_history = transcript[-MAX_MESSAGES_IN_CONTEX:]
    return recent_history + [new_user_message,]
    
def stream_assistant_reply(model_input, summary_text):

    assistant_text = ""
    with client.responses.stream(
        model=MODEL,
        instructions=build_instructions(summary_text),
        input=model_input
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
                assistant_text += event.delta
        
        stream.get_final_response()
    
    return assistant_text

def generate_summary(transcript):

    if not transcript:
        return ""
    
    transcript_text = json.dumps(transcript, indent=2)

    response = client.responses.create(
        model=MODEL,
        instructions=(
            "You create compact memory summaries for an assisstant.\n"
            "Summarize only useful facts from the conversation.\n"
            "Include stable preferences, goals, ongoing tasks, and important technical context.\n"
            "Do not invent anything.\n"
            "Keep it short and scannable."
        ),
        input=(
            "Summarize this conversation transcript into concise bullet points.\n\n"
            f"{transcript_text}"
        )
    )

    return response.output_text.strip()


def run():

    transcript = load_transcript()
    summary_text = load_summary()

    print("Terminal Assistant (local transcript mode)")
    print(session_summary(transcript, summary_text))
    print(f"Only the most recent {MAX_MESSAGES_IN_CONTEX} will be used for context.")
    print("Type 'exit' to quit.")
    print("Type '/reset' to clear the saved transcript.\n")
    print("Type '/history' to see conversation history.\n")
    print("Type '/summarize' to refresh summary memroy.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            save_transcript(transcript)
            print(f"Transcript saved to {TRANSCRIPT_PATH}")
            print("Goodbye!")
            break

        if user_input == "/reset":
            transcript = []
            save_transcript(transcript)
            clear_summary()
            summary_text = ""
            print("Transcript cleared.\n")
            continue

        if user_input == "/history":
            print_history(transcript)
            continue

        if user_input == "/summarize":
            print("\nUpdating summary memory...")
            summary_text = generate_summary(transcript)
            save_summary(summary_text)
            print("Summary memory saved.")
            print("\n---Summary Memory---")
            print(summary_text if summary_text else "(empty)")
            print("-"*10)
            print()
            continue


        if not user_input:
            continue

        new_user_message = {
            "role":"user",
            "content": user_input
            }
        
        model_input = build_model_input(transcript, new_user_message)

        print("\nAssistant: ", end="", flush=True)
        assistant_text = stream_assistant_reply(model_input, summary_text)

        transcript.append(new_user_message)
        transcript.append({"role":"assistant",
                           "content": assistant_text})
        
        save_transcript(transcript)

if __name__ == "__main__":
    run()
   