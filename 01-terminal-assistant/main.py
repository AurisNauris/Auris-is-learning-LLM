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


if os.path.exists(TRANSCRIPT_PATH):
    with open(TRANSCRIPT_PATH, 'r') as f:
        transcript = json.load(f)
    print(f"Loaded existing transcript with {len(transcript)} messages")
else:
    transcript = []

print("Terminal Assistant")
print("Type 'exit' to quit./n")


while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ['exit','quit']:
        with open(TRANSCRIPT_PATH, "w") as f:
            json.dump(transcript, f, indent=2)
        print(f"Transcript saved to {TRANSCRIPT_PATH}")
        print("Goodbye!")
        break

    if not user_input:
        continue
    
    new_user_message = {
        "role":"user",
        "content":user_input,
    }

    model_input = transcript + [new_user_message]
    
    print(f"\nAssistant: ", end="",flush=True)
    assistant_text = ""

    with client.responses.stream(
        model="gpt-4o-mini",
        instructions="You are a helpful Python instructor. Be concice, clear and pracitcal.",
        input=model_input
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
                assistant_text += event.delta
        
        final_response = stream.get_final_response()

    print("\n")
    transcript.append({"role": "assistant",
                       "content": assistant_text})
   