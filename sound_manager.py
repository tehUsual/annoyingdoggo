from interval_timer import IntervalTimer
import shutil
import asyncio
import discord
import random
import json
import os


MAX_HISTORY = 20
MAX_SEARCH = 30


class SoundManager:
    def __init__(self, sounds_folder):
        self.sounds_folder = sounds_folder
        self.sounds = []
        self.sounds_by_length = {}
        self.recorded = []
        self.history = []
        self.removed = []
        self.current_sound = None

        self.ffmpeg = "C:\\Standalone\\ffmpeg\\ffmpeg.exe"
        self._voice_client = None
        self._channel = None

        self._load_sounds()

    # Adds a reference to the voice client
    def add_voice_client(self, voice_client: discord.VoiceClient):
        self._voice_client = voice_client

    def add_text_channel(self, channel):
        self._channel = channel

    # Attaches the callback timer
    def attach(self, timer: IntervalTimer):
        timer.on_play_sound = self.on_play_sound

    @staticmethod
    def detach(timer: IntervalTimer):
        timer.on_play_sound = None

    def can_play_sound(self) -> bool:
        return self._voice_client and not self._voice_client.is_playing()

    def sound_exists(self, sound_name):
        return sound_name in self.sounds

    # Loads all the sounds
    def _load_sounds(self):
        self.sounds = [i for i in os.listdir(self.sounds_folder) if i.endswith('.mp3')]
        print(f'Loaded {len(self.sounds)} sounds.')
        self.recorded = [i for i in os.listdir("assets/personal") if i.endswith('.mp3')]
        print(f'Loaded {len(self.recorded)} recorded sounds.')

        with open("assets/db.json", "r") as f:
            js = json.load(f)
            for entry in js:
                if entry["name"] in self.sounds:
                    if not entry["file_dur"] + 1 in self.sounds_by_length:
                        self.sounds_by_length[entry["file_dur"] + 1] = []
                    self.sounds_by_length[entry["file_dur"] + 1].append(entry["name"])

        for key in sorted(self.sounds_by_length.keys()):
            print(f'Loaded {len(self.sounds_by_length[key])} sounds with length {key}')

        self.removed = [i for i in os.listdir("assets/removed") if i.endswith('.mp3')]
        print(f'Found {len(self.removed)} removed sounds.')


    def play_custom_pogchamp(self):
        sound_file = "assets/special/pogchamp.mp3"
        if self._voice_client:
            if not self._voice_client.is_playing():
                self._voice_client.play(discord.FFmpegPCMAudio(executable=self.ffmpeg, source=sound_file))

    def play_custom_dova(self):
        sound_file = "assets/special/dova.mp3"
        if self._voice_client:
            if not self._voice_client.is_playing():
                self._voice_client.play(discord.FFmpegPCMAudio(executable=self.ffmpeg, source=sound_file))

    def play_sound_with_duration(self, dur):
        if self.can_play_sound():
            if dur in self.sounds_by_length:
                sound_file = f'{self.sounds_folder}/{random.choice(self.sounds_by_length[dur])}'
                self._voice_client.play(discord.FFmpegPCMAudio(executable=self.ffmpeg, source=sound_file))

    def play_specific(self, sound_name):
        sound_file = f'{self.sounds_folder}/{sound_name}'
        self._voice_client.play(discord.FFmpegPCMAudio(executable=self.ffmpeg, source=sound_file))

    def remove_sound(self, sound_name):
        sound_file_src = f'{self.sounds_folder}/{sound_name}'
        sound_file_trg = f'assets/removed/{sound_name}'
        shutil.move(sound_file_src, sound_file_trg)
        self.removed.append(sound_name)

        self.sounds.remove(sound_name)
        for key in self.sounds_by_length:
            if sound_name in self.sounds_by_length[key]:
                self.sounds_by_length[key].remove(sound_name)
                break

    def get_removed_list(self):
        return self.removed

    def restore_sound(self, sound_name):
        sound_file_src = f'assets/removed/{sound_name}'
        sound_file_trg = f'{self.sounds_folder}/{sound_name}'
        shutil.move(sound_file_src, sound_file_trg)

        self.removed.remove(sound_name)
        self.sounds.append(sound_name)

    def search_library(self, search_field):
        matches = []
        match_num = 0
        for sound_name in self.sounds:
            if search_field in sound_name:
                matches.append(sound_name)
                match_num += 1

            if match_num >= MAX_SEARCH:
                break
        return matches

    def play_recorded(self):
        sound_file = f'assets/personal/{random.choice(self.recorded)}'
        if self._voice_client:
            if not self._voice_client.is_playing():
                self._voice_client.play(discord.FFmpegPCMAudio(executable=self.ffmpeg, source=sound_file))
                self._update_history(sound_file)


    # Replay previous sound
    def replay_sound(self):
        self._play_sound(self.get_current_sound(False), log=False)

    # Plays a random sound
    def on_play_sound(self):
        if self.sounds:
            sound_file = random.choice(self.sounds)
            sound_path = f'{self.sounds_folder}/{sound_file}'
            self._play_sound(sound_path)

    def _play_sound(self, sound_file, log=True):
        if self._voice_client:
            if not self._voice_client.is_playing():
                if log:
                    self._update_history(sound_file)
                    print(sound_file)

                self._voice_client.play(discord.FFmpegPCMAudio(executable=self.ffmpeg, source=sound_file))

    # async def print_debug(self, msg):
    #     await self._channel.send(msg)

    def _update_history(self, sound_file):
        self.current_sound = sound_file

        if len(self.history) > 15:
            self.history.pop(0)
        self.history.append(sound_file)

    def get_current_sound(self, force_split=False):
        if force_split:
            return self.current_sound.split('/')[-1]
        return self.current_sound

    def get_current_sound_full(self):
        return f'{self.sounds_folder}/{self.current_sound}'

    def get_history(self):
        return self.history

    # Returns the current playing state
    def is_playing(self):
        return self._voice_client.is_playing()
