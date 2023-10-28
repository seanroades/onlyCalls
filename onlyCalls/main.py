import json
from typing import Iterator 
import openai
import csv
import random
from elevenlabs import set_api_key, generate, Voice, VoiceSettings, play
import os
from typing import Union
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

if not OPENAI_API_KEY or not ELEVEN_LABS_API_KEY:
    raise ValueError("Both OPENAI_API_KEY and ELEVEN_LABS_API_KEY must be set in the environment.")

## setup 11
set_api_key(ELEVEN_LABS_API_KEY)
openai.api_key = OPENAI_API_KEY


def supabase_upload():
    with open("path_to_your_audio_file", "rb") as file:
        file_name = "your_audio_file_name"
        path_in_bucket = "path_in_bucket/" + file_name
        bucket = "your_bucket_name"
        res = supabase.storage.from_(bucket).upload(path_in_bucket, file)

def remind(json_object):
    text_data = generate_text(json_object)
    generate_text(text_data['text'], text_data['voice_id'])

def generate_voice(text, voiceId):
    print(f"Generating voice with text: {text} and voiceId: {voiceId}")
    audio: Union[bytes, Iterator[bytes]] = generate(
    text=text,
    model="eleven_multilingual_v2",
    voice=Voice(
            voice_id=voiceId,
            settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.49, use_speaker_boost=True)
        )
    )
    
    with open('calls/audio.mp3', 'wb') as f:
        f.write(audio)

    play(audio)

def generate_text(goal_data) -> str:
    if 'goal' not in goal_data or 'time' not in goal_data:
        return "Invalid JSON object. 'goal' and 'time' keys are required."
    
    person = select_random_person()

    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
          {"role": "system", "content": f"""
Pretend you are {person['person_name']}. 

You have this persona:
{person['persona']}

Given a goal and time for the user, you should tell them aggressively to do their goal in the style of your character, use your accomplishments as a reference. Only return your motivational line to them.
"""},
          {"role": "user", "content": f"""
Goal:
{goal_data['goal']} at {goal_data['time']}
"""}
      ]
    )
    text = response['choices'][0]['message']['content']
    print(f"Generated text: {text}")
    return { "text": text, "voice_id": person['voice_id']}

def select_random_person():
    with open('persons.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)
        random_person = random.choice(data)
        print(f"Selected random person: {random_person['real_person']}")
        return {'voice_id': random_person['voice_id'], 'persona': random_person['default_persona'], 'person_name': random_person['real_person']}


if __name__ == "__main__":
    with open('test.json', 'r') as file:
        goal_data = json.load(file)
    text_voice = generate_text(goal_data)
    generate_voice(text_voice["text"], text_voice["voice_id"])
