import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client


load_dotenv()
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)


def send_message_twilio(from_number, to_number, message_body):
    try:
        message = client.messages.create(
            from_=to_number, body=message_body, to=from_number
        )
        print(f"Message sent successfully. SID: {message.sid}")
    except Exception as e:
        print(f"Error: {e}")


def parse_time(time_string):
    try:
        datetime_obj = datetime.datetime.strptime(time_string, "%H:%M:%d:%m:%Y")
        return datetime_obj
    except ValueError as e:
        print(f"Error: {e}")
        return None
