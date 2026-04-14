import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# loads the .env where API keys sit etc
# note that .env should be always in .gitignore
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

previous_response_id = None

print("Terminal Assistant")
print("Type 'exit' to quit./n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ['exit','quit']:
        print("Goodbye!")
        break

    if not user_input:
        continue

    request = {
        "model" : "gpt-4o-mini",
        "instructions" : "You are a helpful programming tutor. Be concise, practical, and clear.",
        "input" : user_input,
        }
    
    if previous_response_id:
        request["previous_response_id"] = previous_response_id

    print(f"\nAssistant: ", end="",flush=True)
    
    # with client.responses.stream(**request) as stream:
    #     for event in stream:
    #         if event.type == "response.output_text.data":
    #             print(event.delta, end="", flush=True)
    print("\n ---stram-debug---")
    start = time.perf_counter()

    with client.responses.stream(**request) as stream:
        chunk_count = 0
        for text in stream.text_deltas:
            chunk_count += 1
            elapsed = time.perf_counter() - start
            #print(text, end="",flush=True)
            print(f"[{elapsed:0.3f}s] chunk {chunk_count}: {text!r}")

        final_response = stream.get_final_response()

    print("\n ---end-debug---")
    print("Final text: \n")
    print(final_response.output_text)
    print()
    previous_response_id = final_response.id