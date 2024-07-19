import os
import telebot

from pathlib import Path
from loguru import logger
from telebot import types
from tiktokWorker import TiktokDL, fetch_tt_data, is_tiktok_link

import shared

# Set up logging
logs_path = Path().absolute() / "logs" / "bot.log"
logger.add(logs_path.absolute(), rotation="5 MB")

# Initialize the bot and TikTok downloader
bot = telebot.TeleBot(shared.bot_token)
my_tiktok = TiktokDL()


# Handler for /start command
@logger.catch()
@bot.message_handler(commands=["start"])
def send_welcome(message):
    logger.debug("Start message from user {}".format(message.from_user.id))
    bot.reply_to(
        message,
        "<b>Hello!</b>\nI am a <b>TikTok video downloader</b> bot.\nYou can run me <b>in any chat</b> using <b>@{}</b> (inline)\nAlso, you can <b>just send me video link</b> for download!".format(
            bot.get_me().username
        ),
        parse_mode="HTML",
    )


# Handler for tiktok video links
@logger.catch()
@bot.message_handler(func=lambda message: True)
def download_tiktok(message):
    # Check if the message is a TikTok video link
    tiktok_link = is_tiktok_link(message.text)
    if tiktok_link:
        logger.debug(
            "Download request from user {}: {}".format(
                message.from_user.id, tiktok_link
            )
        )

        # Start video download
        bot.send_chat_action(message.chat.id, "record_video")
        result = my_tiktok.download_video(tiktok_link)
        # On success, send the video to the chat
        if result:
            # Try to fetch video data
            try:
                author, descr = fetch_tt_data(tiktok_link)
                logger.debug("Author: [{}], Description: [{}]".format(author, descr))
                description = "👤 <b>{}</b>\n📃 <i>{}</i>\n\n".format(author, descr)
            except Exception as e:
                logger.error("Cannot fetch video data: {}".format(e))
                description = ""

            # Send the video to the chat
            with open(result, "rb") as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption='{}📺 <a href="{}">TikTok</a> <b>downloaded</b> successfully!'.format(
                        description, tiktok_link
                    ),
                    parse_mode="HTML",
                )

            # Remove the local video file
            try:
                os.remove(result)
            except Exception as e:
                logger.error("Cannot remove file {}: {}".format(result, e))
        else:
            # Apologize on download failure
            bot.reply_to(message, "😟 Download failed, <b>sorry</b>", parse_mode="HTML")


# Handler for inline queries
@logger.catch()
@bot.inline_handler(func=lambda query: True)
def query_video(query):
    # Check if the query is a TikTok video link
    tiktok_link = is_tiktok_link(query.query)
    if tiktok_link:
        logger.debug(
            "Inline query [{}] from user {}".format(tiktok_link, query.from_user.id)
        )
        try:
            # Create an inline keyboard with a button
            # Without a button we can't handle the chosen_inline_result
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton(
                text="Downloading...", callback_data="000"
            )
            markup.add(button)

            # Try to fetch video data
            try:
                author, descr = fetch_tt_data(tiktok_link)
                logger.debug("Author: [{}], Description: [{}]".format(author, descr))
                description = "{} | {}".format(author, descr)
            except Exception as e:
                logger.error("Cannot fetch video data: {}".format(e))
                description = tiktok_link

            # Form the inline query result
            r = types.InlineQueryResultVideo(
                id="1",
                video_url=shared.video_url,
                mime_type="video/mp4",
                thumbnail_url=shared.thumb_url,
                title="Download tiktok video",
                description=description,
                caption="⚙️ Download in progress...",
                reply_markup=markup,
            )

            bot.answer_inline_query(query.id, [r])
        except Exception as e:
            logger.error("Cannot answer inline query: {}".format(e))


# Handler for chosen inline results
@logger.catch()
@bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
def chosen_inline(chosen_inline_result):
    logger.debug("Chosen inline result: {}".format(chosen_inline_result.query))
    # Try to download the video
    try:
        result = my_tiktok.download_video(chosen_inline_result.query)
        if result:
            # Upload the local video to the buffer channel
            # (you can't edit the inline message with a video from the local file)
            with open(result, "rb") as video:
                sent_message = bot.send_video(shared.channel_id, video)

            # Try to fetch video data
            try:
                author, descr = fetch_tt_data(chosen_inline_result.query)
                logger.debug("Author: [{}], Description: [{}]".format(author, descr))
                description = "👤 <b>{}</b>\n📃 <i>{}</i>\n\n".format(author, descr)
            except Exception as e:
                logger.error("Cannot fetch video data: {}".format(e))
                description = ""

            # Get the file ID of the uploaded video
            file_id = sent_message.video.file_id

            # Edit the inline message to replace the video using the file ID
            media = types.InputMediaVideo(
                media=file_id,
                caption='{}📺 <a href="{}">TikTok</a> <b>downloaded</b> successfully!'.format(
                    description, chosen_inline_result.query
                ),
                parse_mode="HTML",
            )

            bot.edit_message_media(
                media=media, inline_message_id=chosen_inline_result.inline_message_id
            )

            # Remove the local video file
            try:
                os.remove(result)
            except Exception as e:
                logger.error("Cannot remove file {}: {}".format(result, e))
        else:
            # Apologize on download failure
            logger.error("Download failed: {}".format(chosen_inline_result.query))
            bot.edit_message_caption(
                caption="😟 Download failed, <b>sorry</b>\n👁‍🗨 Video link: {}".format(
                    chosen_inline_result.query
                ),
                inline_message_id=chosen_inline_result.inline_message_id,
                parse_mode="HTML",
            )
    except Exception as e:
        # Apologize on download error
        logger.error("Cannot download video: {}".format(e))
        bot.edit_message_caption(
            caption="😟 Download failed, <b>sorry</b>\n👁‍🗨 Video link: {}".format(
                chosen_inline_result.query
            ),
            inline_message_id=chosen_inline_result.inline_message_id,
            parse_mode="HTML",
        )


# Main entry point
if __name__ == "__main__":
    logger.info("Bot started!")
    bot.polling(non_stop=True)
