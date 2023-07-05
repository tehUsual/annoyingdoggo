from discord.ext import commands
from discord import File, Message, Member, VoiceState, VoiceClient
from interval_timer import IntervalTimer
from sound_manager import SoundManager
from googletrans import Translator
import random
import os


# Permissions 238214400
with open("token.txt", "r") as f:
    TOKEN = f.read().strip()

COMPLY_CHANCE = 80
# Admins
with open("admins.txt", "r") as f:
    ADMINS = [int(i.strip()) for i in f if i]


class SoundBot(commands.Bot):
    def __init__(self, command_prefix='-', self_bot=False):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot)
        self.sm = SoundManager('assets/sounds_lib')
        self.it = IntervalTimer()
        self._voice_client = None
        self._debug = False
        self._channel = None
        self.googletrans = None

        self._recorded_author = {}

        self.nicknames = self.load_nicknames()
        self.insults = self.load_insults()
        self.swearwords = self.load_swearwords()
        self.create_translator()
        self.initialize()
        self.add_commands()





    @staticmethod
    def initialize():
        if not os.path.isdir("assets"):
            os.mkdir("assets")
        if not os.path.isdir("assets/uploads"):
            os.mkdir("assets/uploads")
        if not os.path.isdir("assets/removed"):
            os.mkdir("assets/removed")

    @staticmethod
    def load_nicknames():
        with open("assets/nicknames.txt", "rb") as f:
            data = f.read().decode().split('\n')
        return [i.strip() for i in data if i]

    @staticmethod
    def load_insults():
        with open("assets/insults.txt", "rb") as f:
            data = f.read().decode().split('\n')
        return [i.strip() for i in data if i]

    @staticmethod
    def load_swearwords():
        with open("assets/words.dat", "r") as f:
            data = f.read().split('\n')
        return [i.strip() for i in data if i]

    def create_translator(self):
        self.googletrans = Translator(service_urls=['translate.googleapis.com'])

    def translate(self, text, src="no", dest="en") -> str:
        ret = self.googletrans.translate(text, src=src, dest=dest)
        if ret:
            return ret.text
        else:
            return ""

    @staticmethod
    def generate_borks():
        return ' '.join((['Bork'] * random.randint(1, 9))) + "!"

    @staticmethod
    def roll_comply(author_id):
        return author_id in ADMINS or random.randint(0, 100) <= 75

    @staticmethod
    def roll_attack():
        return random.choice(["nickname", "disconnect", "private_insult",
                              "public_insult", "server_deafen", "server_mute"])


    async def on_ready(self):
        print(f'The bot has logged in as {self.user}')


    # async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
    #    if before.channel is None and after.channel is not None:

        # if after.channel.id == [YOUR_CHANNEL_ID]:
        #    await member.guild.system_channel.send("Alarm!")


    # Add commands
    def add_commands(self):
        # ----- On voice channel change


        # ------------------------------------------------------
        # ----- Text
        @self.command(name='hello', help='Responds with many borks.')
        async def greeting(context):
            self._channel = self.get_channel(context.channel)
            # self.sm.add_text_channel(self._channel)
            await context.send(self.generate_borks())


        # ------------------------------------------------------
        # ----- Voice join/leave
        @self.command(name='join', help='Joins your voice channel.')
        async def join_voice(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                # If the author is connected to a voice channel
                if context.author.voice:
                    # If the bot is not already connected
                    if not self._voice_client:
                        voice_channel = context.author.voice.channel
                        self._voice_client = await voice_channel.connect()
                        self.sm.add_voice_client(self._voice_client)
                    # The bot is already connected
                    else:
                        await context.send('I\'m already connected to a voice channel.')
                # Author is not connected to a voice channel
                else:
                    await context.send('Please join a voice channel first.')
            else:
                await context.send(self.generate_borks())

        @self.command(name='leave', help='Disconnects from the current voice channel.')
        async def leave_voice(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                # If the bot is not connected to a voice channel
                if not self._voice_client:
                    await context.send('I\'m not connected to a voice channel.')
                # The bot is connected to a voice channel
                else:
                    if self.it.running():
                        self.it.stop()
                    self._voice_client = None
                    await context.voice_client.disconnect()
            else:
                await context.send(self.generate_borks())


        # ------------------------------------------------------
        # ----- Timer start/stop
        @self.command(name='start', help='Starts the soundboard timer: `<min_dur> <max_dur>`.')
        async def start(context: commands.Context, min_dur, max_dur):
            if self._debug or self.roll_comply(context.author.id):
                # Check if the bot is already in voice
                if context.author.voice:
                    # If the bot is not already connected
                    if not self._voice_client:
                        voice_channel = context.author.voice.channel
                        self._voice_client = await voice_channel.connect()
                        self.sm.add_voice_client(self._voice_client)
                # Author is not connected to a voice channel
                else:
                    await context.send('Please join a voice channel first.')

                # Verify parameters
                try:
                    _min_dur = int(min_dur)
                    _max_dur = int(max_dur)
                except ValueError as e:
                    await context.send('Starts the soundboard timer: `<min_dur> <max_dur>`.')
                    return

                # Check if the timer is already running
                if self.it.running():
                    await context.send('Timer is already running.')
                    return

                self.sm.attach(self.it)

                self.it.start(int(min_dur), int(max_dur))

                self.sm.on_play_sound()
                await context.send(f'Timer started! Min: `{min_dur}`, Max: `{max_dur}`')
            else:
                await context.send(self.generate_borks())

        @self.command(name='stop', help='Stops the timer.')
        async def stop(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                if not self.it.running():
                    await context.send('There is no timer running.')
                    return

                self.it.stop()
                await context.send('The timer has stopped.')
            else:
                await context.send(self.generate_borks())

        @self.command(name='shush', help='Stops the current sound')
        async def shush(context: commands.Context):
            if self._debug or self._voice_client:
                if self._voice_client.is_playing():
                    print("Shushing")
                    self._voice_client.stop()


        # ------------------------------------------------------
        # ----- Stats
        @self.command(name='history', help='Prints a history of the last played sounds.')
        async def history(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                _history = self.sm.get_history()
                if len(_history) < 1:
                    await context.send('The history is empty.')
                    return

                msg = '```' + '\n'.join(_history) + '```'
                await context.send(msg)
            else:
                await context.send(self.generate_borks())


        # ------------------------------------------------------
        # ----- Download/upload
        @self.command(name='download', help='Uploads the current/previous sound.')
        async def download(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                # _current = self.sm.get_current_sound_full()
                _current = self.sm.get_current_sound()
                if not _current:
                    await _current.send('No sound has been played.')
                    return
                await context.send(content=_current.split('\'')[-1], file=File(_current))
            else:
                await context.send(self.generate_borks())

        @self.command(name='upload', help='Upload a sound.')
        async def upload(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                message: Message = context.message

                print(f'Found {len(message.attachments)}.')
                for attachment in message.attachments:
                    file_name = attachment.filename
                    if file_name.endswith('.mp3'):
                        file_path = f'assets/uploads/{file_name}'
                        await attachment.save(file_path)
                        # with open(file_path, 'wb') as f:
            else:
                await context.send(self.generate_borks())


        # ------------------------------------------------------
        # ----- Management
        @self.command(name='remove', help='Removes a sound from the library using `DoggoRemove™`.')
        async def remove(context: commands.Context, sound_name: str):
            if '..' in sound_name or '/' in sound_name:
                return

            if self.sm.sound_exists(sound_name):
                self.sm.remove_sound(sound_name)
                await context.send(f'The sound `{sound_name}` has been removed from the library. '
                                   f'Thanks for using our removal service DoggoRemove™.')
            else:
                await context.send(f'The sound with a name of `{sound_name}` does not exist.')

        @self.command(name='removed_list', help='Lists all the removed sounds.')
        async def removed_list(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                _removed = self.sm.get_removed_list()
                if len(_removed) > 0:
                    msg = '```' + '\n'.join(_removed) + '```'
                    await context.send(msg)
                else:
                    await context.send(f'No sounds have been removed.')
            else:
                await context.send(self.generate_borks())

        @self.command(name='restore', help='Restores a removed sound using `DoggoRestore™`.')
        async def restore(context: commands.Context, sound_name: str):
            if '..' in sound_name or '/' in sound_name:
                return

            if self._debug or self.roll_comply(context.author.id):
                _removed = self.sm.get_removed_list()
                if sound_name in _removed:
                    self.sm.restore_sound(sound_name)
                    await context.send(f'The sound `{sound_name}` has been restored. '
                                       f'Thanks for using our restoration service DoggoRestore™.')
                else:
                    await context.send(f'The sound `{sound_name}` is not in the removed list.')
                    msg = '```' + '\n'.join(_removed) + '```'
                    await context.send(msg)
            else:
                await context.send(self.generate_borks())

        @self.command(name='search', help='Looks for sounds in the sound library using `DoggoSearch™`.')
        async def search(context: commands.Context, search_word: str):
            if self._debug or self.roll_comply(context.author.id):
                matches = self.sm.search_library(search_word)
                if matches:
                    msg = f'Thanks for using DoggoSearch™. Found `{len(matches) - 1}` sounds.\n' + '```' + '\n'.join(matches) + '```'
                    await context.send(msg)
                else:
                    await context.send(f'DoggoSearch™ did not find any sounds containing `{search_word}`.')
            else:
                await context.send(self.generate_borks())


        # ------------------------------------------------------
        # ----- Manual playing
        @self.command(name='bark', help='Plays a random sound.')
        async def bark(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                if self.sm.can_play_sound():
                    self.sm.on_play_sound()
            else:
                await context.send(self.generate_borks())

        @self.command(name='rebark', help='Replays the previous sound.')
        async def replay(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                if self.sm.can_play_sound():
                    self.sm.replay_sound()
            else:
                await context.send(self.generate_borks())

        @self.command(name='playdur', help='Plays a sound with a specific length between `1`s and `16`s')
        async def playdur(context: commands.Context, dur: int):
            if self._debug or self.roll_comply(context.author.id):
                if 0 < dur < 17:
                    if self.sm.can_play_sound():
                        self.sm.play_sound_with_duration(dur)
                else:
                    await context.send('Plays a sound with a specific length between `1`s and `16`s')

        @self.command(name='play', help='Plays a specific sound by name.')
        async def play(context: commands.Context, *args):
            sound_name = ' '.join(args)
            if '..' in sound_name or '/' in sound_name:
                return

            if self._debug or self.roll_comply(context.author.id):
                if self.sm.can_play_sound():
                    if self.sm.sound_exists(sound_name):
                        self.sm.play_specific(sound_name)
                    else:
                        await context.send(f'The sound with a name of `{sound_name}` does not exist.')
            else:
                await context.send(self.generate_borks())

        @self.command(name='say', help='Speaks text with the help of TTS.')
        async def say(context: commands.Context, *args):
            if self._debug or self.roll_comply(context.author.id):
                await context.send(' '.join(args), tts=True)
            else:
                await context.send(self.generate_borks())

        @self.command(name='pog', help='Pogs in the voice.')
        async def custom_pogchamp(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                if self.sm.can_play_sound():
                    self.sm.play_custom_pogchamp()
            else:
                await context.send(self.generate_borks())

        @self.command(name='dova', help='dovaaa.')
        async def custom_dova(context: commands.Context):
            if self._debug or self.roll_comply(context.author.id):
                if self.sm.can_play_sound():
                    self.sm.play_custom_dova()
            else:
                await context.send(self.generate_borks())


#        @self.command(name='recorded', help='Plays recorded sounds.')
#        async def recorded(context: commands.Context):
#            if self._debug or self.roll_comply(context.author.id):
#                if self.sm.can_play_sound():
#                    # Get the user who played the command
#                    author: Member = context.author
#
#                    # Add user to dict of not present
#                    if author not in self._recorded_author:
#                        self._recorded_author[author] = 10
#                    else:
#                        self._recorded_author[author] -= 1
#
#                    # Determine available requests
#                    if self._recorded_author[author] > -1:
#                        await context.send(f'{author.mention}, you have {self._recorded_author[author]} recorded requests left.')
#                        self.sm.play_recorded()
#                    elif self._recorded_author[author] > -2:
#                        await context.send(f'{author.mention}, you are out of recorded requests.')
#                    elif self._recorded_author[author] > -3:
#                        await context.send(f'{author.mention}, you are out of recorded requests god dammit.')
#                    elif self._recorded_author[author] > -4:
#                        await context.send(f'{author.mention}, wtf dude.')
#                    else:
#                        _random_nick = random.choice(self.nicknames)
#                        _success = False
#                        try:
#                            await context.author.edit(nick=_random_nick)
#                        except Exception as e:
#                            _success = False
#                        else:
#                            _success = True
#
#                        if _success:
#                            await context.send(f'{author.mention}, be gone `{_random_nick}`!')
#                            await context.author.edit(voice_channel=None)
#                        else:
#                            await context.send(f'{author.mention}, hey you are admin pussy, please rename yourself to -> `{_random_nick}`!')
#                            await context.author.edit(voice_channel=None)
#            else:
#                await context.send(self.generate_borks())


        # ------------------------------------------------------
        # ----- Fun commands
        @self.command(name='attack', help='Attacks a user.')
        async def attack(context: commands.Context, member: Member):
            if self._debug or self.roll_comply(context.author.id):
                attack_command = self.roll_attack()
                if attack_command == "nickname":
                    await member.edit(nick=random.choice(self.nicknames))
                elif attack_command == "disconnect":
                    await member.edit(voice_channel=None)
                elif attack_command == "private_insult":
                    await member.send(random.choice(self.insults))
                elif attack_command == "public_insult":
                    await context.send(f'{member}, {random.choice(self.insults)}.')
                elif attack_command == "server_deafen":
                    await member.edit(deafen=True)
                elif attack_command == "server_mute":
                    await member.edit(mute=True)
            else:
                await context.send(self.generate_borks())

        @self.command(name='nickname', help='Gives a member a random nickname')
        async def nickname(context: commands.Context, member: Member):
            if self._debug or self.roll_comply(context.author.id):
                await member.edit(nick=random.choice(self.nicknames))
            else:
                await context.send(self.generate_borks())

        @self.command(name='fuck', help='Swears in Dog™')
        async def fuck(context: commands.Context):
            s_word = random.choice(self.swearwords)
            try:
                t_word = self.translate(s_word)
            except Exception as e:
                t_word = ""
            await context.send(f"{s_word} -> (DoggoTranslate™) -> {t_word}")


        # ------------------------------------------------------
        # ----- Other
        @self.command(name='debug', help='Toggles debug mode.')
        async def debug(context: commands.Context):
            if context.author.id in ADMINS:
                self._debug = not self._debug
                await context.send(f'Debug is now set to: {self._debug}')
            else:
                await context.send(f'Author only command. Bork')


# ----- On voice channel change
# @bot.event
# async def on_voice_state_update(member, before, after):
#     if before.channel is None and after.channel is not None:
#         if after.channel.id == [YOUR_CHANNEL_ID]:
#             await member.guild.system_channel.send("Alarm!")

# ----- Mention author
# context.message.author.mention()

# ----- Check if the bot is connected to a voice channel
# self._voice_client.is_connected()

# voice: VoiceState = member.voice


soundbot = SoundBot('-')
soundbot.run(TOKEN)
