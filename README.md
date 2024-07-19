# Telegram Bot for TikTok Video Download

This bot allows you to download TikTok videos directly in the chat with the bot or using inline mode (by tagging the bot in any chat). You can use it here: [@TTtoTG_bot](https://t.me/TTtoTG_bot). Detailed installation instructions are not included here, as users who need them should be able to manage the installation process.

## ⚙️ Before You Start

Before running the bot, please ensure you have the following prerequisites:

1. **Install Requirements:**
   - Install all dependencies listed in the `requirements.txt` file.

2. **Install ffprobe:**
   - Ensure `ffprobe` is installed on your machine.

3. **TikTok Downloader Package:**
   - The bot uses the [tiktok-downloader](https://github.com/krypton-byte/tiktok-downloader) package. Install it from the GitHub repository.

4. **Enable Inline Mode:**
   - Use @BotFather to enable inline mode and turn on inline feedback for your bot.

5. **Setup Private Channel:**
   - Create a private channel for video buffering (necessary for inline mode functionality).
   - Edit all required variables in the `shared.py` file.
