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
STATE_PATH = "01-terminal-assistant/state.json"
previous_response_id = None

print("Terminal Assistant")
print("Type 'exit' to quit./n")

if os.path.exists(TRANSCRIPT_PATH):
    with open(TRANSCRIPT_PATH, 'r') as f:
        transcript = json.load(f)
    print(f"Loaded existing transcript with {len(transcript)} messages")
else:
    transcript = []

if os.path.exists(STATE_PATH):
    with open(STATE_PATH, "r") as f:
        state = json.load(f)
    previous_response_id = state.get("previous_response_id")
    print(f"Loaded previous_response_id: {previous_response_id}")
else:
    previous_response_id = None


while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ['exit','quit']:
        with open(TRANSCRIPT_PATH, "w") as f:
            json.dump(transcript, f, indent=2)
        print(f"Transcript saved to {TRANSCRIPT_PATH}")

        with open(STATE_PATH, "w") as f:
            json.dump({"previous_response_id": previous_response_id}, f, indent=2)
        print(f"State saved to {STATE_PATH}")


        print("Goodbye!")
        break

    if not user_input:
        continue
    
    transcript.append({"role":"user","content":user_input})

    request = {
        "model" : "gpt-4o-mini",
        "instructions" : "You are a helpful programming tutor. Be concise, practical, and clear.",
        "input" : user_input,
        }
    

    if previous_response_id:
        request["previous_response_id"] = previous_response_id

    print(f"\nAssistant: ", end="",flush=True)

    assistant_text = ""

    with client.responses.stream(**request) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
                assistant_text += event.delta
        
        final_response = stream.get_final_response()

    transcript.append({"role": "assistant",
                       "content": assistant_text})
    previous_response_id = final_response.id
   