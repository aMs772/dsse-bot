# def main():
#     print("Hello from dsse-bot!")


# if __name__ == "__main__":
#     main()


from src.chatbot import answer_question


def main():
    print("DSSE Assistant")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        try:
            answer = answer_question(question)

            print(f"\nBot: {answer}\n")

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()