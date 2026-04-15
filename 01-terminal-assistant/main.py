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
MODEL = "gpt-4o-mini"
INSTRUCTIONS = "You are a helpful programming tutor. Be concise, clear, and practical."

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

def session_summary(transcript):
    if not transcript:
        return "No previous session found."
    
    message_count = len(transcript)
    turn_count = message_count // 2

    last_message = transcript[-1]
    last_role = last_message["role"]
    last_content = last_message["content"].strip().replace("\n", " ")

    if len(last_content) > 80:
        last_content = last_content[:77] + "..."
    
    return (
        f"Loaded {message_count} messages.",
        f"({turn_count} completed turns)",
        f"Last {last_role} message: {last_content}"
    )

def stream_assistant_reply(model_input):

    assistant_text = ""
    with client.responses.stream(
        model=MODEL,
        instructions=INSTRUCTIONS,
        input=model_input
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
                assistant_text += event.delta
        
        stream.get_final_response()
    
    return assistant_text

def run():

    transcript = load_transcript()

    print("Terminal Assistant (local transcript mode)")
    print(session_summary(transcript))

    print("Type 'exit' to quit.")
    print("Type '/reset' to clear the saved transcript.\n")

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
            print("Transcript cleared.\n")
            continue

        if not user_input:
            continue

        new_user_message = {
            "role":"user",
            "content": user_input
            }
        
        model_input = transcript + [new_user_message,]

        print("\nAssistant: ", end="", flush=True)
        assistant_text = stream_assistant_reply(model_input)

        transcript.append(new_user_message)
        transcript.append({"role":"assistant",
                           "content": assistant_text})
        
        save_transcript(transcript)

if __name__ == "__main__":
    run()
