from signal import signal, SIGINT
from os import path as ospath, remove as osremove, execl as osexecl
from subprocess import run as srun, check_output
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time
from time import time
from sys import executable
from telegram.ext import CommandHandler

from telegram import ParseMode, InlineKeyboardMarkup
from bot import bot, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, AUTHORIZED_CHATS, TIMEZONE, LOGGER, Interval, INCOMPLETE_TASK_NOTIFIER, DB_URI, app, main_loop
from .helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.ext_utils.db_handler import DbManger
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker
from .modules import authorize, list, cancel_mirror, mirror_status, mirror_leech, clone, ytdlp, shell, eval, delete, count, leech_settings, search, rss, bt_select, speedtest, button
from datetime import datetime, timedelta
import pytz



def stats(update, context):
    if ospath.exists('.git'):
        last_commit = check_output(["git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'"], shell=True).decode()
    else:
        last_commit = 'No UPSTREAM_REPO'
    total, used, free, disk = disk_usage('/')
    swap = swap_memory()
    memory = virtual_memory()
    stats = f'<b>Commit Date:</b> {last_commit}\n\n'\
            f'<b>Bot Uptime:</b> {get_readable_time(time() - botStartTime)}\n'\
            f'<b>OS Uptime:</b> {get_readable_time(time() - boot_time())}\n\n'\
            f'<b>Total Disk Space:</b> {get_readable_file_size(total)}\n'\
            f'<b>Used:</b> {get_readable_file_size(used)} | <b>Free:</b> {get_readable_file_size(free)}\n\n'\
            f'<b>Upload:</b> {get_readable_file_size(net_io_counters().bytes_sent)}\n'\
            f'<b>Download:</b> {get_readable_file_size(net_io_counters().bytes_recv)}\n\n'\
            f'<b>CPU:</b> {cpu_percent(interval=0.5)}%\n'\
            f'<b>RAM:</b> {memory.percent}%\n'\
            f'<b>DISK:</b> {disk}%\n\n'\
            f'<b>Physical Cores:</b> {cpu_count(logical=False)}\n'\
            f'<b>Total Cores:</b> {cpu_count(logical=True)}\n\n'\
            f'<b>SWAP:</b> {get_readable_file_size(swap.total)} | <b>Used:</b> {swap.percent}%\n'\
            f'<b>Memory Total:</b> {get_readable_file_size(memory.total)}\n'\
            f'<b>Memory Free:</b> {get_readable_file_size(memory.available)}\n'\
            f'<b>Memory Used:</b> {get_readable_file_size(memory.used)}\n'
    sendMessage(stats, context.bot, update.message)


