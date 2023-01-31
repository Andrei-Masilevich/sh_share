import asyncio
import logging
import os
import sys
import telebot
import yaml

from optparse import OptionParser, OptionValueError
import os.path as ps
from string import Template

L = logging.getLogger("TeleBot")

class Configuration(object):
    
    def __init__(self, 
                 telegram_bot_token: str, 
                 telegram_channel_id: str, 
                 commands: map):
        self._telegram_bot_token = telegram_bot_token
        self._telegram_channel_id = telegram_channel_id
        self._commands = commands
        
    @property
    def commands(self):
        return list(self._commands.keys())
    
    @property
    def auth_token(self):
        return self._telegram_bot_token

    @property
    def channel_id(self):
        return self._telegram_channel_id
    
    def get_response(self, command: str):
        return self._commands.get(command)


class CONFIG_YAML_FORMAT:
    NOTIFY = "notify"
    NOTIFY_MESSAGE = "message"
    TELEGRAM = "telegram"
    # https://t.me/BotFather
    # @BotFather
    TELEGRAM_BOT_TOKEN = "bot_token"
    # https://api.telegram.org/bot{}/getUpdates to get channel ID
    # Look at:
    # https://telegram-bot-sdk.readme.io/reference/getupdates
    #
    TELEGRAM_CHANNEL_ID = "channel_id"

def read_config(config_path: str, options):
    try:
        with open(config_path, 'r') as f:
            yaml_tpl_str = f.read()
            
            if options.command:
                yaml_tpl_str = Template(yaml_tpl_str).safe_substitute(
                    NOTIFY_COMMAND = options.command)
            if options.message:
                yaml_tpl_str = Template(yaml_tpl_str).safe_substitute(
                    NOTIFY_MESSAGE = options.message)
            if options.telegram_bot_token:
                yaml_tpl_str = Template(yaml_tpl_str).safe_substitute(
                    TELEGRAM_BOT_TOKEN = options.telegram_bot_token)
            if options.telegram_channel_id:
                yaml_tpl_str = Template(yaml_tpl_str).safe_substitute(
                    TELEGRAM_CHANNEL_ID = options.telegram_channel_id)
                
            assert yaml_tpl_str.find('$') < 0, "Insufficient arguments in configuration file"
            
            parsed_yaml = yaml.safe_load(yaml_tpl_str)
            assert parsed_yaml, "Can't parse YAML"
            
            telegram_coinfig = parsed_yaml.get(CONFIG_YAML_FORMAT.TELEGRAM)
            assert telegram_coinfig, "There is no %r key" % (CONFIG_YAML_FORMAT.TELEGRAM)
            telegram_bot_tocken = telegram_coinfig.get(CONFIG_YAML_FORMAT.TELEGRAM_BOT_TOKEN)
            assert telegram_bot_tocken, "There is no %r key" % (CONFIG_YAML_FORMAT.TELEGRAM_BOT_TOKEN)
            telegram_channel_id = telegram_coinfig.get(CONFIG_YAML_FORMAT.TELEGRAM_CHANNEL_ID)
            assert telegram_channel_id, "There is no %r key" % (CONFIG_YAML_FORMAT.TELEGRAM_CHANNEL_ID)
            
            commands_yaml = parsed_yaml.get(CONFIG_YAML_FORMAT.NOTIFY)
            assert commands_yaml, "There is no %r key" % (CONFIG_YAML_FORMAT.NOTIFY)
            commands = {}
            for command in commands_yaml:
                for command_item_ in command.items():
                    (command_name, command_definition) = command_item_
                    break
                command_message = command_definition.get(CONFIG_YAML_FORMAT.NOTIFY_MESSAGE)
                assert command_message, "There is no %r key" % (CONFIG_YAML_FORMAT.NOTIFY_MESSAGE)
                commands[command_name] = command_message
            
            return Configuration(telegram_bot_tocken, telegram_channel_id, commands)
    except BaseException as err:
        raise OptionValueError("Invalid format of %r: %s" % (config_path, err))

    return None


def main():

    try:
        usage = "usage: %prog [options] (config path)"
        parser = OptionParser(usage=usage, 
                              description="This Bot responses for configured command posted in the channel")
        
        parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                          help="Command to emit message response to private channel.")
        parser.add_option("--command", type='str', dest="command",
                          help="Command to emit message response to private channel.")
        parser.add_option("--message", type='str', dest="message",
                          help="Message that corresponds to command.")
        parser.add_option("--telegram-bot-token", type='str', dest="telegram_bot_token", 
                          help="Authorization token for Telegram bot that will communicate to the channel.")
        parser.add_option("--telegram-channel-id", type='str', dest="telegram_channel_id", 
                          help="Telegram channel ID to communicate with bot.")
        (options, args) = parser.parse_args()
        
        if any(args):
            config_file = args[0]
        else:
            config_file = ps.abspath(ps.join(ps.dirname(__file__), "..", "notify.tpl.yaml"))
        
        configuration = read_config(config_file, options)
        
        if options.debug:
            L.setLevel("DEBUG")

        bot = telebot.TeleBot(configuration.auth_token)
    except SystemExit as err:
        return err.code
    except BaseException as err:
        L.error("Invalid configuration: %s", err)
        return 1

    @bot.channel_post_handler(commands=configuration.commands)
    def send_response(message):
        if message.chat.id == configuration.channel_id:
            response = configuration.get_response(message.text[1:])
            if response:
                bot.reply_to(message, response)
    
    async def async_polling():
        bot.polling()
        await asyncio.sleep(0.1)
        
    try:
        asyncio.run(async_polling())
    except KeyboardInterrupt:
        pass
    except BaseException as err:
        L.error("%s", err)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())