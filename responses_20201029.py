
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
import datetime
import pytz
# the below import is only needed for forwarding the sms, in case the client sends KONTAKT
from twilio.rest import Client

account_sid = '######################'
auth_token = '*********************'
client = Client(account_sid, auth_token)
# below is the number that is supposed to send out the sms to one of use, in case a client has send KONTAKT
happ_num1 = '+14*******'
# below is the number on which we will receive the sms with the message that a client requests KONTAKT
happ_num2 = '+15*******'

app = Flask(__name__)

file_path = '/home/.../dummy_patient_table.txt'

@app.route("/sms", methods=['GET', 'POST'])
def incoming_sms():
    """Send a dynamic reply to an incoming text message"""
    
    # Get the message and phone number the of the user replying back
    body = request.values.get('Body', None)
    phone_num = request.values.get('From', None)
    
    # get all the data to this user in a data fram
    df0 = pd.read_csv(file_path, dtype={'weekday': str})
    df0.reminder_start = pd.to_datetime(df0.reminder_start).dt.tz_localize('UTC').dt.tz_convert('Europe/Sofia')
    df0.reminder_stop  = pd.to_datetime(df0.reminder_stop).dt.tz_localize('UTC').dt.tz_convert('Europe/Sofia')

    df = df0[df0.phone_num == phone_num]
    
    # dictionary below turns the weekday number into weekday names for the messages
    num2wday = {0:'пон.', 1:'вт.', 2:'ср.', 3:'четв.', 4:'пет.', 5:'съб.', 6:'нед.'} 

    # Start our TwiML response
    resp = MessagingResponse()

    # Determine the right reply for this message
    if body == 'INFO':
        pass
        # this code word is preserved by twilio, but this can be changed:
        # https://www.twilio.com/docs/sms/services/advanced-opt-out
        
    if body.lower() == 'инфо':
        m = 'Вие използвате услугата на Хапп за напомняне на приемане на лекарства.\nЗа спиране на услугата напишете STOP\nЗа да се свържем с Вас обратно - KONTAKT\nЗа списък на всички лекарства с включени напомняния - NAPOMNYANIYA\nЗа достъп до листовката на определено лекарство - INFO-[LEKARSTVO], например INFO-AMIDOFEN\nЗа детайли за всички лекарства, които взимате -  LEKARSTVA\nЗа списък на всички лекарства които взимате и сте взимали - ISTORIYA'
        resp.message(m)
        
        
    if body.lower() == 'стоп':
        # set all the reminder flags of this patient to 0 and save the update df0 to the file
        df0.reminder_flag[df0.phone_num == phone_num] = 0
        # update also the column of the stop date with the current date
        df0.reminder_stop[df0.phone_num == phone_num] = pytz.timezone("Europe/Sofia").localize(datetime.datetime.now())
        # you also need to update the current working version of the dataframe (df)
        df.reminder_flag[df.phone_num == phone_num] = 0
        df.reminder_stop[df.phone_num == phone_num] = pytz.timezone("Europe/Sofia").localize(datetime.datetime.now())
        # update the changes also the the original file itself
        df0.to_csv(file_path, index=False, date_format="%d.%m.%y")
        m = 'Вие успешно се отписахте от услугата за напомняния на Хапп. Ако искате да я включите на ново отговорете START'
        resp.message(m)
        
        
    if body.lower() == 'napomnyaniya' or body.lower() == 'напомняния':
        # sends messages of the kind:
        # За следните лекарства има включени напомняния:
        # Амидофен, ден 6 от 14 от услугата: напомняния в 09:00, 15:00, 21:00
        # Валериан, ден 3 : 09:00, 17:00, само вторник и петък.
        # За спиране на напомнянията отговорете STOP. За да активирате напомняния за допълнителни лекарства, моля отговорете с KONTAKT.

        # select only medications with reminder flag == 1
        df = df[df.reminder_flag == 1]
        df_gr = df.groupby(['medicine','weekday','reminder_start','reminder_stop'])['med_intake_time'].apply(list).reset_index(name='med_intake_time')

        
        str_list = ['За следните лекарства има включени напомняния:\n']
        for idx,row in df_gr.iterrows():
            # create the string 'frequency' that says what weekdays the customer has to take the medications
            if row.weekday == '0123456':
                frequency = 'всеки ден'
            else:
                frequency =  ', '.join(num2wday[day_num] for day_num in row.weekday)
                
            # calculate the days since the start of the reminder_start
            time_delta = datetime.datetime.now(pytz.timezone('Europe/Sofia')) - row.reminder_start
            days_of_service = time_delta.days

            med_and_doses =  f'{row.medicine}, ден {days_of_service} от услугата: напомняния {frequency} в ' + ', '.join(row.med_intake_time) + '\n'
            str_list.append(med_and_doses)
            
        resp.message(''.join(str_list))
        
    if body.lower() == 'lekarstva' or body.lower() == 'лекарства':
        #sends message of the kind:
        # “Детайли за Вашите лекарства:
        # Амидофен, всеки ден, от 06/10/2020 до 14/10/2020: 1 хапче от 2 мг в 09:00, 2 хапчета от 2 мг в 15:00, 1 хапче от 2 мг в 21:00
        # Валериан (06/10/2020-14/10/2020, вторник и петък): 1 хапче от 2 мг в 09:00, 1 хапче от 2 мг в 17:00.
        
        # select only medications with reminder flag == 1
        df = df[df.reminder_flag == 1]

        df['dose+time'] = df.dose + ' в ' + df.med_intake_time
        df_gr = df.groupby(['medicine','weekday','reminder_start','reminder_stop'])['dose+time'].apply(list).reset_index(name='dose+time')

        str_list = ['Детайли за Вашите лекарства:\n']
        for idx,row in df_gr.iterrows():
            # create the string 'frequency' that says what weekdays the customer has to take the medications
            if row.weekday == '0123456':
                frequency = 'всеки ден'
            else:
                frequency =  ', '.join(num2wday[day_num] for day_num in row.weekday)

            med_and_doses =  f'{row.medicine}, {frequency}, {row.reminder_start.strftime("%d.%m.%y")}-{row.reminder_stop.strftime("%d.%m.%y")}: ' + ', '.join(row['dose+time']) + '\n'
            str_list.append(med_and_doses)
            
        resp.message(''.join(str_list))
        
        
    if body.lower() == 'istoriya' or body.lower() == 'история':
        # is like 'lekasrstva' from above, but shows instead of current medications the ones you have taken previously
        #sends message of the kind:
        # “Преди сте приемали следните лекарства:
        # Амидофен, всеки ден, от 06/10/2020 до 14/10/2020: 1 хапче от 2 мг в 09:00, 2 хапчета от 2 мг в 15:00, 1 хапче от 2 мг в 21:00
        # Валериан (06/10/2020-14/10/2020, вторник и петък): 1 хапче от 2 мг в 09:00, 1 хапче от 2 мг в 17:00.
        
        # select only medications with reminder flag == 1
        df = df[df.reminder_flag == 0]

        df['dose+time'] = df.dose + ' в ' + df.med_intake_time
        df_gr = df.groupby(['medicine','weekday','reminder_start','reminder_stop'])['dose+time'].apply(list).reset_index(name='dose+time')

        str_list = ['Преди сте приемали следните лекарства:\n']
        for idx,row in df_gr.iterrows():
            # create the string 'frequency' that says what weekdays the customer has to take the medications
            if row.weekday == '0123456':
                frequency = 'всеки ден'
            else:
                frequency =  ', '.join(num2wday[day_num] for day_num in row.weekday)

            med_and_doses =  f'{row.medicine}, {frequency}, {row.reminder_start.strftime("%d.%m.%y")}-{row.reminder_stop.strftime("%d.%m.%y")}: ' + ', '.join(row['dose+time']) + '\n'
            str_list.append(med_and_doses)
            
        str_list.append('За детайли относно лекарствата, които взимате сега отговорете LEKARSTVA')
        resp.message(''.join(str_list))
        
        
    
    if 'info-' in body.lower() or 'инфо-' in body.lower():
        # if the message contains 'info' string of some kind strip it and make the letters lower case
        stripped_str = body.lstrip('info-').lstrip('INFO-').lstrip('ИНФО-').lstrip('инфо-').lower()

        # check if the residual string is contained in the columns 'medicine' or the latinized version 'med_latinized'
        if df.medicine.str.contains(stripped_str).any() or df.med_latinized.str.contains(stripped_str).any():
            
            # get the link to the medicine, depending on in what column it is located
            try:
                link = df.link[df.medicine == stripped_str].iloc[0]
            except:
                link = df.link[df.med_latinized == stripped_str].iloc[0]

            resp.message(f'Вижте тук листовка към лекарсвото {stripped_str}: {link} \nАко имате въпроси или проблеми с Вашето лекарство обърнете се към Вашия лекар или фармацевт.')
            
        else:
            all_meds_of_customer = ', '.join(df.medicine.unique())
            # if the string is not contained we tell the customer, that he has missspelled the medicine
            resp.message(f'Зададеното от Вас лекарство {stripped_str} не e измежду въведените Ваши лекарства - {all_meds_of_customer}')
            
    
    # this is to stop not all the medications of the patient, but only a selected one, e.g. 'стоп-аспирин'
    if 'stop-' in body.lower() or 'стоп-' in body.lower():
        # if the message contains 'stop' string of some kind strip it and make the letters lower case
        stripped_str = body.lower().lstrip('stop-').lstrip('стоп-')

        # check if the residual string is contained in the columns 'medicine' or the latinized version 'med_latinized'
        if df.medicine.str.contains(stripped_str).any() or df.med_latinized.str.contains(stripped_str).any():
            
            # get the link to the medicine, depending on in what column it is located
            try:
                # set all the reminder flags of this patient to 0 and save the update df0 to the file
                df0.reminder_flag[(df0.phone_num == phone_num) & (df0.medicine == stripped_str)] = 0
                # update also the column of the stop date with the current date
                df0.reminder_stop[(df0.phone_num == phone_num) & (df0.medicine == stripped_str)] = pytz.timezone("Europe/Sofia").localize(datetime.datetime.now())
                # you also need to update the current working version of the dataframe (df)
                df.reminder_flag[(df.phone_num == phone_num) & (df.medicine == stripped_str)] = 0
                df.reminder_stop[(df.phone_num == phone_num) & (df.medicine == stripped_str)] = pytz.timezone("Europe/Sofia").localize(datetime.datetime.now())
                # update the changes also the the original file itself
                df0.to_csv(file_path, index=False, date_format="%d.%m.%y")
                
            # this is for the case that the client types the medicine in latin, instead of cyrillic, e.g. amidofen, instead of амидофен 
            except:
                df0.reminder_flag[(df0.phone_num == phone_num) & (df0.med_latinized == stripped_str)] = 0
                # update also the column of the stop date with the current date
                df0.reminder_stop[(df0.phone_num == phone_num) & (df0.med_latinized == stripped_str)] = pytz.timezone("Europe/Sofia").localize(datetime.datetime.now())
                # you also need to update the current working version of the dataframe (df)
                df.reminder_flag[(df.phone_num == phone_num) & (df.med_latinized == stripped_str)] = 0
                df.reminder_stop[(df.phone_num == phone_num) & (df.med_latinized == stripped_str)] = pytz.timezone("Europe/Sofia").localize(datetime.datetime.now())
                # update the changes also the the original file itself
                df0.to_csv(file_path, index=False, date_format="%d.%m.%y")

            resp.message(f'Успешно прекратихте Вашите напомнянията за {stripped_str}!')
            
        else:
            all_meds_of_customer = ', '.join(df.medicine.unique())
            # if the string is not contained we tell the customer, that he has missspelled the medicine
            resp.message(f'Зададеното от Вас лекарство {stripped_str} не e измежду въведените Ваши лекарства - {all_meds_of_customer}')
            
   
    if body.lower() == 'kontakt' or body.lower() == 'контакт':
        m = f'Клиент с номер {phone_num} запита контакт с нас, свържи се с него!'
        message = client.messages.create(body=m, from_= happ_num1, to=happ_num2)
        

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
