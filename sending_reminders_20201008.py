# from twilio.rest import Client
import pandas as pd
import datetime
import time
import pytz
import numpy as np
from dateutil import parser

# the bottom 2 should be stored in environment variables for safety, say the twilio instructions
account_sid = '########################'
auth_token = '*******************'
# client = Client(account_sid, auth_token)

our_twilio_number = '+14************'


# Read in the data into a data frame object:

df = pd.read_csv('/home/.../dummy_patient_table.txt', dtype={'weekday': str})
# line below is converting all the start and stop dates to Sofia time zone, 
# else there might be problems with the cloud server times
df.reminder_start = pd.to_datetime(df.reminder_start).dt.tz_localize('UTC').dt.tz_convert('Europe/Sofia')
df.reminder_stop  = pd.to_datetime(df.reminder_stop).dt.tz_localize('UTC').dt.tz_convert('Europe/Sofia')


time_now = datetime.datetime.now(pytz.timezone('Europe/Sofia')).strftime('%H:%M')
#time_now = '09:00'

date_now = datetime.datetime.now(pytz.timezone('Europe/Sofia'))
#date_now = parser.parse("2020-10-02 09:00+03:00")

def simulated_send_sms_func(df):
    '''Function that acts like sending sms'''
    # put all the medicines and their doses into one string, e.g. "1 happche 5mg amidofen, 2 happchete 3mg aspirin, 4 happcheta 10 mg nurofen"
    med_and_doses =  ', '.join(f"{row.dose} {row.medicine}" for idx, row in df.iterrows())
    sms_content = f"Zdraveyte {df.patient_name.iloc[0]}, {df.med_intake_time.iloc[0]} chasa e, vreme da priemete {med_and_doses}. Za prekratyavane na saobshtenieta otgovorete STOP"
    print(sms_content)
    #message = client.messages.create(body=sms_content, from_=our_twilio_number, to=df.phone_num[0])

# select all rows of df that contain the current time
df_current = df[df.med_intake_time == time_now]

# filter only the entries of df for which the current time is within the start and stop date of the reminder
df_current = df_current[(df_current.reminder_start < date_now) & (date_now < df_current.reminder_stop)]

# filter if today's weekday is within the "weekday" range of the medicine, e.g. if today is Wednesday check if its weekday number 2 is within the "weekday" string
df_current = df_current[df_current.weekday.str.contains(str(date_now.weekday()))]

# filter the entries with reminder_flag == 1 (reminder_flag == 0 means 'don't send')
df_current = df_current[df_current.reminder_flag == 1]

# split all the rows for the current time into dataframes corresponding to the customer: df_current = [df_current_ivanov, df_current_georgiev, ...]
dfs_by_customer = [df_i for _, df_i in df_current.groupby(df_current.patient_name)]

# now loop through all the splitted dfs by customer
for df_i in dfs_by_customer:
    simulated_send_sms_func(df_i)
    # df_current.apply(simulated_send_sms_func, axis=1)

# if df contains no schedules for the the current time, then df_current will be just empty
if df_current.empty:
    print('No drugs scheduled at ', time_now)
