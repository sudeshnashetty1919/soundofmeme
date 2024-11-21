import time
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.loginfortwitter import Login_Page
from pages.GenerateSongs import SoundOfMeme
import config
from selenium.webdriver.chrome.service import Service
import pickle
from webdriver_manager.chrome import ChromeDriverManager

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
    
def load_processed_mentions():
    """
    Load processed mentions from a file.
    Returns a set of processed tagger names.
    """
    if os.path.exists("processed_mentions.json"):
        with open("processed_mentions.json", "r") as file:
            return set(json.load(file))
    return set()


def save_processed_mentions(processed_mentions):
    """
    Save processed tagger names to a file.
    """
    with open("processed_mentions.json", "w") as file:
        json.dump(list(processed_mentions), file)


def reply_to_mention(driver, song_url, tagger_name):
    """
    Reply to a specific mention with the generated song URL.
    """
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

        print(f"Successfully replied to the mention of {tagger_name} with URL: {song_url}")

    except Exception as e:
        print(f"Error replying to the mention for {tagger_name}: {e}")


def main():
    """
    Main function:
    - Logs in to Twitter.
    - Processes mentions by tagger_name.
    """
    
    # Initialize Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    # Go to the login page
    driver.get('https://twitter.com/login')
    login_page = Login_Page(driver)
    # Attempt to load cookies if they exist
    if load_cookie(driver):
        print("Cookies loaded. Refreshing page to maintain session...")
        time.sleep(5)
        driver.refresh()  # Refresh the page to load session cookies
    else:
        print("Cookies not valid or not found, logging in manually.")
        
        login_page.enter_text(login_page.email_input, config.TWITTER_EMAIL)
        login_page.click_element(login_page.next_button)
        
        # Handle phone/username input if asked
        if login_page.is_phone_or_user_name_asked():
            login_page.enter_phone_or_user_name(config.PHONE_OR_USERNAME)
            login_page.click_element(login_page.next_button)
        
        # Enter password and complete login
        login_page.enter_text(login_page.password_input, config.TWITTER_PASSWORD)
        login_page.click_element(login_page.login_button)

        # Wait for the login to complete and verify login success
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Account menu']")))

        # Save cookies after successful login
        save_cookie(driver)
    
    # You can now proceed with your tasks
    print("Logged in successfully.")

    # Perform actions such as checking mentions, replying, etc.

    # Example task - Print out the user's homepage content
    driver.get("https://twitter.com/home")
    print("logged in without email and password")

    """
    # Initialize WebDriver
    driver = webdriver.Chrome()  # Ensure the ChromeDriver is installed and in PATH
    driver.maximize_window()
    driver.get("https://twitter.com/login")

    # Login to Twitter
    login_page = Login_Page(driver)
    login_page.enter_text(login_page.email_input, config.TWITTER_EMAIL)
    login_page.click_element(login_page.next_button)
    if login_page.is_phone_or_user_name_asked():
        login_page.enter_phone_or_user_name(config.PHONE_OR_USERNAME)
        login_page.click_element(login_page.next_button)

    login_page.enter_text(login_page.password_input, config.TWITTER_PASSWORD)
    login_page.click_element(login_page.login_button)
    print("Logged in successfully.")
    """
    # Navigate to mentions
    login_page.click_on_notifications()
    login_page.click_on_mentions()

    # Load already processed mentions
    processed_mentions = load_processed_mentions()
    print("Already processed tagger names:", processed_mentions)

    while True:
        print("Checking for new mentions...")
        mentions = login_page.get_mentions()  # Fetch mentions
        print("Mentions fetched:", mentions)

        if not mentions:
            print("No mentions found. Retrying after a delay.")
            time.sleep(10)
            continue

        new_mentions_found = False

        for mention in mentions:
            try:
                tagger_name = mention["tagger_name"]

                if tagger_name in processed_mentions:
                    print(f"Skipping already processed mention: {tagger_name}")
                    continue

                print(f"Processing mention by {tagger_name}")

                # Click on tagger's name to navigate to their profile
                clicked_name = login_page.click_on_tagger_name(tagger_name)

                if clicked_name and clicked_name.lower() == tagger_name.lower():
                    print(f"Clicked on @{clicked_name}'s profile.")
                    file_path = login_page.take_screenshot(tagger_name)
                    login_page.click_on_back()

                    if file_path is None:
                        print(f"Error: Screenshot not saved for {tagger_name}")
                        continue

                    print(f"Screenshot saved at: {file_path}")

                    # Generate a song using the screenshot
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

                            time.sleep(180)  # Wait for song generation
                            slugs = sound_of_meme.fetch_slugs_for_uploaded_ids(uploaded_ids)

                            if slugs:
                                song_url = slugs[0]  # Use the first generated song URL
                                print(f"Generated song URL: {song_url}")

                                reply_to_mention(driver, song_url, tagger_name)
                                login_page.click_on_back()
                            else:
                                print(f"No song URLs found for {tagger_name}")
                        else:
                            print(f"Upload failed for {tagger_name}")
                    else:
                        print("Login to SoundOfMeme failed.")

                    # Mark as processed
                    processed_mentions.add(tagger_name)
                    new_mentions_found = True
                else:
                    print(f"Could not click on or verify tagger: {tagger_name}")
                    continue

            except Exception as e:
                print(f"Error processing mention for {tagger_name}: {e}")

            # Save processed mentions
            save_processed_mentions(processed_mentions)

        if not new_mentions_found:
            print("No new mentions found. All mentions processed. Exiting.")
            break

        # Optionally wait before rechecking mentions
        time.sleep(10)
    save_cookie(driver)
    # Quit the driver after processing
    driver.quit()

if __name__ == "__main__":
    main()
