import llm_tools
from utils import *


def main():
    history = [
        {
            "role": "system",
            "content": (
                "You are a Kubernetes assistant. "
                "You have many tools to help you manage Kubernetes resources. "
                "Not use markdown output. "
                "Not use english answer. "
                "Friendly use table output. "
                "Every response end with: Ciallo～(∠・ω<)⌒★"
            )
        },
    ]
    while True:
        try:
            user_input = input("Input your questions (or 'exit/quit' to exit): >>> ").strip()
            if user_input.lower() in ("exit", "quit"):
                print("Bye!")
                break
            if user_input:
                for response in call_llm(prompt=user_input, thinking=True, max_tokens=8192, messages=history, temperature=0.1):
                    print(response, end="", flush=True)
                print()
        except KeyboardInterrupt:
            print("\nExit.")
            break
        except EOFError:
            print("\nExit.")
            break

if __name__ == "__main__":
    main()