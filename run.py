from bw_secrets import BOT_TOKEN
from bot import BOT
import logging


def main():
    """ Setup bot intents and cogs and bring General Walarus to life """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    BOT.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
