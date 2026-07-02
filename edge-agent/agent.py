import time

from config import *

from network import check_latest_firmware, download_file
while True:
    print("Checking for firmware update...")

    data = check_latest_firmware()

    if data:
        print("Latest Firmware Info:", data)

    else:
        print("Could not connect to server.")

    time.sleep(CHECK_INTERVAL)

