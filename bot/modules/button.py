from telegram.ext import CommandHandler, CallbackQueryHandler

from bot import dispatcher
from bot.helper.telegram_helper import button_build
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMarkup, editMessage, deleteMessage

from .listener import MirrorLeechListener
from .mirror_leech import _mirror_leech
from ._ytdlp import _ytdl

but_dict = {}


def make_button(from_user, msg_id, cmd, iszip=False, extract=False):
    user_id = from_user.id
    name = from_user.full_name
    msg = f"Hey <a href='tg://user?id={user_id}'>{name}</a>, First click if you want to zip the contents or extract as an archive (only one will work at a time) then click destination...\n\n"
    if iszip:
        msg+= 'Note:- File Will be <b>Zipped</b>\n'
        zipbutname = 'Cancel Zipping'
        zipbutdata = 'czip'
        acttxt = 'zip'
    else:
        zipbutname = 'Zip'
        zipbutdata = 'zip' 
        acttxt = 'non'

    if extract:
        msg+= 'Note:- If it is a Archive it will be <b>Extracted</b>\n'
        extractbutname = 'Cancel Extracting'
        extractbutdata = 'cextract'
        acttxt = 'extract'
    else:
        extractbutname = 'Extract'
        extractbutdata = 'extract'
        acttxt = 'non'
    msg+= '<b>Choose where to upload your files:-</b>\n'
    
    buttons = button_build.ButtonMaker()
    buttons.sbutton('To Drive', f'but {msg_id} gdrive {cmd} {acttxt}')
    buttons.sbutton('To Telegram', f'but {msg_id} telegram {cmd} {acttxt}')
    buttons.sbutton(zipbutname, f'but {msg_id} {zipbutdata} {cmd}')
    if not cmd=='ytdlp':
        buttons.sbutton(extractbutname, f'but {msg_id} {extractbutdata} {cmd}')
    buttons.sbutton('Cancel', f'but {msg_id} cancel')
    button = buttons.build_menu(2)

    return msg, button


def mlbutton(update, context):
    message = update.message
    user_id = message.from_user.id
    msg_id = message.message_id
    cmd = update.message.text
    if cmd.startswith(f"/{BotCommands.Aria2cbut}"):
        cmd = 'aria2c'
    elif cmd.startswith(f"/{BotCommands.Qbitbut}"):
        cmd = 'qbit'
    elif cmd.startswith(f"/{BotCommands.Ytdlpbut}"):
        cmd = 'ytdlp'
    else:
        cmd = 'aria2c'
    
    but_dict[msg_id] = [user_id, message]
    msg, inbutton = make_button(message.from_user, msg_id, cmd)
    sendMarkup(msg, context.bot, message, inbutton)


def mlbuttonqb(update, context):
    bot = context.bot
    query = update.callback_query
    message = query.message
    from_user = query.from_user
    user_id = from_user.id
    data = query.data.split(" ")
    but_id = int(data[1])

    try:
        but_info = but_dict[but_id]
        uid = but_info[0]
    except KeyError:
        query.answer(text="Data Not Found")
        return editMessage('<b>Data</b> Not Found', message)

    if user_id != uid:
        return query.answer(text="Don't waste your time!", show_alert=True)
    elif data[2] == 'zip':
        query.answer(text="File Will be Zipped", show_alert=True)
        msg, inbutton = make_button(from_user, data[1], data[3], iszip=True)
        return editMessage(msg, message, inbutton)
    elif data[2] == 'czip':
        query.answer(text="File Will not be Zipped", show_alert=True)
        msg, inbutton = make_button(from_user, data[1], data[3])
        return editMessage(msg, message, inbutton)
    elif data[2] == 'extract':
        query.answer(text="If it is a Archive it will be Extracted", show_alert=True)
        msg, inbutton = make_button(from_user, data[1], data[3], extract=True)
        return editMessage(msg, message, inbutton)
    elif data[2] == 'cextract':
        query.answer(text="File Will not be Extracted", show_alert=True)
        msg, inbutton = make_button(from_user, data[1], data[3])
        return editMessage(msg, message, inbutton)
    elif data[2] in ['gdrive', 'telegram']:
        query.answer('Done!')
        but_message=but_info[1]

        if data[4] == 'zip':
            isZip=True
            extract=False
        elif data[4] == 'extract':
            isZip=False
            extract=True
        else:
            isZip=False
            extract=False
        
        if data[2] == 'telegram':
            isLeech=True
        else:
            isLeech=False
        
        if data[3] == 'aria2c':
            _mirror_leech(bot, but_message, isZip=isZip, extract=extract, isQbit=False, isLeech=isLeech)
        elif data[3] == 'qbit':
            _mirror_leech(bot, but_message, isZip=isZip, extract=extract, isQbit=True, isLeech=isLeech)
        elif data[3] == 'ytdlp':
            _ytdl(bot, but_message, isZip=isZip, isLeech=isLeech)
        else:
            del but_dict[but_id]
            return editMessage('Something Error', message)
        del but_dict[but_id]
        return deleteMessage(bot, message)
    else:
        del but_dict[but_id]
        return editMessage('Canceled...', message)


mltb_handler_1 = CommandHandler(BotCommands.Aria2cbut, mlbutton,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
mltb_handler_2 = CommandHandler(BotCommands.Qbitbut, mlbutton,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
mltb_handler_3 = CommandHandler(BotCommands.Ytdlpbut, mlbutton,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
mltbcb_handler = CallbackQueryHandler(mlbuttonqb, pattern="but", run_async=True)

dispatcher.add_handler(mltb_handler_1)
dispatcher.add_handler(mltb_handler_2)
dispatcher.add_handler(mltb_handler_3)
dispatcher.add_handler(mltbcb_handler)