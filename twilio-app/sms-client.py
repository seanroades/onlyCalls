from flask import Flask, request
import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client
from .caller import make_call
from only_calls.main import create_reminder, get_time


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


app = Flask(__name__)


@app.route("/", methods=["GET"])
def root():
    return {"message": "Hello World"}


@app.route("/sms", methods=["POST"])
def sms():
    data = request.form
    res = {}
    try:
        res["From"] = data["From"]
        res["To"] = data["To"]
        res["Body"] = data["Body"]
    except:
        return {"status": "There is no data"}

    times = get_time(res["Body"])
    bot_name = "NOT_IMPLEMENTED"

    create_reminder(
        res["Body"],
        times["human_readable"],
        res["From"],
        times["timestampz"],
        bot_name,
        times["utc_timestamp"],
    )

    print(times)

    send_message_twilio(
        from_number=res["From"],
        to_number=res["To"],
        message_body="Reminder set successfully for " + times["human_readable"],
    )

    return {"status": "success"}


@app.route("/call", methods=["POST"])
def call():
    data = request.form
    res = {}
    try:
        res["to"] = data["to"]
        res["audio_url"] = data["audio_url"]
    except:
        return {"status": "There is no data"}

    make_call(call_url=res["audio_url"], to_number=res["to"])

    return {"status": "success"}


if __name__ == "__main__":
    app.run(debug=True, port=6969)
