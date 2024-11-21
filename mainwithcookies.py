import os
import time
import json
import pickle
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pages.loginfortwitter import Login_Page
from pages.GenerateSongs import SoundOfMeme
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("script.log"),
        logging.StreamHandler()
    ]
)

class CookieManager:
    """Handles saving and loading of cookies."""
    
    @staticmethod
    def save_cookies(driver):
        with open("cookie.pkl", 'wb') as filehandler:
            pickle.dump(driver.get_cookies(), filehandler)
        logging.info("Cookies saved successfully.")

    @staticmethod
    def load_cookies(driver):
        if os.path.exists("cookie.pkl"):
            with open("cookie.pkl", 'rb') as cookiesfile:
                cookies = pickle.load(cookiesfile)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            logging.info("Cookies loaded successfully.")
            return True
        logging.warning("No cookies file found.")
        return False

class ReplyLogManager:
    """Handles saving and loading of reply logs."""
    
    @staticmethod
    def load_log():
        if os.path.exists("reply_log.json"):
            with open("reply_log.json", "r") as file:
                logging.info("Reply log loaded.")
                return json.load(file)
        logging.info("No reply log found. Starting fresh.")
        return {}

    @staticmethod
    def save_log(reply_log):
        with open("reply_log.json", "w") as file:
            json.dump(reply_log, file, indent=4)
        logging.info("Reply log saved.")

class TwitterBot:
    """Handles login and interactions with Twitter."""
    
    def __init__(self, driver):
        self.driver = driver
        self.login_page = Login_Page(driver)

    def login(self):
        """Attempts to log in using cookies or manual credentials."""
        if CookieManager.load_cookies(self.driver):
            logging.info("Cookies loaded. Refreshing page to maintain session...")
            time.sleep(5)
            self.driver.refresh()
        else:
            logging.info("Cookies not found or invalid. Logging in manually.")
            self.manual_login()
            CookieManager.save_cookies(self.driver)

    def manual_login(self):
        """Performs manual login with credentials."""
        self.login_page.enter_text(self.login_page.email_input, config.TWITTER_EMAIL)
        self.login_page.click_element(self.login_page.next_button)

        # Handle username/phone input if prompted
        if self.login_page.is_phone_or_user_name_asked():
            self.login_page.enter_phone_or_user_name(config.PHONE_OR_USERNAME)
            self.login_page.click_element(self.login_page.next_button)

        self.login_page.enter_text(self.login_page.password_input, config.TWITTER_PASSWORD)
        self.login_page.click_element(self.login_page.login_button)

        # Wait for login to complete
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Account menu']")))
        logging.info("Logged in successfully.")

    def get_mentions(self, unread_count):
        """Fetches mentions from unread notifications."""
        return self.login_page.get_mentions(unread_count)

    def reply_to_mention(self, song_url, tagger_name):
        """Replies to a specific mention with the generated song URL."""
        try:
            reply_button_xpath = f"//span[contains(text(),'{tagger_name}')]//ancestor::div[contains(@class,'r-kzbkwu')]"
            reply_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, reply_button_xpath))
            )
            reply_button.click()

            reply_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']"))
            )
            reply_input.send_keys(song_url)

            post_reply_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='tweetButtonInline']"))
            )
            post_reply_button.click()

            logging.info(f"Successfully replied to the mention by {tagger_name} with URL: {song_url}")
            return {"song_url": song_url, "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        except Exception as e:
            logging.error(f"Error replying to mention for {tagger_name}: {e}")
            return None

class SoundOfMemeHandler:
    """Handles interactions with SoundOfMeme API."""
    
    @staticmethod
    def process_song(file_path, tagger_name):
        sound_of_meme = SoundOfMeme()
        token = sound_of_meme.login("Sudeshna Shetty", "sudeshnashetty2211@gmail.com", "https://example.com/profile.jpg")

        if token:
            uploaded_data = sound_of_meme.upload_image(file_path)
            if uploaded_data and "songs" in uploaded_data:
                uploaded_ids = [int(id_str) for id_str in uploaded_data["songs"].split(",")]
                time.sleep(240)  # Wait for processing
                slugs = sound_of_meme.fetch_slugs_for_uploaded_ids(uploaded_ids)
                if slugs:
                    return slugs[0]
        logging.error(f"Failed to process song for {tagger_name}.")
        return None

def main():
    # Initialize WebDriver
    logging.info("Initializing WebDriver.")
    service = Service(ChromeDriverManager().install())
    service = Service("/root/.wdm/drivers/chromedriver/linux64/131.0.6778.85/chromedriver")
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    twitter_bot = TwitterBot(driver)
    twitter_bot.login()

    unread_count = twitter_bot.login_page.get_unread_notifications()
    logging.info(f"Unread mentions to process: {unread_count}")

    reply_log = ReplyLogManager.load_log()
    mentions_processed = 0

    while mentions_processed < unread_count:
        mentions = twitter_bot.get_mentions(unread_count)
        for mention in mentions:
            tagger_name = mention["tagger_name"]
            file_path = twitter_bot.login_page.take_screenshot(tagger_name)
            if not file_path:
                continue

            song_url = SoundOfMemeHandler.process_song(file_path, tagger_name)
            if song_url:
                reply_details = twitter_bot.reply_to_mention(song_url, tagger_name)
                if reply_details:
                    reply_log.setdefault(tagger_name, []).append(reply_details)
                    ReplyLogManager.save_log(reply_log)

            mentions_processed += 1
        time.sleep(10)  # Avoid spamming requests

    logging.info("Processed all mentions. Exiting.")
    driver.quit()

if __name__ == "__main__":
    main()
