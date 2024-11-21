import requests
import time

class SoundOfMeme:
    def __init__(self):
        self.login_url = "https://testapi.soundofmeme.com/googlelogin"
        self.upload_url = "https://engine.soundofmeme.com/image"
        self.usersongs_url = "https://testapi.soundofmeme.com/usersongs"
        self.access_token = None

    def login(self, name, email, picture_url):
        payload = {"name": name, "email": email, "picture": picture_url}

        try:
            response = requests.post(self.login_url, json=payload)
            response.raise_for_status()
            response_data = response.json()

            if "access_token" in response_data:
                self.access_token = response_data["access_token"]
                print(f"Login successful! Access Token: {self.access_token}")
                return self.access_token
            else:
                print("Login failed! Access token not received.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"API login failed: {e}")
            return None

    def upload_image(self, file_path, prompt=1, publish=False):
        if not self.access_token:
            print("Access token is missing!")
            return None

        try:
            with open(file_path, "rb") as file:
                img_data = file.read()

            files = {"file": ("image.jpg", img_data, "image/jpeg")}
            data = {"publish": "true" if publish else "false", "prompt": str(prompt)}
            headers = {"Authorization": f"Bearer {self.access_token}"}
            print(f"Sending data: {data}")

            response = requests.post(self.upload_url, data=data, files=files, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            #print(f"Image uploaded successfully: {response_data}")
            return response_data
        except requests.exceptions.RequestException as e:
            print(f"API image upload failed: {e}")
            return None

    def fetch_slugs_for_uploaded_ids(self, uploaded_ids):
        """
        Fetch slugs for specific song IDs (from upload response) and append the base URL.
        """
        if not self.access_token:
            print("Access token is missing!")
            return None

        base_url = "https://song.soundofmeme.com/"
        slugs = []
        page = 1

        while True:
            try:
                url = f"{self.usersongs_url}?page={page}"
                print(page)
                print(uploaded_ids)
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                songs_response = response.json()

                # Debugging: Log the page response
                #print(f"Page {page} response: {songs_response}")

                if not songs_response.get("songs"):
                    print(f"No more songs found or invalid response on page {page}.")
                    break

                # Match IDs with slugs and append base URL
                for song in songs_response["songs"]:
                    if song.get("song_id") in uploaded_ids:
                        slug = song.get("slug")
                        if slug:
                            full_url = f"{base_url}{slug}"
                            slugs.append(full_url)
                            print(f"Found slug for ID {song['song_id']}: {full_url}")
                        else:
                            print(f"Slug not found for ID {song['song_id']}.")

                # Move to the next page
                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching songs on page {page}: {e}")
                break

        return slugs