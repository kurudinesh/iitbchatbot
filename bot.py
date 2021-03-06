import time
import telebot
from flask import Flask, request, Response, render_template, jsonify
from flask_paginate import Pagination, get_page_args
import os
import logging
from chatdao import *
from Securemsgs import *
from filtertext import *

TOKEN = os.environ["TOKEN"]
cbot = telebot.TeleBot(token=TOKEN)
server = Flask(__name__)
CHAT_ID = os.environ["CHAT_ID"]
ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]
url = os.environ["URL"]
userids = set()
userids.add(ADMIN_CHAT_ID)
submsgsentids = set()

print("starting bot.py")
loglvl = logging.ERROR
server.logger.setLevel(loglvl)
logging.getLogger("requests").setLevel(loglvl)
logging.getLogger('werkzeug').setLevel(loglvl)
# os.environ['WERKZEUG_RUN_MAIN'] = 'true'

@cbot.message_handler(func=lambda message: message.chat.type == "private", commands=['start']) # welcome message handler
def send_welcome(message):
    cbot.reply_to(message, 'Hi, I will help you in posting your messages in confession@iitb group anonymously')

@cbot.message_handler(func=lambda message: message.chat.type == "private", commands=['help']) # help message handler
def send_welcome(message):
    cbot.reply_to(message, 'Send your message to be sent anonymously')

@cbot.message_handler(content_types=["new_chat_members"])
def foo(message):
    for user in message.new_chat_members:
        userids.add(user.id)
        save_user([user.username, user.id, 1, 0])
    print('new members added')
    cbot.reply_to(message, "welcome")


@cbot.message_handler(content_types=["left_chat_member", "kick_chat_member"])
def foo(message):
    # bot.reply_to(message, "Bye")
    uid = message.left_chat_member.id
    user = message.left_chat_member
    # update_user_status(user.id, 2)

    if uid in userids:
        userids.remove(uid)
        save_user([user.username, user.id, 2, 0])
        print("user removed")
    else:
        print("user removed with id {}".format(uid))

@cbot.message_handler(func=lambda message: message.chat.type == "private")
def echo_message(message):
    try:
        userid = message.from_user.id
        sub = False
        if userid in userids:
            # print("user not removed")
            sub = True
        # else:
        #     if is_subscribed(CHAT_ID,userid):
        #         # print("user subscribed with id {}".format(userid))
        #         userids.add(userid)
        #         sub = True
        if sub:
            text = ""
            if message.from_user.username is not None:
                text = message.from_user.username
            else:
                text = message.from_user.id
            cypher = encryptmsg(text)
            mid = -1
            msgtxt = filtertxt(message.text)
            if cypher is not None:
                mid=save_log(cypher)
                cbot.send_message(CHAT_ID, "#" + str(mid) + " " + msgtxt)
            else:
                cbot.send_message(CHAT_ID, "#" + str(mid) + " " + msgtxt)
            # bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
        elif userid not in submsgsentids:
            cbot.reply_to(message, 'Please subscribe to the channel')
            submsgsentids.add(userid)
    except Exception as e:
        print(e)

def is_subscribed(chat_id, user_id):
    try:
        var = cbot.get_chat_member(chat_id, user_id)
        if var.status == 'left':
            return False
        return True
    except Exception as e:
        if e.result_json['description'] == 'Bad Request: user not found':
            cbot.send_message(CHAT_ID, 'Please subscribe to the channel')
            return False

def call_create_tables():
    create_tables()
    global userids
    userids = loaduserids()
    userids.add(ADMIN_CHAT_ID)


@server.route('/{}'.format(TOKEN), methods=['POST'])
def getMessage():
    cbot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    cbot.remove_webhook()
    global url
    s = cbot.set_webhook('{URL}{HOOK}'.format(URL=url, HOOK=TOKEN))
    if s:
       return "webhook setup ok"
    else:
       return "webhook setup failed"


@server.route('/', methods=['GET', 'POST'])
def index():
    return '.'

@server.route('/afvasfv', methods=['GET', 'POST'])
def setpubgetprkey():

    return Response(getprivatekey(),
                       mimetype="text/plain",
                       headers={"Content-Disposition":
                                    "attachment;filename=prkey.pem"})

@server.route('/asdvasdvasdv', methods=['GET'])
def resetpubkeyhandler():

    return resetpubkey(), 200

@server.route('/username', methods=['GET'])
def username():

    return render_template("getuser.html")

@server.route('/username', methods=['POST'])
def usernamepost():
    uploaded_file = request.files['file']
    mid = request.form["id"]
    encmsg = get_log(mid)
    uname = 'msg id not found'
    if encmsg is not None:
        try:
            if uploaded_file.filename != '':
                key = uploaded_file.read()
                uname = decryptmsg(key,encmsg)
                if uname is not None:
                    aid = save_log_access(mid)
                    if aid < 0:
                        uname = 'msg id not found'
        except Exception as e:
            uname = 'msg id not found'
            print(e)
    return uname


@server.route('/getaccesslogs')
def getaccesslogshandler():
    perpage = 20

    page, perpage, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    startat = page * perpage
    total = getlogscount()
    pagination_users = getaccesslogs(offset,perpage)
    pagination = Pagination(page=page, per_page=perpage,total=total,
                            css_framework='bootstrap4')
    return render_template('accesslogs.html',
                           data=pagination_users,
                           page=page,
                           per_page=perpage,
                           pagination=pagination,
                           )
    # return jsonify(data=getaccesslogs(startat,perpage))

@server.before_first_request
def call_create_tables():
    create_tables()
    global userids
    userids = loaduserids()
    userids.add(int(ADMIN_CHAT_ID))

def localpoll(cbot):
    cbot.delete_webhook()
    # call_create_tables()
    while True:
        try:
            cbot.polling(none_stop=True)
            # ConnectionError and ReadTimeout because of possible timout of the requests library
            # maybe there are others, therefore Exception
        except Exception as e:
            time.sleep(15)
            cbot.stop_polling()
            cbot.stop_bot()
            print(e)


if __name__ == '__main__':

    # note the threaded arg which allow
    # your app to have more than one thread
    print("running app")
    server.run(threaded=True)
