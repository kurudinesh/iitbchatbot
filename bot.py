import time
import telebot
from flask import Flask, request
import os


TOKEN = "1615092091:AAGxLgfkhUpiinHyRe8s0Z-JnqqEJlNL9cA"
bot = telebot.TeleBot(token=TOKEN)
server = Flask(__name__)


def findat(msg):
    # from a list of texts, it finds the one with the '@' sign
    for i in msg:
        if '@' in i:
            return i

@bot.message_handler(commands=['start']) # welcome message handler
def send_welcome(message):
    bot.reply_to(message, '(placeholder text)')

@bot.message_handler(commands=['help']) # help message handler
def send_welcome(message):
    bot.reply_to(message, 'ALPHA = FEATURES MAY NOT WORK')

@bot.message_handler(func=lambda msg: msg.text is not None and '@' in msg.text)
# lambda function finds messages with the '@' sign in them
# in case msg.text doesn't exist, the handler doesn't process it
def at_converter(message):
    texts = message.text.split()
    at_text = findat(texts)
    if at_text == '@': # in case it's just the '@', skip
        pass
    else:
        insta_link = "https://instagram.com/{}".format(at_text[1:])
        bot.reply_to(message, insta_link)

# while True:
#     try:
#         bot.polling(none_stop=True)
#         # ConnectionError and ReadTimeout because of possible timout of the requests library
#         # maybe there are others, therefore Exception
#     except Exception:
#         time.sleep(15)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)


@server.route('/{}'.format(TOKEN), methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


# @server.route("/")
# def webhook():
#     bot.remove_webhook()
#     bot.set_webhook(url='http://127.0.0.1:5000/' + TOKEN)
#     print('web hook is set')
#     return "!", 200

@server.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    bot.remove_webhook()
    s = bot.set_webhook('{URL}{HOOK}'.format(URL='https://boiling-island-24259.herokuapp.com/', HOOK=TOKEN))
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