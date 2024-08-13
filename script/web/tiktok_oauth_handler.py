import os
import logging
import random
import string
from flask import Blueprint, redirect, request, session, jsonify
import requests
import json

tiktok_oauth_blueprint = Blueprint('tiktok_oauth', __name__)

CLIENT_KEY = os.getenv('OAUTH_TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('OAUTH_TIKTOK_CLIENT_SECRET')
DOMAIN_NAME = os.getenv('APP_DOMAIN_NAME')
REDIRECT_URI = f'https://{DOMAIN_NAME}/oauth/tiktok/callback/'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Step 1: Redirect to TikTok's authorization page
@tiktok_oauth_blueprint.route('/oauth/tiktok', strict_slashes=False)
def oauth():
    state = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    session['state'] = state

    url = 'https://www.tiktok.com/v2/auth/authorize/'
    params = {
        'client_key': CLIENT_KEY,
        'scope': 'user.info.basic,user.info.profile,video.publish,video.upload',
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'state': state
    }
    
    auth_url = requests.Request('GET', url, params=params).prepare().url
    return redirect(auth_url)

# Step 2: Handle the callback from TikTok
@tiktok_oauth_blueprint.route('/oauth/tiktok/callback/')
def callback():
    logging.info("Received callback from TikTok.")

    # Step 1: Retrieve code and state from the request
    code = request.args.get('code')
    state = request.args.get('state')
    logging.info(f"Authorization code: {code}, State: {state}")

    # Step 2: Validate the state parameter to prevent CSRF attacks
    if state != session.get('state'):
        logging.error("State mismatch. Possible CSRF attack.")
        return 'State mismatch. Possible CSRF attack.', 400

    logging.info("State parameter validated successfully.")

    # Step 3: Exchange the authorization code for an access token and refresh token
    token_url = 'https://open.tiktokapis.com/v2/oauth/token/'
    data = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    logging.info(f"Sending POST request to TikTok API to exchange code for tokens. URL: {token_url}, Data: {data}")

    try:
        response = requests.post(token_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        logging.info(f"Received response from TikTok API. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error during request to TikTok API: {e}")
        return f"Failed to contact TikTok API: {e}", 500

    if response.status_code == 200:
        token_data = response.json()
        logging.info(f"Token data received: {token_data}")
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')

        # Step 4: Use the access token to get the TikTok username
        try:
            from tiktok_utils import get_username
            username = get_username(access_token)
            logging.info(f"Retrieved TikTok username: {username}")
        except Exception as e:
            logging.error(f"Failed to retrieve TikTok username: {e}")
            return f"Failed to retrieve TikTok username: {e}", 500

        # Step 5: Update the JSON file with the new refresh token
        account_file_path = f'/mnt/accounts/{username}.json'
        logging.info(f"Updating account JSON file at: {account_file_path}")

        try:
            with open(account_file_path, 'r') as file:
                account_data = json.load(file)
            logging.info(f"Current account data: {account_data}")

            account_data['refresh_token'] = refresh_token
            logging.info(f"Updated refresh token in account data.")

            with open(account_file_path, 'w') as file:
                json.dump(account_data, file, indent=4)
            logging.info(f"Account file updated successfully.")
        except FileNotFoundError:
            logging.error(f"Account file not found: {account_file_path}")
            return f"Account file not found: {account_file_path}", 500
        except Exception as e:
            logging.error(f"Failed to update account JSON file: {e}")
            return f"Failed to update account JSON file: {e}", 500

        return jsonify(access_token=access_token, refresh_token=refresh_token)
    else:
        error_description = response.json().get('error_description', 'No error description provided')
        logging.error(f"Failed to get access token: {error_description}")
        return f"Failed to get access token: {error_description}", 400

