
# pages/login_page.py
import os
import time
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle


class Login_Page(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.signup_button= (By.XPATH,"//a[@data-testid='loginButton']")
        self.email_input = (By.XPATH, "//input[@name='text']")
        self.password_input = (By.XPATH, "//input[@type='password']")
        self.next_button = (By.XPATH, "//span[contains(text(),'Next')]")
        self.login_button = (By.XPATH, "//span[contains(text(),'Log in')]")
        self.phone_number_user_name = (By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")
        self.notifications = (By.XPATH, "//a[@href='/notifications']")
        self.tagger_name = (By.XPATH, "//a[contains(@class, 'r-dnmrzs')]/div/span")
        self.screen_for_shot = (By.XPATH, "(//div[@class='css-175oi2r'])[16]")
        self.mentions = (By.XPATH, "//span[contains(text(),'Mentions')]")
        self.screenshot_dir = os.path.join(os.getcwd(), "twitterBot", "screenshots")
        self.back_from_profile = (By.XPATH, "//button[@aria-label='Back']")
        self.notifications_number= (By.XPATH,"//div[contains(@aria-label,'unread items')]//span")
        self.profile_icon = (By.XPATH, "//button[@aria-label='Account menu']")

    def signup(self):
        self.click_element(self.signup_button)
    
    def login(self, email, password):
        """Log in to Twitter using email and password."""
        self.enter_text(self.email_input, email)
        self.click_element(self.next_button)
        self.enter_text(self.password_input, password)
        self.click_element(self.login_button)
        print("Logged in successfully.")

    def is_phone_or_user_name_asked(self):
        """Check if Twitter prompts for phone number or username."""
        try:
            WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located(self.phone_number_user_name)
            )
            return True
        except Exception:
            print("Phone number or username input not requested.")
            return False

    def enter_phone_or_user_name(self, content):
        """Enter phone number or username if prompted."""
        self.enter_text(self.phone_number_user_name, content)

    def click_on_notifications(self):
        """Click on the Notifications button."""
        time.sleep(10)
        self.wait_for_element(self.notifications).click()

    def click_on_mentions(self):
        """Click on the Mentions button."""
        time.sleep(10)
        self.wait_for_element(self.mentions).click()
        

    def click_on_tagger_name(self, tagger_name):
        """
        Click on the tagger's name element and return its text.
        """
        try:
            # Dynamically construct the XPath for the tagger's name
            tagger_xpath = f"//span[contains(text(),'{tagger_name}')]"
            
            # Find the WebElement using the XPath
            tagger_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, tagger_xpath))
            )

            # Extract and sanitize the tagger's name text
            tagger_text = tagger_element.text.strip()
            print(f"Found tagger: {tagger_text}")

            # Perform the click action
            tagger_element.click()
            return tagger_text
        except Exception as e:
            print(f"Error clicking on tagger name or retrieving text: {e}")
            return None

    def take_screenshot(self, tagger_name):
        time.sleep(5)
        try:
            element = self.wait_for_element(self.screen_for_shot)
            if element is None:
                print("Element not found. Cannot take screenshot.")
                return None

            # Take a screenshot of the element
            screenshot_name = f"{''.join(e for e in tagger_name if e.isalnum() or e in (' ', '_', '-'))}.png"
            screenshot_path = os.path.join(self.screenshot_dir, screenshot_name)

            # Ensure screenshot directory exists
            if not os.path.exists(self.screenshot_dir):
                os.makedirs(self.screenshot_dir)

            # Save the screenshot
            element.screenshot(screenshot_path)
            print(f"Screenshot saved as: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
    """
    def get_mentions(self, count=0):
    
        mentions = []
        try:
            # Locate all tweets in the mentions section
            tweets = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")

            for index, tweet in enumerate(tweets[:count]):  # Limit to the provided count
                try:
                    tagger_element = tweet.find_element(By.XPATH, ".//a[contains(@class, 'r-dnmrzs')]/div/span")
                    tagger_name = tagger_element.text
                    mentions.append({"index": index, "tagger_name": tagger_name})
                except Exception as inner_e:
                    print(f"Error extracting tagger name from tweet at index {index}: {inner_e}")
        except Exception as e:
            print(f"Error fetching mentions: {e}")

        return mentions
    """
    def get_mentions(self, unread_count):
        try:
            # Wait for mentions to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//article[@data-testid='tweet']"))
            )
            mentions_elements = self.driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
            print(f"Found {len(mentions_elements)} mention elements.")

            # Limit to unread notifications
            mentions_elements = mentions_elements[:unread_count]
            print(f"Processing the first {len(mentions_elements)} mentions.")

            mentions = []
            for element in mentions_elements:
                try:
                    tagger_name = element.find_element(By.XPATH, ".//a[contains(@class, 'r-dnmrzs')]/div/span").text
                    print(f"Tagger name found: {tagger_name}")
                    mentions.append({"tagger_name": tagger_name})
                except Exception as e:
                    print(f"Error extracting tagger name: {e}")
                    continue
            return mentions
        except Exception as e:
            print(f"Error fetching mentions: {e}")
            return []

    def click_on_back(self):
        # Navigate back to the previous page (mentions page)
        try:
            back_element = self.driver.find_element(*self.back_from_profile)
            back_element.click()
            time.sleep(2)  # Wait for the page to load back
        except Exception as e:
            print(f"Error clicking on 'Back' button: {e}")

    def fetch_all_tweets_with_scroll(driver, max_scrolls=20, scroll_pause=2):
        time.sleep(scroll_pause)
        tweets = []
        last_height = driver.execute_script("return document.body.scrollHeight")

        for scroll_count in range(max_scrolls):
            print(f"Scrolling {scroll_count + 1}/{max_scrolls}...")
            tweet_elements = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")

            for index, tweet_element in enumerate(tweet_elements):
                try:
                    tweet_text = tweet_element.text
                    tweets.append(tweet_text)
                    #print(f"Tweet {len(tweets)}: {tweet_text}")
                except Exception as e:
                    print(f"Error fetching text for tweet {index + 1}: {e}")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Reached the bottom of the page.")
                break
            last_height = new_height

        return tweets

    def get_unread_notifications(self):
        """
        Fetch the number of unread notifications.
        """
        try:
            # Wait for the element containing the unread notifications to be visible
            unread_notifications_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label,'unread items')]//span"))
                    )
            
            # If the element is found, try to fetch the unread notification count
            unread_text = unread_notifications_element.text.strip()
            print(unread_text)
            # Check if the unread count is a number or not
            if unread_text.isdigit():
                unread_count = int(unread_text)
            else:
                unread_count = 0  # No unread notifications

            print(f"Unread notifications: {unread_count}")
            return unread_count

        except Exception as e:
            print(f"Error fetching unread notifications: {e}")
            return 0

    def is_logged_in(self):
        try:
            # Check if the profile icon is present to confirm login
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.profile_icon)
            )
            return True
        except:
            return False
    def perform_login_with_cookies(self, driver):
        """Logs in to Twitter using saved cookies."""
        try:
            # Load cookies from a file
            with open("cookies.pkl", "rb") as file:
                cookies = pickle.load(file)

            for cookie in cookies:
                driver.add_cookie(cookie)

            # Refresh the page to apply cookies
            driver.refresh()
            print("Login successful using cookies.")

        except FileNotFoundError:
            print("Cookies file not found. Please log in manually to save cookies.")
        except Exception as e:
            print(f"Error logging in with cookies: {e}")

    def save_cookies(driver, file_path):
        """Saves cookies to a file after manual login."""
        with open(file_path, "wb") as file:
            pickle.dump(driver.get_cookies(), file)

#//span[contains(text(),'@SSudesshna66398')]//ancestor::div[contains(@class,'r-kzbkwu')]
