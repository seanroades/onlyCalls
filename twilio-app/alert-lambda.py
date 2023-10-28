import requests

## Make request to the api
def lambda_handler(event, context):
    # Read audio_url and phone_number from the event
    audio_url = event["audio_url"]
    phone_number = event["phone_number"]

    # Make request to the api and pass data as form data
    response = requests.post(
        "https://4514-2600-387-f-4b1b-00-8.ngrok.io/call",
        data={"to": phone_number, "audio_url": audio_url},
    )

    # Return the response
    return {"status": "success"}
