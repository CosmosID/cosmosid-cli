from sys import stdout
from threading import Thread
from time import sleep


class ThreadLogger:
    _instance = None
    _initialized = False
    _enabled = False
    _finished = False
    _delay = 0.5

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ThreadLogger, cls).__new__(*args, **kwargs)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._prev_lines_amount = 0
            self._channels = {}
            self._max_line_length = 0

    def start(self):
        if self._enabled:
            raise RuntimeError("Logger is started!")
        self._enabled = True
        self._finished = False
        Thread(target=self._print_process).start()

    def stop(self):
        self._enabled = False
        while not self._finished:
            sleep(self._delay / 10)
        self._channels.clear()

    def info(self, channel, msg):
        self._channels[channel] = msg

    def _get_text(self, channels):
        longest_name_length = max([len(name) for name in channels.keys()])
        template = f"%{longest_name_length + 1}s  %s"
        lines = [template % (name, msg) for name, msg in channels.items()]
        self._max_line_length = max([len(line) for line in lines]) + 1
        return "\n".join(lines) + "\n"

    def _clear(self):
        stdout.write("\033[F" * self._prev_lines_amount)
        stdout.write(
            ("\r" + " " * self._max_line_length + "\n") * self._prev_lines_amount
        )
        stdout.write("\033[F" * self._prev_lines_amount)

    def _print_process(self):
        while self._enabled:
            sleep(self._delay)
            if not self._channels:
                continue
            self._clear()
            channels = self._channels.copy()
            stdout.write(self._get_text(channels))
            self._prev_lines_amount = len(channels.keys())
        self._finished = True
