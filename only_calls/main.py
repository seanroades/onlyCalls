import json
from typing import Iterator
import openai
import csv
import random
import os
from typing import Union
from dotenv import load_dotenv
import requests
import uuid
from supabase import create_client, Client
from datetime import datetime
import pytz

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
SUPABASE_ADMIN = os.getenv("SUPABASE_ADMIN")
SUPABASE_URL = os.getenv("SUPABASE_URL")

if (
    not OPENAI_API_KEY
    or not ELEVEN_LABS_API_KEY
    or not SUPABASE_ADMIN
    or not SUPABASE_URL
):
    raise ValueError(
        "Both OPENAI_API_KEY and ELEVEN_LABS_API_KEY and SUPABASE_ADMIN and SUPABASE_URL must be set in the environment."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ADMIN)

## setup 11
openai.api_key = OPENAI_API_KEY


def upload_reminder(
    audio: Union[bytes, Iterator[bytes]],
    number: str,
    time: str,
    bot_name: str,
    utc_timestamp: str,
) -> bool:
    """Returns uuid of audio path to point to in table"""
    audio_id = str(uuid.uuid4())

    # Audio upload
    path_in_bucket = audio_id + ".mp3"  # e.g., just the mp3 file name not the full path

    supabase.storage.from_("reminders").upload(
        file=audio, path=path_in_bucket, file_options={"content-type": "audio/mpeg"}
    )

    data, count = (
        supabase.table("reminders")
        .insert(
            [
                {
                    "number": number,
                    "time": time,
                    "bot_name": bot_name,
                    "audio_path": path_in_bucket,
                }
            ]
        )
        .execute()
    )

    # Get public url for audio
    audio_url = supabase.storage.from_("reminders").get_public_url(path_in_bucket)

    print(f"\n[Uploaded audio]: {audio_url}")

    req_body = {"phone_number": number, "audio_url": audio_url, "time": utc_timestamp}

    response = requests.post(
        "https://cl5u6hgzuc.execute-api.us-west-2.amazonaws.com/test/schedule",
        json=req_body,
    )

    print(response)
    return True


def remind(json_object) -> None:
    text_data = generate_text(json_object)
    generate_text(text_data["text"], text_data["voice_id"])


def generate_voice(text, voiceId) -> Union[bytes, Iterator[bytes]]:
    """Returns path of reminder audio to be used for uploading voice, time is human readable for the LLM"""
    print(f"\n[Generating voice with text]: {voiceId}")
    CHUNK_SIZE = 1024

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voiceId}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": f"{ELEVEN_LABS_API_KEY}",
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7,
            "style": 0.49,
            "use_speaker_boost": True,
        },
    }

    response = requests.post(url, json=data, headers=headers)

    chunks = bytearray()

    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunk:
            chunks.extend(chunk)

    return bytes(chunks)


def generate_text(goal_data) -> str:
    if "goal" not in goal_data or "time" not in goal_data:
        return "Invalid JSON object. 'goal' and 'time' keys are required."

    person = select_random_person()

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"""
Pretend you are {person['person_name']}. 

You have this persona:
{person['persona']}

Given a goal and time for the user, you should tell them aggressively to do their goal in the style of your character, use your accomplishments as a reference. Introduce yourself and shame them into doing their goals based on your acheivements. Only return your motivational line to them.
""",
            },
            {
                "role": "user",
                "content": f"""
Goal:
{goal_data['goal']} at {goal_data['time']}
""",
            },
        ],
    )
    text = response["choices"][0]["message"]["content"]
    print(f"\n[Generated text]: {text}")
    return {"text": text, "voice_id": person["voice_id"]}


def select_random_person() -> dict[str, Union[str, any]]:
    with open("persons.csv", "r") as file:
        reader = csv.DictReader(file)
        data = list(reader)
        random_person = random.choice(data)
        print(f"[Selected random person]: {random_person['real_person']}")
        return {
            "voice_id": random_person["voice_id"],
            "persona": random_person["default_persona"],
            "person_name": random_person["real_person"],
        }


def time_safety_checks(time_json):
    """Given a str that should be in format mm:hh:day:month:year, check it is of valid format, convert it to a human readable time and a timestampz of the current timezone. Returns times for human readable for LLM and timestampz of PST time"""
    time_str = f"{time_json['min']}:{time_json['hour']}:{time_json['day']}:{time_json['month']}:{time_json['year']}"

    try:
        datetime_object = datetime.strptime(time_str, "%M:%H:%d:%m:%Y")
        human_readable_time = datetime_object.strftime(
            "%H:%M on %B %d, %Y"
        )  # B for full month name
        current_time = datetime.now()

        # Check there isn't < 3 min difference
        time_difference = datetime_object - current_time
        if time_difference.total_seconds() < 240:  # Check it is > 4 min
            return "Your reminder may be too early to be processed by our systems. Please set it for 5 min or more in the future. If you believe this was a mistake, let us know!"

        # Set to PST
        new_date_time_object = datetime_object.replace(tzinfo=pytz.UTC)
        new_date_time_object = new_date_time_object.astimezone(
            pytz.timezone("America/Los_Angeles")
        )  # TODO: generalize timezon

        timestamp = datetime_object.timestamp()
        la_timestamp = new_date_time_object.timestamp()  # LA time
        datetime_object = datetime.fromtimestamp(timestamp, pytz.UTC)
        new_date_time_object = datetime.fromtimestamp(
            la_timestamp, pytz.timezone("America/Los_Angeles")
        )
        # Cast as str b/c Object of type datetime is not JSON serializable
        return {
            "human_readable": human_readable_time,
            "timestampz": str(new_date_time_object),
            "utc_timestamp": str(datetime_object),
        }

    except ValueError:
        raise ValueError("Incorrect time format, should be mm:hh:day:month:year")


def get_time(message):
    """Get time from a prompt, returns a human_readable time and a timestampz"""
    while True:
        try:
            current_time = datetime.now()
            human_readable_time = {
                "min": current_time.minute,
                "hour": current_time.hour,
                "day": current_time.day,
                "month": current_time.month,
                "year": current_time.year,
            }  # Converted to a JSON of min, hour, day, month, and year

            print("get time", "curr time is ", human_readable_time)

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
You will be given a time when the user wants to be reminded at some time in the future. 
           
You will be given a current time in json format.
           
Return the future time to remind the user in the same JSON format with double quotes. Only return the JSON. 
""",
                    },
                    {
                        "role": "user",
                        "content": f"""
The current time is the following in JSON format: {human_readable_time}

reminder:
{message}

Future time:
""",
                    },
                ],
            )
            time_str = response["choices"][0]["message"]["content"]

            time_json = json.loads(time_str)  # parse the string into a dictionary

            times = time_safety_checks(time_json)

            print("[TIMES]: ", times)

            return times
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")


def create_reminder(
    goal: str,
    time: str,
    phone_number: str,
    exact_time: any,
    bot_name: str,
    utc_timestamp: str,
) -> bool:
    """Entire process for reminder, given time / goal. Time is human readable time from get_time. Goal is the message from the user in its entirety."""
    text_voice = generate_text({"goal": goal, "time": time})
    audio = generate_voice(text_voice["text"], text_voice["voice_id"])
    upload_reminder(audio, phone_number, exact_time, bot_name, utc_timestamp)
