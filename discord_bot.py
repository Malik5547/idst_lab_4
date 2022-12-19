#!./.venv/bin/python

import discord  # base discord module
import code  # code.interact
import os  # environment variables
import inspect  # call stack inspection
import random  # dumb random number generator
import asyncio

from discord.ext import commands  # Bot class and utils


################################################################################
############################### HELPER FUNCTIONS ###############################
################################################################################

# log_msg - fancy print
#   @msg   : string to print
#   @level : log level from {'debug', 'info', 'warning', 'error'}
def log_msg(msg: str, level: str):
    # user selectable display config (prompt symbol, color)
    dsp_sel = {
        'debug': ('\033[34m', '-'),
        'info': ('\033[32m', '*'),
        'warning': ('\033[33m', '?'),
        'error': ('\033[31m', '!'),
    }

    # internal ansi codes
    _extra_ansi = {
        'critical': '\033[35m',
        'bold': '\033[1m',
        'unbold': '\033[2m',
        'clear': '\033[0m',
    }

    # get information about call site
    caller = inspect.stack()[1]

    # input sanity check
    if level not in dsp_sel:
        print('%s%s[@] %s:%d %sBad log level: "%s"%s' % \
              (_extra_ansi['critical'], _extra_ansi['bold'],
               caller.function, caller.lineno,
               _extra_ansi['unbold'], level, _extra_ansi['clear']))
        return

    # print the damn message already
    print('%s%s[%s] %s:%d %s%s%s' % \
          (_extra_ansi['bold'], *dsp_sel[level],
           caller.function, caller.lineno,
           _extra_ansi['unbold'], msg, _extra_ansi['clear']))


################################################################################
############################## BOT IMPLEMENTATION ##############################
################################################################################

# bot instantiation
description = '''My discoord bot.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(command_prefix='!',  description=description, intents=intents)


# on_ready - called after connection to server is established
@bot.event
async def on_ready():
    log_msg('logged on as <%s>' % bot.user, 'info')


# on_message - called when a new message is posted to the server
#   @msg : discord.message.Message
@bot.event
async def on_message(msg):
    #code.interact(local=dict(globals(), **locals()))

    # filter out our own messages
    if msg.author == bot.user:
       return

    log_msg('message from <%s>: "%s"' % (msg.author, msg.content), 'debug')

    # overriding the default on_message handler blocks commands from executing
    # manually call the bot's command processor on given message
    await bot.process_commands(msg)


# on_voice_state_update
#   @msg : discord.message.Message
@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        return

    if len(voice_state.channel.members) == 1:
        await  voice_state.disconnect()

# roll - rng chat command
#   @ctx     : command invocation context
#   @max_val : upper bound for number generation (must be at least 1)
@bot.command(brief='Generate random number between 1 and <arg>')
async def roll(ctx, max_val: int):
    # argument sanity check
    if max_val < 1:
        raise Exception('argument <max_val> must be at least 1')

    await ctx.send(random.randint(1, max_val))


# Plays a song from local filesystem
@bot.command(brief='Play a song from local filesystem')
async def play(ctx, query):
    """Plays a file from the local filesystem"""

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    if ctx.message.guild.voice_client is None:
        channel = ctx.message.author.voice.channel
        await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source="/home/student/Music/" + query + ".mp3", options="-b:a 160k"))
    voice_channel.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

    await ctx.send(f'Now playing: {query}')


# List available songs
@bot.command(brief='List all available songs')
async def list(ctx):
    #dir_path, dir_names, files = os.walk('/home/student/Music/')

    await ctx.send(f'Songs: ')
    for _, _, files in os.walk('/home/student/Music/'):
        for file in files:
            await ctx.send(f" - {file}")


# Disconect the bot
@bot.command(brief='Disconect the bot from voice chat')
async def scram(ctx):
    ctx.voice_client.stop()

    await ctx.voice_client.disconnect()

# roll_error - error handler for the <roll> command
#   @ctx     : command that crashed invocation context
#   @error   : ...
@roll.error
async def roll_error(ctx, error):
    await ctx.send(str(error))


################################################################################
############################# PROGRAM ENTRY POINT ##############################
################################################################################

if __name__ == '__main__':
    # check that token exists in environment
    if 'BOT_TOKEN' not in os.environ:
        log_msg('save your token in the BOT_TOKEN env variable!', 'error')
        exit(-1)

    # launch bot (blocking operation)
    bot.run(os.environ['BOT_TOKEN'])