def start(update, context):
    buttons = ButtonMaker()
    buttons.buildbutton("Owner", "https://www.github.com/amirulandalib")
    reply_markup = buttons.build_menu(2)
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f'''
This bot can mirror all your links to Google Drive or to telegram!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
        sendMarkup(start_string, context.bot, update.message, reply_markup)
    else:
        sendMarkup('Not an Authorized user, deploy your own mirror-leech bot', context.bot, update.message, reply_markup)

def restart(update, context):
    restart_message = sendMessage("Restarting...", context.bot, update.message)
    if Interval:
        Interval[0].cancel()
        Interval.clear()
    clean_all()
    srun(["pkill", "-9", "-f", "gunicorn|aria2c|qbittorrent-nox|ffmpeg"])
    srun(["npx", "kill-port", "80"])
    srun(["npx", "kill-port", "8090"])
    srun(["killall", "node"])
    srun(["python3", "update.py"])
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    osexecl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update.message)
    end_time = int(round(time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update.message)

help_string = f'''
NOTE: Try each command without any perfix to see more detalis.
/{BotCommands.MirrorCommand[1]}: Start mirroring to Google Drive.
/{BotCommands.ZipMirrorCommand[1]}: Start mirroring and upload the file/folder compressed with zip extension.
/{BotCommands.UnzipMirrorCommand[1]}: Start mirroring and upload the file/folder extracted from any archive extension.
/{BotCommands.QbMirrorCommand[1]}: Start Mirroring to Google Drive using qBittorrent.
/{BotCommands.QbZipMirrorCommand[1]}: Start mirroring using qBittorrent and upload the file/folder compressed with zip extension.
/{BotCommands.QbUnzipMirrorCommand[1]}: Start mirroring using qBittorrent and upload the file/folder extracted from any archive extension.
/{BotCommands.YtdlCommand[1]}: Mirror yt-dlp supported link.
/{BotCommands.YtdlZipCommand[1]}: Mirror yt-dlp supported link as zip.
/{BotCommands.LeechCommand[1]}: Start leeching to Telegram.
/{BotCommands.ZipLeechCommand[1]}: Start leeching and upload the file/folder compressed with zip extension.
/{BotCommands.UnzipLeechCommand[1]}: Start leeching and upload the file/folder extracted from any archive extension.
/{BotCommands.QbLeechCommand[1]}: Start leeching using qBittorrent.
/{BotCommands.QbZipLeechCommand[1]}: Start leeching using qBittorrent and upload the file/folder compressed with zip extension.
/{BotCommands.QbUnzipLeechCommand[1]}: Start leeching using qBittorrent and upload the file/folder extracted from any archive extension.
/{BotCommands.YtdlLeechCommand[1]}: Leech yt-dlp supported link.
/{BotCommands.YtdlZipLeechCommand[1]}: Leech yt-dlp supported link as zip.
/{BotCommands.CloneCommand} [drive_url]: Copy file/folder to Google Drive.
/{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive.
/{BotCommands.DeleteCommand} [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo).
/{BotCommands.LeechSetCommand} [query]: Leech settings.
/{BotCommands.SetThumbCommand}: Reply photo to set it as Thumbnail.
/{BotCommands.BtSelectCommand}: Select files from torrents by gid or reply.
/{BotCommands.RssListCommand[1]}: List all subscribed rss feed info (Only Owner & Sudo).
/{BotCommands.RssGetCommand[1]}: Force fetch last N links (Only Owner & Sudo).
/{BotCommands.RssSubCommand[1]}: Subscribe new rss feed (Only Owner & Sudo).
/{BotCommands.RssUnSubCommand[1]}: Unubscribe rss feed by title (Only Owner & Sudo).
/{BotCommands.RssSettingsCommand[1]} [query]: Rss Settings (Only Owner & Sudo).
/{BotCommands.CancelMirror}: Cancel task by gid or reply.
/{BotCommands.CancelAllCommand} [query]: Cancel all [status] tasks.
/{BotCommands.ListCommand} [query]: Search in Google Drive(s).
/{BotCommands.SearchCommand} [query]: Search for torrents with API.
/{BotCommands.StatusCommand}: Shows a status of all the downloads.
/{BotCommands.StatsCommand}: Show stats of the machine where the bot is hosted in.
/{BotCommands.PingCommand}: Check how long it takes to Ping the Bot (Only Owner & Sudo).
/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.AuthorizedUsersCommand}: Show authorized users (Only Owner & Sudo).
/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner).
/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner).
/{BotCommands.SpeedTestCommand}: Check network speed of the server.
/{BotCommands.RestartCommand}: Restart and update the bot (Only Owner & Sudo).
/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports (Only Owner & Sudo).
/{BotCommands.ShellCommand}: Run shell commands (Only Owner).
/{BotCommands.EvalCommand}: Run Python Code Line | Lines (Only Owner).
/{BotCommands.ExecCommand}: Run Commands In Exec (Only Owner).
/{BotCommands.ClearLocalsCommand}: Clear {BotCommands.EvalCommand} or {BotCommands.ExecCommand} locals (Only Owner).
'''

def bot_help(update, context):
    sendMessage(help_string, context.bot, update.message)

botcmds = [

        (f'{BotCommands.HelpCommand}','Get Detailed Help.'),
        (f'{BotCommands.MirrorCommand[1]}','Start mirroring to Google Drive.'),
        (f'{BotCommands.ZipMirrorCommand[1]}','Start mirroring and upload the file/folder compressed with zip extension.'),
        (f'{BotCommands.UnzipMirrorCommand[1]}','Start mirroring and upload the file/folder extracted from any archive extension.'),
        (f'{BotCommands.QbMirrorCommand[1]}','Start Mirroring to Google Drive using qBittorrent.'),
        (f'{BotCommands.QbZipMirrorCommand[1]}','Start mirroring using qBittorrent and upload the file/folder compressed with zip extension.'),
        (f'{BotCommands.QbUnzipMirrorCommand[1]}','Start mirroring using qBittorrent and upload the file/folder extracted from any archive extension.'),
        (f'{BotCommands.YtdlCommand[1]}','Mirror yt-dlp supported link.'),
        (f'{BotCommands.YtdlZipCommand[1]}','Mirror yt-dlp supported link as zip.'),
        (f'{BotCommands.LeechCommand[1]}','Start leeching to Telegram.'),
        (f'{BotCommands.ZipLeechCommand[1]}','Start leeching and upload the file/folder compressed with zip extension.'),
        (f'{BotCommands.UnzipLeechCommand[1]}','Start leeching and upload the file/folder extracted from any archive extension.'),
        (f'{BotCommands.QbLeechCommand[1]}','Start leeching using qBittorrent.'),
        (f'{BotCommands.QbZipLeechCommand[1]}','Start leeching using qBittorrent and upload the file/folder compressed with zip extension.'),
        (f'{BotCommands.QbUnzipLeechCommand[1]}','Start leeching using qBittorrent and upload the file/folder extracted from any archive extension.'),
        (f'{BotCommands.YtdlLeechCommand[1]}','Leech yt-dlp supported link.'),
        (f'{BotCommands.YtdlZipLeechCommand[1]}','Leech yt-dlp supported link as zip.'),
        (f'{BotCommands.CloneCommand}','[drive_url] Copy file or folder to Google Drive.'),
        (f'{BotCommands.CountCommand}','[drive_url] - Count file or folder of Google Drive.'),
        (f'{BotCommands.DeleteCommand}','[drive_url] - Delete file or folder from Google Drive (Only Owner & Sudo).'),
        (f'{BotCommands.LeechSetCommand}','[query] - Leech settings.'),
        (f'{BotCommands.SetThumbCommand}','Reply photo to set it as Thumbnail.'),
        (f'{BotCommands.BtSelectCommand}','Select files from torrents by gid or reply.'),
        (f'{BotCommands.RssListCommand[1]}','List all subscribed rss feed info (Only Owner & Sudo).'),
        (f'{BotCommands.RssGetCommand[1]}','Force fetch last N links (Only Owner & Sudo).'),
        (f'{BotCommands.RssSubCommand[1]}','Subscribe new rss feed (Only Owner & Sudo).'),
        (f'{BotCommands.RssUnSubCommand[1]}','Unubscribe rss feed by title (Only Owner & Sudo).'),
        (f'{BotCommands.RssSettingsCommand[1]}','[query] - Rss Settings (Only Owner & Sudo).'),
        (f'{BotCommands.CancelMirror}','Cancel task by gid or reply.'),
        (f'{BotCommands.CancelAllCommand}','[query] - Cancel all [status] tasks.'),
        (f'{BotCommands.ListCommand}','[query] - Search in Google Drive(s).'),
        (f'{BotCommands.SearchCommand}','[query] - Search for torrents with API.'),
        (f'{BotCommands.StatusCommand}','Shows a status of all the downloads.'),
        (f'{BotCommands.StatsCommand}','Show stats of the machine where the bot is hosted in.'),
        (f'{BotCommands.PingCommand}','Check how long it takes to Ping the Bot (Only Owner & Sudo).'),
        (f'{BotCommands.AuthorizeCommand}','Authorize a chat or a user to use the bot (Only Owner & Sudo).'),
        (f'{BotCommands.UnAuthorizeCommand}','Unauthorize a chat or a user to use the bot (Only Owner & Sudo).'),
        (f'{BotCommands.AuthorizedUsersCommand}','Show authorized users (Only Owner & Sudo).'),
        (f'{BotCommands.AddSudoCommand}','Add sudo user (Only Owner).'),
        (f'{BotCommands.RmSudoCommand}','Remove sudo users (Only Owner).'),
        (f'{BotCommands.SpeedTestCommand}','Check network speed of the server.'),
        (f'{BotCommands.RestartCommand}','Restart and update the bot (Only Owner & Sudo).'),
        (f'{BotCommands.LogCommand}','Get a log file of the bot. Handy for getting crash reports (Only Owner & Sudo).'),
        (f'{BotCommands.ShellCommand}','Run shell commands (Only Owner).'),
        (f'{BotCommands.EvalCommand}','Run Python Code Line | Lines (Only Owner).'),
        (f'{BotCommands.ExecCommand}','Run Commands In Exec (Only Owner).'),
        (f'{BotCommands.ClearLocalsCommand}','Clear Local Downloads.')
    ]

def main():
    bot.set_my_commands(botcmds)
    start_cleanup()
    now=datetime.now(pytz.timezone(f'{TIMEZONE}'))
    date = now.strftime('%d/%m/%y')
    time = now.strftime('%I:%M:%S %p')
    notifier_dict = False
    if INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
        if notifier_dict := DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                if ospath.isfile(".restartmsg"):
                    with open(".restartmsg") as f:
                        chat_id, msg_id = map(int, f)
                    msg = f"<b>🤖 BOT Rebooted 🔄</b>\n"
                    msg += f"<b>\n📅 Date: {date}</b>\n"
                    msg += f"<b>⏰ Time: {time}</b>\n"
                    msg += f"<b>🌃 TimeZone: {TIMEZONE}</b>\n\n"
                    msg += f"<b>ℹ️ Please Re-Download again if Any downloads got Canceled during Reboot</b>\n\n"
                    msg += f"<b>#Rebooted</b>"
             
                else:
                    msg = f"<b>🤖 BOT Rebooted 🔄</b>\n"
                    msg += f"<b>\n📅 Date: {date}</b>\n"
                    msg += f"<b>⏰ Time: {time}</b>\n"
                    msg += f"<b>🌃 TimeZone: {TIMEZONE}</b>\n\n"
                    msg += f"<b>ℹ️ Please Re-Download again if Any downloads got Canceled during Reboot</b>\n\n"
                    msg += f"<b>#Rebooted</b>"

                for tag, links in data.items():
                     msg += f"\n{tag}: "
                     for index, link in enumerate(links, start=1):
                         msg += f" <a href='{link}'>{index}</a> |"
                         if len(msg.encode()) > 4000:
                             if 'Restarted successfully' in msg and cid == chat_id:
                                 bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTML', disable_web_page_preview=True)
                                 osremove(".restartmsg")
                             else:
                                 try:
                                     bot.sendMessage(cid, msg, 'HTML', disable_web_page_preview=True)
                                 except Exception as e:
                                     LOGGER.error(e)
                             msg = ''
                if 'Restarted successfully' in msg and cid == chat_id:
                     bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTML', disable_web_page_preview=True)
                     osremove(".restartmsg")
                else:
                    try:
                        bot.sendMessage(cid, msg, 'HTML', disable_web_page_preview=True)
                    except Exception as e:
                        LOGGER.error(e)
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        msg = f"Restarted successfully"
        bot.edit_message_text(msg, chat_id, msg_id)
        osremove(".restartmsg")
    elif not notifier_dict and AUTHORIZED_CHATS:
        text = f"<b>🤖 BOT Rebooted 🔄</b>\n<b>\n📅 Date: {date}</b>\n<b>⏰ Time: {time}</b>\n<b>🌃 TimeZone: {TIMEZONE}</b>\n\n<b>ℹ️ Please Re-Download again if Any downloads got Canceled during Reboot</b>\n\n<b>#Rebooted</b>"
        for id_ in AUTHORIZED_CHATS:
            try:
                bot.sendMessage(chat_id=id_, text=text, parse_mode=ParseMode.HTML)
            except Exception as e:
                LOGGER.error(e)

    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal(SIGINT, exit_clean_up)

app.start()
main()

main_loop.run_forever()
