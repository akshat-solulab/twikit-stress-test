import twikit
from typing import Optional
import json
import asyncio
from pathlib import Path
import time

SCRIPT_DIR = Path(__file__).parent
EXTRACTED_COOKIES_PATH = SCRIPT_DIR / "x.com.cookies.json"
SAVED_COOKIES_PATH = SCRIPT_DIR / "twikit_cookies.json"


def await_for_cookies() -> dict:
    """Awaits for the cookies file"""

    print(f"Please copy the '{EXTRACTED_COOKIES_PATH}' file into this repo...")

    while not EXTRACTED_COOKIES_PATH.exists():
        time.sleep(5)

    print("Cookie file detected")

    with open(EXTRACTED_COOKIES_PATH, "r", encoding="utf-8") as cookies_file:
        cookies = json.load(cookies_file)

    cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
    return cookies_dict


async def async_get_twitter_cookies(username, email, password) -> Optional[str]:
    """Verifies that the Twitter credentials are correct and get the cookies"""

    client = twikit.Client(
        language="en-US"
    )

    try:
        valid_cookies = False

        # If cookies exist, try with those and validate
        if SAVED_COOKIES_PATH.exists():
            with open(SAVED_COOKIES_PATH, "r", encoding="utf-8") as cookies_file:
                cookies = json.load(cookies_file)
                client.set_cookies(cookies)

            user = await client.user()
            valid_cookies = user.screen_name == username

        if not valid_cookies:
            print("Logging in with password")
            await client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password,
            )
            client.save_cookies(SAVED_COOKIES_PATH)

    except twikit.errors.BadRequest:
        print("Twitter login failed due to a known issue with the login flow.\nPlease check the known issues section in the README to find the solution. You will need to provide us with a cookies file.")
        cookies = await_for_cookies()
        client.set_cookies(cookies)
        client.save_cookies(SAVED_COOKIES_PATH)  # Save cookies to the specified path

    return json.dumps(client.get_cookies()).replace(" ", "")


def get_twitter_cookies(username, email, password) -> Optional[str]:
    """get_twitter_cookies"""
    return asyncio.run(async_get_twitter_cookies(username, email, password))


def main():
    config_path = SCRIPT_DIR / ".memeooorr" / "local_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    username = input("Enter your Twitter username: ")
    email = input("Enter your Twitter email: ")
    password = input("Enter your Twitter password: ")

    try:
        cookies = get_twitter_cookies(username, email, password)
        with open(config_path, "w", encoding="utf-8") as config_file:
            config = {
                "twikit_username": username,
                "twikit_email": email,
                "twikit_password": password,
                "twikit_cookies": cookies
            }
            json.dump(config, config_file, indent=4)
        print("Cookies saved successfully.")
    except twikit.errors.Unauthorized as e:
        print(f"Authentication failed: {e}")

if __name__ == "__main__":
    main()


async def async_validate_twitter_credentials():
    """Test twitter credential validity"""

    # Load cookies
    with open(Path(".memeooorr", "local_config.json"), "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        cookies = json.loads(config["twikit_cookies"])

    # Instantiate the client
    client = twikit.Client(
        language="en-US"
    )

    # Set cookies
    client.set_cookies(cookies)

    # Try to read using cookies
    try:
        tweet = await client.get_tweet_by_id("1741522811116753092")
        is_valid_cookies = tweet.user.id == "1450081635559428107"
        return is_valid_cookies, None
    except twikit.errors.Forbidden:
        is_valid_cookies = False
        cookies = await async_get_twitter_cookies(
            config["twikit_username"],
            config["twikit_email"],
            config["twikit_password"]
        )
        with open(SCRIPT_DIR / ".memeooorr" / "local_config.json", "w", encoding="utf-8") as config_file:
            config["twikit_cookies"] = cookies
            json.dump(config, config_file, indent=4)
        return is_valid_cookies, cookies


def validate_twitter_credentials() -> Optional[str]:
    """Validate twitter credentials"""
    return asyncio.run(async_validate_twitter_credentials())
