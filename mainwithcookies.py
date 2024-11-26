import time
import os
import json
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
from selenium.webdriver.chrome.options import Options
import config
import pickle

os.environ["PATH"] += os.pathsep + "/usr/local/bin"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("script.log"),
        logging.StreamHandler()
    ]
)

def save_cookie(driver):
    """ Save cookies to a file. """
    with open("cookie.pkl", 'wb') as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)
        logging.info("Cookies saved successfully.")

def load_cookie(driver):
    """ Load cookies from a file. """
    if os.path.exists("cookie.pkl"):
        with open("cookie.pkl", 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                driver.add_cookie(cookie)
        logging.info("Cookies loaded successfully.")
        return True
    logging.warning("No cookies found.")
    return False

def load_reply_log():
    """Load the reply log from a file."""
    if os.path.exists("reply_log.json"):
        with open("reply_log.json", "r") as file:
            logging.info("Reply log loaded.")
            return json.load(file)
    logging.info("No reply log found. Starting fresh.")
    return {}

def save_reply_log(reply_log):
    """Save the reply log to a file."""
    with open("reply_log.json", "w") as file:
        json.dump(reply_log, file, indent=4)
        logging.info("Reply log saved.")

def reply_to_mention(driver, song_url, tagger_name):
    """Reply to a specific mention with the generated song URL."""
    try:
        reply_button_xpath = f"//span[contains(text(),'{tagger_name}')]//ancestor::div[contains(@class,'r-kzbkwu')]"
        reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, reply_button_xpath))
        )
        reply_button.click()

        # Wait for the reply input field
        reply_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']"))
        )
        reply_input.send_keys(song_url)  # Enter the song URL

        # Wait for the post reply button to be clickable
        post_reply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='tweetButtonInline']"))
        )
        post_reply_button.click()

        logging.info(f"Successfully replied to the mention of {tagger_name} with URL: {song_url}")

        # Log the reply details
        return {"song_url": song_url, "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    except Exception as e:
        logging.error(f"Error replying to the mention for {tagger_name}: {e}")
        return None

def main():
    """
    Main function:
    - Logs in to Twitter.
    - Processes the first `n` mentions based on the unread notification count.
    """
    # Initialize Chrome WebDriver
    # Set up Chrome options for headless mode and required flags
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox")  # Disable sandboxing (needed for Docker)
    options.add_argument("--disable-dev-shm-usage")  # Disable /dev/shm usage
    options.add_argument("--remote-debugging-port=9222")  # Allow debugging on a given port
    logging.info("Initializing WebDriver.")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    driver.get('https://twitter.com/login')
    login_page = Login_Page(driver)

    # Attempt to load cookies if they exist
    if load_cookie(driver):
        logging.info("Cookies loaded. Refreshing page to maintain session...")
        time.sleep(10)
        driver.refresh()
    else:
        logging.info("Cookies not valid or not found, logging in manually.")
        login_page.enter_text(login_page.email_input, config.TWITTER_EMAIL)
        login_page.click_element(login_page.next_button)

        # Handle phone/username input if asked
        if login_page.is_phone_or_user_name_asked():
            login_page.enter_phone_or_user_name(config.PHONE_OR_USERNAME)
            login_page.click_element(login_page.next_button)

        login_page.enter_text(login_page.password_input, config.TWITTER_PASSWORD)
        login_page.click_element(login_page.login_button)

        # Wait for the login to complete
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Account menu']")))
        save_cookie(driver)

    logging.info("Logged in successfully.")
    driver.get("https://twitter.com/home")

    print("Logged in to the homepage.")
    time.sleep(30)

    unread_count = login_page.get_unread_notifications()
    print(f"Unread mentions to process: {unread_count}")

    login_page.click_on_notifications()
    time.sleep(5)
    login_page.click_on_mentions()
    time.sleep(10)
    driver.refresh()
    login_page.click_on_notifications()
    time.sleep(5)
    login_page.click_on_mentions()

    reply_log = load_reply_log()
    print("Reply log loaded.")

    mentions_processed = 0

    while mentions_processed < unread_count:
        print(f"Checking for new mentions... ({mentions_processed + 1}/{unread_count})")
        mentions = login_page.get_mentions(unread_count)

        if not mentions:
            print("No mentions found. Retrying after a delay.")
            time.sleep(10)
            unread_count = login_page.get_unread_notifications()
            print("from if in while loop")
            continue

        for mention in mentions:
            if mentions_processed >= unread_count:
                break

            try:
                tagger_name = mention["tagger_name"]
                print(f"Processing mention by {tagger_name}")

                clicked_name = login_page.click_on_tagger_name(tagger_name)

                if clicked_name:
                    print(f"Clicked on @{clicked_name}'s profile.")
                    file_path = login_page.take_screenshot(tagger_name)
                    login_page.click_on_back()

                    if not file_path:
                        print(f"Error: Screenshot not saved for {tagger_name}")
                        continue

                    print(f"Screenshot saved at: {file_path}")

                    sound_of_meme = SoundOfMeme()
                    token = sound_of_meme.login(
                        name="Sudeshna Shetty",
                        email="sudeshnashetty2211@gmail.com",
                        picture_url="https://lh3.googleusercontent.com/a/ACg8ocLA7Y24F3ZGv4-l_gpYhumZ2MgrvQKlqwHT3D-AG7wadKA3Lg=s96-c",
                    )

                    if token:
                        uploaded_data = sound_of_meme.upload_image(file_path)
                        if uploaded_data and "songs" in uploaded_data:
                            uploaded_ids = [int(id_str) for id_str in uploaded_data["songs"].split(",")]
                            print(f"Uploaded IDs: {uploaded_ids}")

                            time.sleep(240)
                            slugs = sound_of_meme.fetch_slugs_for_uploaded_ids(uploaded_ids)

                            if slugs:
                                song_url = slugs[0]
                                print(f"Generated song URL: {song_url}")

                                reply_details = reply_to_mention(driver, song_url, tagger_name)
                                if reply_details:
                                    reply_log.setdefault(tagger_name, []).append(reply_details)
                                    save_reply_log(reply_log)
                            else:
                                print(f"No song URLs found for {tagger_name}")
                        else:
                            print(f"Upload failed for {tagger_name}")
                    else:
                        print("Login to SoundOfMeme failed.")
                else:
                    print(f"Could not click on or verify tagger: {tagger_name}")

            except Exception as e:
                print(f"Error processing mention for {tagger_name}: {e}")

            mentions_processed += 1

        if mentions_processed < unread_count:
            print("Waiting before checking for new mentions...")
            time.sleep(10)

    print("Processed all unread mentions. Exiting.")
    save_cookie(driver)
    driver.quit()

if __name__ == "__main__":
    main()
