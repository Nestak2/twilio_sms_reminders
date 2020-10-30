# twilio_sms_reminders
Pytnon scripts for sending periodic, scheduled sms reminders using the twilio library/service.

The scripts are writen for the purpose of reminding patients about their medication intake, but the scripts can be altered for your particular application.
The scripts are intended to fullfil the service presented here: https://youtu.be/H4PVDc8M0a0

The main idea for the use of the scripts is the following:
- The user has some data base (in this case a csv file, dummy_patient_table.txt) containing the time and the phone number to which sms messages should be send. The csv also contains some additional relevant information - in the present case we use it as medication intake reminders, so the csv contains the medication name, dose, intake start and stop date and similar
- there is the sending_reminders.py script, that has to be ran periodically, e.g. by a cloud service like AWS or Microsoft Azure or alternatively run locally
in a time delayed loop every N seconds. When the sending_reminders.py script gets executed in checks if for the current time (e.g. 9:30 am) there are any logs in the csv for sending sms and if so it sends the sms' with the corresponding content (e.g., 'Hi, it's 9:30 am, time to take Aspirin!')
- there is also the script responses.py. If is is run over an ngrok tunnel it waits if there will be sms replies back from the patients to the twilio sending number. If a reply is received the script checks if the content of the reply matches some of the if-clauses and performs an action of sending another sms to the patient (e.g. patient writes back to the twilio number: "MEDICATIONS", the scripts sends a reply: "The list of your medications is: Aspirin, Nurofen, Prozac")
