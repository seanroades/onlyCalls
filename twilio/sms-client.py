from flask import Flask, request
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import (
    PromptTemplate,
)
from langchain.llms import OpenAI
import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client
from caller import make_call

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


def parse_message(message, dt=datetime.datetime.now()):
    response_schemas = [
        ResponseSchema(
            name="time",
            description="time (in the format hh:mm:day:month:year) to set up the alarm for",
        ),
        ResponseSchema(name="reminder", description="content for the alarm/reminder"),
        ResponseSchema(
            name="response",
            description="LLM generated text to confirm that the reminder is set at a specific time, please return the time back in text and not time object",
        ),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    current_dateTime = dt
    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        template="parse this text message and return the appropriate date and time and content body. Increase the date by one day if the next possible time has passed for today. For example if the user says remind me at 7am and it's already 10pm on oct 28 then make it oct 29 \n{format_instructions}\n{question}",
        input_variables=["question"],
        partial_variables={"format_instructions": format_instructions},
    )
    model = OpenAI(temperature=0)
    _input = prompt.format_prompt(
        question=message + "today's date:" + str(current_dateTime)
    )
    output = model(_input.to_string())
    model_res = output_parser.parse(output)
    return model_res


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

    print(res)

    model_res = parse_message(res["Body"], datetime.datetime.now())
    print(model_res["time"])
    date = parse_time(model_res["time"])
    print(date)
    model_res["time"] = date
    # Check if the available time has already passed otherwise change dates

    if date is not None:
        print(date)
        if date < datetime.datetime.now():
            date = date + datetime.timedelta(days=1)
            print(date)
            model_res["time"] = date
            model_res = parse_message(res["Body"], dt=date)

    send_message_twilio(
        from_number=res["From"],
        to_number=res["To"],
        message_body=model_res["response"],
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
