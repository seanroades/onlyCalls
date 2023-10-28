# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

# Set environment variables for your credentials
# Read more at http://twil.io/secure

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)


def make_call(
    call_url="https://audio.jukehost.co.uk/JPP2bc4fA9Tl8Wbeo7FwuVNhRwsg3Ac5.mp3",
):
    custom_twiml = f"""
    <Response>
    <Play>{call_url}</Play>
    </Response>
    """
    call = client.calls.create(
        url="http://demo.twilio.com/docs/voice.xml",
        to="+15023880975",
        from_="+18556475409",
    )

    print(call.sid)
