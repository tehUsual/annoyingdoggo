import asyncio
import random


class IntervalTimer:
    def __init__(self):
        # Initializaiton
        self.min_dur = 5
        self.max_dur = 20

        # Callbacks
        self.on_play_sound = None

        # Current timer
        self.target_duration = 0
        self.current_duration = 0

        self._task = None

    def running(self):
        return not (self._task is None or self._task.done())

    def start(self, min_dur, max_dur):
        self.min_dur = min_dur
        self.max_dur = max_dur

        self._task = asyncio.create_task(self._run_timer())

    def stop(self):
        self._task.cancel()

    async def _run_timer(self):
        while True:
            # Initialize
            self.target_duration = random.randint(self.min_dur, self.max_dur)
            self.current_duration = 0

            # Wait loop
            while self.current_duration < self.target_duration:
                await asyncio.sleep(1)
                self.current_duration += 1
                print(f'timer: {self.current_duration}/{self.target_duration}')

            # Play sound
            if self.on_play_sound:
                self.on_play_sound()
