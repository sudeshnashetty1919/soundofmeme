import os
import time
import json
import pickle
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


def save_cookie(driver):
    """ Save cookies to a file. """
    with open("cookie.pkl", 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)


def load_cookie(driver):
    """ Load cookies from a file. """
    if os.path.exists("cookie.pkl"):
        with open("cookie.pkl", 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                driver.add_cookie(cookie)
        return True
    return False


def load_reply_log():
    """Load the reply log from a file."""
    if os.path.exists("reply_log.json"):
        with open("reply_log.json", "r") as file:
            return json.load(file)
    return {}


def save_reply_log(reply_log):
    """Save the reply log to a file."""
    with open("reply_log.json", "w") as file:
        json.dump(reply_log, file, indent=4)


def reply_to_mention(driver, song_url, tagger_name):
    """Reply to the second consecutive mention from a specific account with the generated song URL."""
    try:
        # XPath to locate the second consecutive mention from the same account
        reply_button_xpath = f"//span[contains(text(),'{tagger_name}')]//ancestor::div[contains(@class,'r-kzbkwu')]"
        
        # Wait for the reply button of the second mention to be clickable
        reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, reply_button_xpath))
        )
        reply_button.click()

        # Wait for the reply input to be visible
        reply_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']"))
        )
        reply_input.send_keys(song_url)

        # Wait for the post reply button to be clickable
        post_reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='tweetButtonInline']"))
        )
        post_reply_button.click()

        print(f"Successfully replied to the second mention of {tagger_name} with URL: {song_url}")

        return {"song_url": song_url, "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    except Exception as e:
        print(f"Error replying to the mention for {tagger_name}: {e}")
        return None


def process_mentions(driver, login_page, sound_of_meme, reply_log):
    """Process unread mentions and reply."""
    unread_count = login_page.get_unread_notifications()
    print(f"Unread mentions to process: {unread_count}")

    if unread_count == 0:
        return

    login_page.click_on_notifications()
    time.sleep(5)
    login_page.click_on_mentions()
    time.sleep(10)
    login_page.click_on_notifications()
    time.sleep(5)
    login_page.click_on_mentions()
    time.sleep(10)
    driver.refresh()

    mentions_processed = 0

    while mentions_processed < unread_count:
        mentions = login_page.get_mentions(unread_count)
        if not mentions:
            break

        for mention in mentions:
            if mentions_processed >= unread_count:
                break

            tagger_name = mention["tagger_name"]
            print(f"Processing mention by {tagger_name}")

            clicked_name = login_page.click_on_tagger_name(tagger_name)
            if clicked_name:
                file_path = login_page.take_screenshot(tagger_name)
                login_page.click_on_back()

                if file_path:
                    token = sound_of_meme.login(
                        name="Sudeshna Shetty",
                        email="sudeshnashetty2211@gmail.com",
                        picture_url="https://lh3.googleusercontent.com/a/ACg8ocLA7Y24F3ZGv4-l_gpYhumZ2MgrvQKlqwHT3D-AG7wadKA3Lg=s96-c",
                    )

                    if token:
                        uploaded_data = sound_of_meme.upload_image(file_path)
                        if uploaded_data and "songs" in uploaded_data:
                            uploaded_ids = [int(id_str) for id_str in uploaded_data["songs"].split(",")]
                            time.sleep(240)
                            slugs = sound_of_meme.fetch_slugs_for_uploaded_ids(uploaded_ids)

                            if slugs:
                                song_url = slugs[0]
                                reply_details = reply_to_mention(driver, song_url, tagger_name)
                                if reply_details:
                                    reply_log.setdefault(tagger_name, []).append(reply_details)
                                    save_reply_log(reply_log)
            mentions_processed += 1


def main():
    """Main function to continuously process Twitter mentions."""
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    driver.get('https://twitter.com/login')
    login_page = Login_Page(driver)

    if load_cookie(driver):
        print("Cookies loaded. Refreshing page to maintain session...")
        time.sleep(10)
        driver.refresh()
    else:
        print("Cookies not found, logging in manually.")
        login_page.enter_text(login_page.email_input, config.TWITTER_EMAIL)
        login_page.click_element(login_page.next_button)

        if login_page.is_phone_or_user_name_asked():
            login_page.enter_phone_or_user_name(config.PHONE_OR_USERNAME)
            login_page.click_element(login_page.next_button)

        login_page.enter_text(login_page.password_input, config.TWITTER_PASSWORD)
        login_page.click_element(login_page.login_button)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Account menu']"))
        )
        save_cookie(driver)

    print("Logged in successfully.")
    reply_log = load_reply_log()
    sound_of_meme = SoundOfMeme()

    try:
        while True:
            print("Checking for new mentions...")
            process_mentions(driver, login_page, sound_of_meme, reply_log)
            driver.get("https://twitter.com/home")
            print("Waiting 5 minutes before checking again...")
            time.sleep(300)
    except KeyboardInterrupt:
        print("Stopping script.")
    finally:
        save_cookie(driver)
       


if __name__ == "__main__":
    main()
