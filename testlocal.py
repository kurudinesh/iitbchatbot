import os
from jproperties import Properties

configs = Properties()
with open('app-config.properties', 'rb') as config_file:
    configs.load(config_file)
os.environ["DB_USER"] = configs.get("DB_USER").data
os.environ["DB_PASS"] = configs.get("DB_PASS").data
os.environ["DB_NAME"] = configs.get("DB_NAME").data
os.environ["DB_HOST"] = configs.get("DB_HOST").data
os.environ["TOKEN"] = configs.get("TOKEN").data
os.environ["CHAT_ID"] = configs.get("CHAT_ID").data
os.environ['ADMIN_CHAT_ID'] =  configs.get("ADMIN_CHAT_ID").data
os.environ['URL'] = configs.get("URL").data
from bot import *
import threading

# recording_on = Value('b', True)
p = threading.Thread(target=localpoll, args=(cbot,))
p.start()

print("running app")
server.run(threaded=True)
p.join()

