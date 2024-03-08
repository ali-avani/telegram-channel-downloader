import argparse
import asyncio
import mimetypes
import os
import pickle
from pathlib import Path

from dotenv import dotenv_values
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from tqdm import tqdm

config = dotenv_values(".env")

API_ID = config.get("API_ID")
API_HASH = config.get("API_HASH")
CHANNEL_ID = int(config.get("CHANNEL_ID"))
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
MEDIA_PATH = f"{BASE_DIR}/medias"
MEDIA_SAVE_FILE_NAME = "saved_medias"


loop = asyncio.get_event_loop()
client = TelegramClient("tcmc_session", API_ID, API_HASH)
channel = None

show_chats = False
start_id = None
end_id = None
ignore_database = False
dry_run = False

Path(MEDIA_PATH).mkdir(parents=True, exist_ok=True)


class MediaDB:
    filename = None
    _saved_medias = []

    def __init__(self, filename):
        self.filename = filename
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as fp:
                self._saved_medias = set(pickle.load(fp))
        else:
            self._saved_medias = set()

    @property
    def saved_medias(self):
        return self._saved_medias

    @saved_medias.setter
    def saved_medias(self, value):
        with open(self.filename, "wb") as fp:
            pickle.dump(value, fp)
        return self._saved_medias

    def add_media(self, media):
        self._saved_medias.add(media)
        self.saved_medias = self._saved_medias

    def clean_media(self):
        self.saved_medias = set()


class ProgressBar(tqdm):
    async def update_to(self, current, total):
        self.total = total
        self.update(current - self.n)


def display_upload_info(files):
    print(", ".join([file.split("/")[-1] for file in files]))


def get_message_link(message):
    return f"https://t.me/c/{channel.id}/{message.id}"


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


async def main():
    global channel
    media_db = MediaDB(MEDIA_SAVE_FILE_NAME)
    await client.start()
    if show_chats:
        async for dialog in client.iter_dialogs():
            print(f"{dialog.name}: {dialog.entity.id}")
        return

    messages = []
    channel = await client.get_entity(PeerChannel(CHANNEL_ID))
    async for message in client.iter_messages(PeerChannel(CHANNEL_ID), reverse=True):
        file = message.document or message.photo
        if (
            (start_id and message.id < start_id)
            or (end_id and message.id > end_id)
            or not file
            or (not ignore_database and file.id in media_db.saved_medias)
        ):
            continue
        messages.append(message)

    if dry_run:
        for message in messages:
            print(f"{message.id}: {get_message_link(message)}")
        return

    try:
        for message in messages:
            print("Downloading:", message.id)
            message = await client.get_messages(CHANNEL_ID, ids=message.id)
            file = message.document or message.photo
            original_filename = getattr(
                file.attributes[0],
                "file_name",
                f"{file.id}{mimetypes.guess_extension(file.mime_type)}",
            ).replace(" ", "_")
            filename = f"{message.id}_{original_filename}"
            filepath_prefix = f"{MEDIA_PATH}/{filename}"
            await client.download_media(
                message,
                filepath_prefix,
                progress_callback=ProgressBar(unit="B", unit_scale=True).update_to,
            )
            media_db.add_media(file.id)
    finally:
        print("Done")
        print()


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--show-chats", action="store_true", help="Show all chats")
    parser.add_argument("-c", "--clean-channel", action="store_true", help="Clean channel all messages")
    parser.add_argument("-s", "--start-id", type=check_positive, help="Start from message id")
    parser.add_argument("-e", "--end-id", type=check_positive, help="End at message id")
    parser.add_argument("-d", "--ignore-database", action="store_true", help="Ignore media database")
    parser.add_argument("--dry-run", action="store_true", help="Dry run and only show messages")
    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    if args.show_chats:
        show_chats = True
    if args.clean_channel:
        clean_channel = True
    if args.start_id:
        start_id = args.start_id
    if args.end_id:
        end_id = args.end_id
    if args.ignore_database:
        ignore_database = True
    if args.dry_run:
        dry_run = True

    loop.run_until_complete(main())
