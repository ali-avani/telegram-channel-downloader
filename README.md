# Shekan Installer

Python script to download all of media from a Telegram channel in order of upload with extra features.

## Getting Started

Go to [link](https://my.telegram.org/) and create an app. Then get your `api_id` and `api_hash`.

## Installation

Download the scripts:

```
git clone https://github.com/ali-avani/telegram-channel-downloader.git
cd telegram-channel-downloader
```

Edit configuration:

```
cp .env.sample .env
vim .env
```

Run the installer:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```
