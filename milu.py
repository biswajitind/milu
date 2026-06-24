import argparse
import os

import openai
from dotenv import load_dotenv


def configure_openai():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    api_url = os.getenv("OPENAI_API_URL")
    if not api_key or not api_url:
        raise RuntimeError(
            "Please set OPENAI_API_KEY and OPENAI_API_URL in your .env file"
        )

    openai.api_key = api_key
    openai.api_base = api_url


def get_allowed_telegram_ids():
    configured_ids = os.getenv("ALLOWED_TELEGRAM_IDS", "")
    if not configured_ids.strip():
        return set()

    try:
        return {
            int(telegram_id.strip())
            for telegram_id in configured_ids.split(",")
            if telegram_id.strip()
        }
    except ValueError as error:
        raise RuntimeError(
            "ALLOWED_TELEGRAM_IDS must be a comma-separated list of integers"
        ) from error


def process_message(message):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content


def run_interactive():
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return
        if not user_input:
            continue

        print("Milu: " + process_message(user_input))


def run_bot():
    import telegram

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise RuntimeError("Please set TELEGRAM_BOT_TOKEN in your .env file")

    allowed_telegram_ids = get_allowed_telegram_ids()
    bot = telegram.Bot(token=telegram_token)
    offset = None
    print("Milu Telegram bot is running. Press Ctrl+C to stop.")

    try:
        while True:
            updates = bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                offset = update.update_id + 1

                if not update.message or not update.message.text:
                    continue

                chat_id = update.message.chat_id
                if allowed_telegram_ids and chat_id not in allowed_telegram_ids:
                    print(f"Ignoring message from unauthorized Telegram ID: {chat_id}")
                    continue

                try:
                    print(f"Received message from {chat_id}: {update.message.text}")
                    print(update.message)
                    reply = process_message(update.message.text)
                except Exception as error:
                    reply = f"Unable to process your message: {error}"

                bot.send_message(chat_id=chat_id, text=reply)
    except KeyboardInterrupt:
        print("\nTelegram bot stopped.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Chat with Milu through stdin, one message, or Telegram."
    )
    parser.add_argument(
        "--bot",
        action="store_true",
        help="Run continuously as a Telegram bot.",
    )
    parser.add_argument(
        "message",
        nargs="*",
        help="Process one message and exit.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.bot and args.message:
        raise SystemExit("Do not pass a message together with --bot.")

    try:
        configure_openai()

        if args.bot:
            run_bot()
        elif args.message:
            print(process_message(" ".join(args.message)))
        else:
            run_interactive()
    except RuntimeError as error:
        raise SystemExit(error)


if __name__ == "__main__":
    main()
