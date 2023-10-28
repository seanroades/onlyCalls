from only_calls.main import create_reminder, get_time

message = "Remind me to brush my teeth at 7am today"
phone_number = "+18708977103"
bot_name = "NOT_IMPLEMENTED"

times = get_time(message)

try:
  if isinstance(times, dict):
      create_reminder(message, times['human_readable'], phone_number, times['timestampz'], bot_name)
  else:
      print("Reminder set too soon", times)
      # should return to user the message times contains 

except Exception as e:
  print(e)
   # return error to user
  print("UNEXPECTED ERROR OCCURED")