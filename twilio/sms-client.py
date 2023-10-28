from flask import Flask, request

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

    return {"status": "Data printed"}


if __name__ == "__main__":
    app.run(debug=True, port=6969)
