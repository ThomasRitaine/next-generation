import json
import random
import time
import requests
import logging
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_json_file(file_path):
    logging.info(f"Reading input data from {file_path}")
    with open(file_path, 'r') as file:
        data = json.load(file)
    logging.info("Input data successfully read")
    return data

def get_video_data(input_json):
    logging.info("Selecting a random video subject and extracting video language")
    video_subject = random.choice(input_json['video_subjects'])
    video_language = input_json['video_language']
    logging.info(f"Selected video subject: {video_subject}, Video language: {video_language}")
    return video_subject, video_language

def generate_video_for_user(username):
    input_file_path = f'/mnt/accounts/{username}.json'
    input_data = read_json_file(input_file_path)
    video_subject, video_language = get_video_data(input_data)
    
    # Generate script
    logging.info(f"Generating script for subject: {video_subject} in language: {video_language}")
    script_response = requests.post('http://api:8080/api/v1/scripts', json={
        'video_subject': video_subject,
        'video_language': video_language,
        'paragraph_number': 1
    }).json()
    logging.info("Script generated successfully")

    # Generate terms
    logging.info(f"Generating terms for video script")
    terms_response = requests.post('http://api:8080/api/v1/terms', json={
        'video_subject': video_subject,
        'video_script': script_response['data']['video_script'],
        'amount': 7
    }).json()
    logging.info("Terms generated successfully")

    # Final video request
    logging.info(f"Requesting final video generation")
    video_response = requests.post('http://api:8080/api/v1/videos', json={
        'video_subject': video_subject,
        'video_script': script_response['data']['video_script'],
        'video_terms': ', '.join(terms_response['data']['video_terms']),
        'video_aspect': input_data['video_aspect'],
        'video_concat_mode': input_data['video_concat_mode'],
        'video_clip_duration': input_data['video_clip_duration'],
        'video_count': input_data['video_count'],
        'video_source': input_data['video_source'],
        'video_materials': input_data['video_materials'],
        'video_language': video_language,
        'voice_name': input_data['voice_name'],
        'voice_volume': input_data['voice_volume'],
        'voice_rate': input_data['voice_rate'],
        'bgm_type': input_data['bgm_type'],
        'bgm_file': input_data['bgm_file'],
        'bgm_volume': input_data['bgm_volume'],
        'subtitle_enabled': input_data['subtitle_enabled'],
        'subtitle_position': input_data['subtitle_position'],
        'custom_position': input_data['custom_position'],
        'font_name': input_data['font_name'],
        'text_fore_color': input_data['text_fore_color'],
        'text_background_color': input_data['text_background_color'],
        'font_size': input_data['font_size'],
        'stroke_color': input_data['stroke_color'],
        'stroke_width': input_data['stroke_width'],
        'n_threads': input_data['n_threads'],
        'paragraph_number': input_data['paragraph_number']
    }).json()
    logging.info("Video generation request successful")

    task_id = video_response['data']['task_id']
    video_path = f'/mnt/storage/tasks/{task_id}/final-1.mp4'
    logging.info(f"Generated video task ID: {task_id}, video URL: {video_path}")

    # Polling for video completion with timeout
    logging.info("Polling for video completion")
    start_time = datetime.datetime.now()
    timeout = datetime.timedelta(minutes=30)
    while True:
        task_response = requests.get(f'http://api:8080/api/v1/tasks/{task_id}').json()
        if task_response['data']['state'] == 1:
            logging.info("Video generation complete")
            break
        if datetime.datetime.now() - start_time > timeout:
            raise TimeoutError("Timeout reached while waiting for video generation")
        logging.info("Video generation in progress, waiting for 30 seconds before next check")
        time.sleep(30)
    
    # Prepare the description for the video
    description = f"{video_subject} - A short video created using AI tools."

    return video_path, description

