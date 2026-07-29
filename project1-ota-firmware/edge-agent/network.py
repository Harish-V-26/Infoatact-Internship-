
import requests

from config import *

def check_latest_firmware():
    try:
        response = requests.get(
            f"{SERVER_URL}/firmware/latest",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print("Error:", e)
        return None


def download_file(url, filename):
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        with open(filename, "wb") as file:
            file.write(response.content)

        print("Download successful.")
        return True

    except Exception as e:
        print("Download failed:", e)
        return False