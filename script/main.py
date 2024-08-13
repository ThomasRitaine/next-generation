import os
import random
import logging
import threading
import time
from tiktok_utils import upload_video, get_access_token
from web.boot import boot_web_server
from moneyprinterturbo_utils import generate_video_for_user, read_json_file

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def select_random_user():
    accounts_dir = '/mnt/accounts/'
    account_files = [f for f in os.listdir(accounts_dir) if f.endswith('.json') and not f.endswith('.example.json')]
    selected_file = random.choice(account_files)
    username = selected_file.replace('.json', '')
    return username

def start_oauth_server():
    logging.info("Starting TikTok OAuth server in a new thread")
    server_thread = threading.Thread(target=boot_web_server)
    server_thread.daemon = True  # Allows the server to be stopped when the main program exits
    server_thread.start()

def main():
    # Start the web server in a separate thread
    start_oauth_server()

    time.sleep(5)  # Give some time for the server to start properly

    while True:
        try:
            logging.info("Selecting a random user account")
            username = select_random_user()

            logging.info(f"Generating video for user: {username}")
            video_path, description = generate_video_for_user(username)

            logging.info("Getting access token")
            input_data = read_json_file(f'/mnt/accounts/{username}.json')
            access_token = get_access_token(input_data['refresh_token'])

            logging.info("Uploading video to TikTok")
            upload_video(video_path, description, access_token)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            logging.info("Process completed, waiting before the next run.")
            time.sleep(21600)  # Wait for 6 hours before next execution

if __name__ == '__main__':
    main()

