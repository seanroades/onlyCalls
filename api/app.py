from flask import Flask, request
from only_calls.main import create_reminder, get_time
from twilioapp.app import send_message_twilio
from twilioapp.caller import make_call
from datetime import datetime

app = Flask(__name__)


def convert_timestamp(timestamp):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S%z")
    formatted_date = dt.strftime("%H:%M on %B %d, %Y")
    return formatted_date


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
        message_body="Reminder set successfully for "
        + convert_timestamp(times["timestampz"]),
    )

    return {"status": "success"}


@app.route("/call", methods=["POST"])
def call():
    data = request.form
    res = {}
    try:
        res["to"] = data["to"]
        res["audio_url"] = data["audio_url"]
        print("\n[RES], ", res)
    except:
        return {"status": "There is no data"}

    make_call(call_url=res["audio_url"], to_number=res["to"])

    return {"status": "success"}


if __name__ == "__main__":
    app.run(debug=True, port=6969)
