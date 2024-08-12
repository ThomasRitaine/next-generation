import os
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_access_token(refresh_token):
    """
    Refresh the TikTok access token using the provided refresh token.

    This function makes a POST request to the TikTok API to refresh the access token. 
    If the returned refresh token is different from the input refresh token, it updates 
    the local JSON file associated with the TikTok username.

    Parameters:
    refresh_token (str): The current refresh token to be used for getting a new access token.

    Returns:
    str: The new access token.

    Raises:
    Exception: If the token refresh process fails.
    """
    url = 'https://open.tiktokapis.com/v2/oauth/token/'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(url, headers=headers, data=data)
    response_data = response.json()

    if response.status_code == 200:
        new_refresh_token = response_data['refresh_token']
        access_token = response_data['access_token']

        if new_refresh_token != refresh_token:
            from tiktok_utils import get_username
            username = get_username(access_token)
            account_file_path = f'/mnt/accounts/{username}.json'

            with open(account_file_path, 'r') as file:
                account_data = json.load(file)

            account_data['refresh_token'] = new_refresh_token

            with open(account_file_path, 'w') as file:
                json.dump(account_data, file, indent=4)

        return access_token
    else:
        raise Exception(f"Failed to refresh token: {response_data['error_description']}")

def get_username(access_token):
    """
    Retrieves the username of a TikTok account using the provided OAuth access token.

    Args:
        access_token (str): The OAuth access token for the TikTok account.

    Returns:
        str: The username of the TikTok account.
    """
    url = 'https://open.tiktokapis.com/v2/user/info/'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'fields': 'username'
    }

    logging.info(f"Sending GET request to TikTok API to retrieve user info. URL: {url}, Params: {params}")

    response = requests.get(url, headers=headers, params=params)
    logging.info(f"Received response from TikTok API. Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        logging.info(f"Response data: {data}")

        if 'data' in data and 'user' in data['data'] and 'username' in data['data']['user']:
            username = data['data']['user']['username']
            logging.info(f"Username retrieved: {username}")
            return username
        else:
            logging.error("Username not found in the response.")
            raise ValueError("Username not found in the response.")
    else:
        error_message = response.json().get('error', {}).get('message', 'No error description provided')
        logging.error(f"Request failed with status code {response.status_code}: {error_message}")
        raise Exception(f"Request failed with status code {response.status_code}: {error_message}")

def upload_video(video_path, description, access_token):
    """
    Uploads a video to TikTok with the given description using the provided OAuth access token.

    Args:
        video_path (str): The path to the video file.
        description (str): The description of the video.
        access_token (str): The OAuth access token for the TikTok account.

    Returns:
        None
    """

    def initialize_upload(access_token, video_size, chunk_size, total_chunk_count):
        url = 'https://open.tiktokapis.com/v2/post/publish/video/init/'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        data = {
            'post_info': {
                'title': description.strip(),  # Ensure title is non-empty and trimmed
                'privacy_level': 'SELF_ONLY',  # Required for unaudited clients
                'disable_duet': False,
                'disable_comment': False,
                'disable_stitch': False,
                'video_cover_timestamp_ms': 1000
            },
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_size': video_size,
                'chunk_size': chunk_size,
                'total_chunk_count': total_chunk_count
            }
        }

        # Log the exact data being sent
        logging.info(f"Request Headers: {headers}")
        logging.info(f"Request Payload: {data}")

        response = requests.post(url, json=data, headers=headers)
        logging.info(f"Received response for initialization: Status Code={response.status_code}, Response={response.json()}")

        if response.status_code == 200 and response.json().get('error', {}).get('code') == 'ok':
            logging.info("Video upload initialized successfully.")
            return response.json()['data']
        else:
            error_message = response.json().get('error', {}).get('message', 'Unknown error')
            logging.error(f"Failed to initialize upload: {error_message}")
            raise Exception(f"Failed to initialize upload: {error_message}")

    def upload_video_chunk(upload_url, video_path, chunk_size, total_chunk_count):
        with open(video_path, 'rb') as video_file:
            total_size = os.path.getsize(video_path)
            logging.info(f"Uploading video in chunks: Total Size={total_size} bytes, Chunk Size={chunk_size} bytes")

            for i in range(total_chunk_count):
                chunk = video_file.read(chunk_size)
                headers = {
                    'Content-Type': 'video/mp4',
                    'Content-Length': str(len(chunk)),
                    'Content-Range': f'bytes {i * chunk_size}-{(i + 1) * chunk_size - 1}/{total_size}'
                }
                logging.info(f"Uploading chunk {i + 1}/{total_chunk_count}: Range={headers['Content-Range']}")
                response = requests.put(upload_url, headers=headers, data=chunk)
                logging.info(f"Received response for chunk upload: Status Code={response.status_code}")

                if response.status_code not in range(200, 300):
                    logging.error("Failed to upload chunk.")
                    raise Exception("Failed to upload chunk.")
            logging.info("All chunks uploaded successfully.")

    try:
        video_size = os.path.getsize(video_path)
        chunk_size = 10 * 1024 * 1024  # 10 MB chunk size by default
        
        # Adjust chunk size to make sure total_chunk_count is valid
        while video_size % chunk_size != 0:
            chunk_size -= 1
        
        total_chunk_count = video_size // chunk_size

        logging.info(f"Starting video upload process: Video Path={video_path}, Description={description}, Video Size={video_size} bytes, Adjusted Chunk Size={chunk_size} bytes, Total Chunk Count={total_chunk_count}")

        # Initialize the video upload
        init_data = initialize_upload(access_token, video_size, chunk_size, total_chunk_count)
        upload_url = init_data['upload_url']

        # Upload the video in chunks
        upload_video_chunk(upload_url, video_path, chunk_size, total_chunk_count)

        logging.info("Video uploaded successfully.")
    except Exception as e:
        logging.error(f"Error during video upload: {e}")
        raise
