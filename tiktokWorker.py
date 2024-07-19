import os
import re
import random
import string
import datetime
import requests
import subprocess

from pathlib import Path
from loguru import logger


# Check if the link is a TikTok video
def is_tiktok_link(link):
    reg = r"(https:\/\/[0-9\/A-Za-z\.]+)"
    tiktok_link = re.findall(reg, link)
    if tiktok_link and "tiktok.com" in tiktok_link[0]:
        return tiktok_link[0]
    else:
        return False


# Generate a random filename
def generate_random_filename():
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S")
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    filename = timestamp + "_" + random_string
    return filename


# Remove hashtags from the text
def remove_hashtags(text):
    pattern = r"#\S+"
    cleaned_text = re.sub(pattern, "", text)
    cleaned_text = " ".join(cleaned_text.split())
    return cleaned_text


# Fetch TikTok video data (author and description)
def fetch_tt_data(url):
    r = requests.get(url)
    name_regex = r"\"authorName\":\"([^\"]+)\""
    desc_regex = r"\"desc\":\"([^\"]+)\""

    name = re.findall(name_regex, r.text)
    desc = re.findall(desc_regex, r.text)

    return name[0], remove_hashtags(desc[0])


# A bit redefined TiktokDL class
class TiktokDL:
    def download_video(self, tiktok_link):
        if not os.path.isdir("tiktoks"):
            os.mkdir("tiktoks")
        file_name = str(
            Path("tiktoks", "{}.mp4".format(generate_random_filename())).absolute()
        )

        # These providers seem to work
        providers = [
            self.__download_snaptik,
            self.__download_tiktok,
            self.__download_tikwm,
            self.__download_tikdown,
        ]
        # random.shuffle(providers)

        # Trying to download video using different providers
        for provider in providers:
            try:
                logger.debug(
                    "Downloading {} using {}".format(tiktok_link, provider.__name__)
                )
                provider(tiktok_link, str(file_name))

                # We have to check if the downloaded file is a valid video, unfortunately
                result = subprocess.run(
                    ["ffprobe", file_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if result.returncode == 0:
                    result = subprocess.getoutput("ffprobe {}".format(file_name))
                    if (
                        "Duration: N/A" not in result
                        and "Estimating duration from bitrate" not in result
                    ):
                        # If the downloaded file is a valid video, return its name
                        logger.debug(
                            "Downloaded video: [{}] -> [{}]".format(
                                tiktok_link, file_name
                            )
                        )
                        return file_name

                # If the downloaded file is not a valid video, remove it
                if os.path.exists(file_name):
                    try:
                        os.remove(file_name)
                    except Exception as ex:
                        logger.error("Cannot remove file {}: {}".format(file_name, ex))

            except Exception as ex:
                logger.debug(
                    "Cannot download video through {}: {}".format(provider.__name__, ex)
                )

        return False

    def __download_snaptik(self, link, path):
        from tiktok_downloader import snaptik

        d = snaptik(link)
        d[0].download(path)

    def __download_musically(self, link, path):
        from tiktok_downloader import mdown

        d = mdown(link)
        print(d)
        d[0].download(path)

    def __download_tikdown(self, link, path):
        from tiktok_downloader import tikdown

        d = tikdown(link)
        d[0].download(path)

    def __download_tikwm(self, link, path):
        from tiktok_downloader import tikwm

        d = tikwm(link)
        d[0].download(path)

    def __download_tiktok(self, link, path):
        from tiktok_downloader import VideoInfo

        d = VideoInfo.service(link)
        d[0].download(path)
