import time
import telebot
from flask import Flask, request
import os
import logging


TOKEN = "1652615625:AAEnvDdQ0yNEZRnmMsJpRkA-IGyVP0UFfiY"
bot = telebot.TeleBot(token=TOKEN)
server = Flask(__name__)
CHAT_ID = -545625132
ADMIN_CHAT_ID = 275290631
# USER_ID = 275290631
userids = set()
submsgsentids = set()

server.logger.disabled = True
logging.getLogger("requests").setLevel(logging.FATAL)
logging.getLogger('werkzeug').disabled = True
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

@bot.message_handler(commands=['start']) # welcome message handler
def send_welcome(message):
    bot.reply_to(message, 'Hi, I will help you in posting your messages in confession@iitb group anonymously')

@bot.message_handler(commands=['help']) # help message handler
def send_welcome(message):
    bot.reply_to(message, 'Send your message to be sent anonymously')

@bot.message_handler(content_types=["new_chat_members"])
def foo(message):
    for user in message.new_chat_members:
        userids.add(user.id)
    print('new members added')
    bot.reply_to(message, "welcome")

@bot.message_handler(content_types=["left_chat_member","kick_chat_member"])
def foo(message):
    # bot.reply_to(message, "Bye")
    uid = message.left_chat_member.id
    userids.remove(uid)
    if uid in userids:
        print("user not removed")
    else:
        print("user removed with id {}".format(uid))

@bot.message_handler(func=lambda message: message.chat.type=="private")
def echo_message(message):
    try:
        userid = message.from_user.id
        sub = False
        if userid in userids:
            # print("user not removed")
            sub = True
        else:
            if is_subscribed(CHAT_ID,userid):
                # print("user subscribed with id {}".format(userid))
                userids.add(userid)
                sub = True
        if sub:
            bot.send_message(CHAT_ID, message.text)
            bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
        elif userid not in submsgsentids:
            bot.reply_to(message, 'Please subscribe to the channel')
            submsgsentids.add(userid)
    except Exception as e:
        print(e)

def is_subscribed(chat_id, user_id):
    try:
        var = bot.get_chat_member(chat_id, user_id)
        if var.status == 'left':
            return False
        return True
    except Exception as e:
        if e.result_json['description'] == 'Bad Request: user not found':
            bot.send_message(CHAT_ID, 'Please subscribe to the channel')
            return False



# bot.delete_webhook()
# while True:
#     try:
#         bot.polling(none_stop=True)
#         # ConnectionError and ReadTimeout because of possible timout of the requests library
#         # maybe there are others, therefore Exception
#     except Exception:
#         time.sleep(15)
#         bot.stop_polling()
#         bot.stop_bot()
#
#
#
#
@server.route('/{}'.format(TOKEN), methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    bot.remove_webhook()
    url = 'https://iitbchatbot.et.r.appspot.com/'
    # url = 'https://boiling-island-24259.herokuapp.com/'
    s = bot.set_webhook('{URL}{HOOK}'.format(URL=url, HOOK=TOKEN))
    if s:
       return "webhook setup ok"
    else:
       return "webhook setup failed"


@server.route('/', methods=['GET', 'POST'])
def index():
    return '.'

if __name__ == '__main__':
    # note the threaded arg which allow
    # your app to have more than one thread
    server.run(threaded=True)