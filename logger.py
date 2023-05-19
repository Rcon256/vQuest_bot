import datetime
starttime = str(datetime.datetime.now().strftime("%d-%m-%YT%H-%M-%S"))

def log(message):
    try:
        print(str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " Сообщение от {0} {1} (id = {2}) \n {3}".format(message.from_user.first_name,
                                                        message.from_user.last_name,
                                                        str(message.from_user.id), message.text))
        with open(f'log/{starttime}.log', 'a') as l:
            l.write(str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " Сообщение от {0} {1} (id = {2}) \n {3}\n".format(message.from_user.first_name,
                                                        message.from_user.last_name,
                                                        str(message.from_user.id), message.text))
    except Exception as err:
        print(err)
        print(str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " Inline-Сообщение от {0} {1} (id = {2}) \n {3}".format(message.from_user.first_name,
                                                      message.from_user.last_name,
                                                      str(message.from_user.id), message.query))
        with open(f'log/{starttime}.log', 'a') as l:
            l.write(str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " Inline-Сообщение от {0} {1} (id = {2}) \n {3}\n".format(message.from_user.first_name,
                                                        message.from_user.last_name,
                                                        str(message.from_user.id), message.query))
    
def logCB(message):
    print(str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " Сообщение от {0} {1} (id = {2}) \n {3}  - {4}".format(message.from_user.first_name,
                                                        message.from_user.last_name,
                                                        str(message.from_user.id), message.data, message.message.text.split('\n')[0]))
    with open(f'log/{starttime}.log', 'a') as l:
        l.write(str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) + " Сообщение от {0} {1} (id = {2}) \n {3} - {4}\n".format(message.from_user.first_name,
                                                    message.from_user.last_name,
                                                    str(message.from_user.id), message.data, message.message.text.split('\n')[0]))    