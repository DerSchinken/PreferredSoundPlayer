#   Gary Davenport preferredsoundplayer functions 7/9/2021
#
#   This module has no dependencies, other than what comes with Windows 10,
#       the standard Linux kernel, MacOS 10.5 or later, and the
#       Python Standard Library.
#
#   Looping:
#   If sound files are .wav files they will loop in a thread loop duration is equal to length of .wav file
#   Mp3s will be looped by checking 5 times a second to see if sound has finished, and if so relaunch
#   (this is because it is harder to figure out time length of mp3 due to different styles encoding)
#
#   ----------------Windows----------------
#   Windows 10 uses the Windows winmm.dll Multimedia API to play sounds.
#   Windows 10 uses a single instance of a player, allowing for garbage collection tracking
#       See references:
#       “Programming Windows: the Definitive Guide to the WIN32 API,
#           Chapter 22 Sound and Music Section III Advanced Topics
#           ‘The MCI Command String Approach.’”
#           Programming Windows: the Definitive Guide to the WIN32 API,
#           by Charles Petzold, Microsoft Press, 1999.
#       https://stackoverflow.com/questions/22253074/how-to-play-or-open-mp3-or-wav-sound-file-in-c-program
#       https://github.com/michaelgundlach/mp3play
#       & https://github.com/TaylorSMarks/playsound/blob/master/playsound.py
#
#
#   ----------------Linux------------------
#   Linux uses ALSA and gstreamer, part of Linux kernel, also may use ffmpg if available
#   -Linux will always play .wavs with ALSA
#   Otherwise:
#   -Linux will use the first available player in this order: gst-1.0-play, ffmpeg,
#    gst playbin(built on the fly) or ALSA
#   -Linux will try to use gst-1.0-play first (usually present), if not present then
#   -Linux will try to use ffmpeg as its player (usually present), if not present then
#   -Linux will initialize a gstreamer playbin player (is supposed to always be present), if not present then
#   -Linux will play the sound with ALSA, and if not a .wav file will sound like white noise.
#
#   If the playbin player must be used, each sound gets its own instance of a player, to avoid internal conflicts
#       with gstreamers internal looping
#
#   ----------------MacOS-------------------
#   -MacOS uses the afplay module which is present OS X 10.5 and later
#
from __future__ import annotations
from typing import Any, List, Tuple, Union

import sndhdr
import subprocess
from platform import system
from random import random
from subprocess import PIPE

if system() == "Linux":
    import shutil

    try:
        import gi

        gi.require_version('Gst', '1.0')
        from gi.repository import Gst
    except:
        pass
    import os

if system() == "Windows":
    from ctypes import c_buffer, windll
    from sys import getfilesystemencoding
    from threading import Thread
    from time import sleep

PROCESS = Union[Union[str, List[Any, str], Tuple[str, str], subprocess.Popen[str]], subprocess.Popen]


# This module creates a single sound with winmm.dll API and returns the alias to the sound


class WinMMSoundPlayer:
    def __init__(self):
        self.is_song_playing = False
        self.sync = False
        self.P = None
        self.file_name = ""
        self.alias = ""
        self.loop_alias = ""
        self.alias_list = []

    # typical process for using winmm.dll
    def _process_windows_command(self, command_string: str) -> Any:
        buf = c_buffer(255)
        command = command_string.encode(getfilesystemencoding())
        # print(command)
        windll.winmm.mciSendStringA(command, buf, 254, 0)
        return buf.value

    def _collect_garbage(self) -> None:
        #
        #   Garbage Collection
        #
        #   go through alias list
        #       if song not playing
        #           close it
        #           remove it from list
        #
        # aliasListLength=len(self.aliasList)
        # for i in range(aliasListLength):
        #    if self.getIsPlaying(self.aliasList[i])==False:

        # make a list of sounds that are no longer playing
        removal_list = []
        for i in range(len(self.alias_list)):
            if not self.get_is_playing(self.alias_list[i]):
                # print("adding",self.aliasList[i],"to garbage collector removal list.")
                removal_list.append(i)

        # issues stop(not necessary) and close commands to that list
        for i in range(len(removal_list) - 1, -1, -1):
            # print("closing",self.aliasList[removal_list[i]],"at index",removal_list[i])#<-----unprint
            self.stopsound(self.alias_list[removal_list[i]])
            del self.alias_list[removal_list[i]]

    # make an alias, play the song.
    # For Sync play - use the wait flag, then stop and close alias.
    # For Async - unable to close.

    def soundplay(self, file_name: str, block: bool = False) -> str:
        self._collect_garbage()

        self.file_name = file_name
        # make an alias
        self.alias = 'soundplay_' + str(random())
        # print("adding ", self.alias)# <------- unprint
        self.alias_list.append(self.alias)

        str1 = "open \"" + os.path.abspath(self.file_name) + "\"" + " alias " + self.alias
        self._process_windows_command(str1)

        # use the wait feature to block or not block when constructing mciSendString command
        if not block:
            str1 = "play " + self.alias
            # play the sound
            self._process_windows_command(str1)
        else:
            # construct mciSendString command to wait i.e. blocking
            str1 = "play " + self.alias + " wait"
            # play the sound (blocking)
            self._process_windows_command(str1)
            # stop and close the sound after done
            str1 = "stop " + self.alias
            self._process_windows_command(str1)
            str1 = "close " + self.alias
            self._process_windows_command(str1)

        # return the alias of the sound
        return self.alias

    # this function uses the mci/windows api with a repeat call to loop sound
    def loopsound(self, file_name: str) -> str:
        self._collect_garbage()
        self.loop_alias = 'loopalias_' + str(random())
        # print("adding looper alias",self.loop_alias) #<-------unprint
        self.alias_list.append(self.loop_alias)
        open_command = "open \"" + os.path.abspath(file_name) + "\" type mpegvideo alias " + self.loop_alias
        self._process_windows_command(open_command)
        play_command = "play " + self.loop_alias + " repeat"
        self._process_windows_command(play_command)
        return self.loop_alias

    # issue stop and close commands using the sound's alias
    def stopsound(self, sound: str) -> None:
        # print("------------------------")
        try:
            stop_command = "stop " + sound
            self._process_windows_command(stop_command)
            close_command = "close " + sound
            self._process_windows_command(close_command)
        except:
            pass

    # return True or False if song alias 'status' is 'playing'
    def get_is_playing(self, song: str) -> bool:
        try:
            status_command = "status " + song + " mode"
            status = self._process_windows_command(status_command)
            if status == b"playing":
                self.is_song_playing = True
            else:
                self.is_song_playing = False
        except:
            self.is_song_playing = False

        return self.is_song_playing


def is_file_a_wav(file_name: str) -> bool:
    try:
        if sndhdr.what(file_name)[0] == "wav":
            return True
    except:
        return False


class MusicLooper:
    def __init__(self, file_name):
        self.file_name = file_name
        self.playing = False
        self.song_process = None
        # self.optionalForMp3s_CheckRestartHowOften = .2

    def _playwave(self) -> None:
        self.song_process = playwave(self.file_name)

    def _playloop(self) -> None:
        while self.playing:
            # it is easy to get duration of wave file
            if is_file_a_wav(self.file_name):
                self.song_process = playwave(self.file_name)
                sleep(self._get_wav_duration_from_file())
            else:
                # it is hard to get duration of non wave files so check 5 times a second and relaunch if ended
                if self.song_process is not None:
                    if not get_is_playing(self.song_process):
                        self.song_process = playwave(self.file_name)
                else:
                    self.song_process = playwave(self.file_name)
                sleep(.2)
                # sleep(self.optionalForMp3s_CheckRestartHowOften)

    # start looping a wave
    def start_music_loop_wave(self) -> None:
        # def startMusicLoopWave(self,optionalForMp3s_CheckRestartHowOften=.2):
        # self.optionalForMp3s_CheckRestartHowOften=optionalForMp3s_CheckRestartHowOften
        if self.playing:  # don't allow more than one background loop per instance of MusicLooper
            print("Already playing, stop before starting new.")
            return
        else:
            self.playing = True
            t = Thread(target=self._playloop)  # , daemon=True)
            t.setDaemon(True)  # Deprecated! remove in future
            t.start()

    # stop looping a sound
    def stop_music_loop(self) -> None:
        if not self.playing:
            print(str(self.song_process) + " already stopped, play before trying to stop.")
            return
        else:
            self.playing = False  # set playing to False, which stops loop
            # issue command to stop the current wave file playing also, so song does not finish out
            stopwave(self.song_process)

    # get length of wave file in seconds
    def _get_wav_duration_from_file(self) -> float:
        frames = sndhdr.what(self.file_name)[3]
        rate = sndhdr.what(self.file_name)[1]
        duration = float(frames) / rate
        return duration

    def get_song_process(self) -> Any:  # Replace any by what it actually is in the future
        return self.song_process

    def get_playing(self) -> bool:
        return self.playing


# Each sound gets its own Gst.init() and own sound player


class SingleSoundLinux:
    def __init__(self):
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst
        self.pl = None
        self.gst = Gst.init()
        self.player_type = ""

    def _gst_play_process(self) -> None:
        self.pl.set_state(Gst.State.PLAYING)
        bus = self.pl.get_bus()
        bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
        self.pl.set_state(Gst.State.NULL)

    def soundplay(self, file_name: str, block: bool = False) -> List[Any, str]:
        if not self.get_is_playing(self.pl):
            self.pl = Gst.ElementFactory.make("playbin", "player")
            self.pl.set_property('uri', 'file://' + os.path.abspath(file_name))
            self.player_type = "gstreamer"
            self.T = Thread(target=self._gst_play_process, daemon=True)
            self.T.start()
            if block:
                self.T.join()
            return [self.pl, self.player_type]
        else:
            print("already playing, open new SingleSound if you need to play simoultaneously")

    def stopsound(self, sound: List[Any, str]) -> None:
        # print(sound[1])
        if sound[1] == "gstreamer":
            sound[0].set_state(Gst.State.NULL)

    def get_is_playing(self, song: List[Any, str]) -> bool:
        if song is None:
            return False
        # print(song[1])
        if song[1] == "gstreamer":
            state = (str(song[0].get_state(Gst.State.PLAYING)[1]).split()[1])
            if state == "GST_STATE_READY" or state == "GST_STATE_PLAYING":
                return True
            else:
                return False


#########################################################################
# These function definitions are intended to be used by the end user,   #
# but an instance of the class players above can be used also.          #
#########################################################################

# plays a sounnd file and also returns the alias of the sound being played, async method is default
# 3 separate methods allows for the Windows module to initialize an instance of 'WinMMSoundPlayer' class
# this way only one windows type player allows to keep track of all aliases made and garbage can be collected
# when songs have finished playing


def _soundplay_windows(file_name: str, block: bool = False) -> str:
    song = windowsPlayer.soundplay(file_name, block)  # change
    return song


def _soundplay_linux(
        file_name: str,
        block: bool = False
) -> Union[List[Any, str] | Tuple[str, str] | subprocess.Popen[str]]:
    if is_file_a_wav(file_name):  # use alsa if .wav
        # print("using alsa because its a wav")
        command = "exec aplay --quiet " + os.path.abspath(file_name)
    elif shutil.which("gst-play-1.0") is not None:  # use gst-play-1.0 if available
        # print("using gst-play-1.0 since available")
        command = "exec gst-play-1.0 " + os.path.abspath(file_name)
    elif shutil.which("ffplay") is not None:  # use ffplay if present
        # print("using ffplay since available")
        command = "exec ffplay -nodisp -autoexit -loglevel quiet " + os.path.abspath(file_name)
    else:
        try:
            import gi
            gi.require_version('Gst', '1.0')
            from gi.repository import Gst
            song = SingleSoundLinux().soundplay(file_name, block)
            # print("using gst playbin - successful try")
            return song
        except:
            print("must use ALSA, all else failed")
            command = "exec aplay --quiet " + os.path.abspath(file_name)
    if block:
        P = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=PIPE, stderr=PIPE).communicate()
    else:
        P = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=PIPE, stderr=PIPE)
    return P


def _soundplay_mac_os(file_name: str, block: bool = False) -> subprocess.Popen:
    command = "exec afplay \'" + os.path.abspath(file_name) + "\'"
    if block:
        P = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=PIPE, stderr=PIPE).communicate()
    else:
        P = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=PIPE, stderr=PIPE)
    return P


# stops the wave being played, 'process' in the case of windows is actually the alias to the song
# otherwise process is a process in other operating systems.


def stopsound(process: PROCESS) -> None:
    if process is not None:
        try:
            if process is not None:
                if system() == "Windows":
                    windowsPlayer.stopsound(process)
                elif system() == "Linux":
                    # see if process is GSTPlaybin
                    if str(process).find("gstreamer") != -1:
                        SingleSoundLinux().stopsound(process)
                    else:
                        process.terminate()  # Linux but not GSTPlaybin
                else:
                    process.terminate()  # MacOS
        except:
            pass
            # print("process is not playing")
    else:
        pass
        # print("process ", str(process), " not playing")


# pass the process or alias(windows) to the song and return True or False if it is playing


def get_is_playing(process: PROCESS) -> bool:
    if system() == "Windows":
        return windowsPlayer.get_is_playing(process)
    else:
        is_song_playing = False
        if process is not None:
            # see if process is GSTPlaybin
            if system() == "Linux":
                # see if process is GSTPlaybin
                if str(process).find("gstreamer") != -1:
                    return SingleSoundLinux().get_is_playing(process)
                else:  # Linux but not GSTPlaybin
                    try:
                        return process.poll() is None
                    except:
                        pass
            else:
                try:
                    return process.poll() is None
                except:
                    pass

        return is_song_playing


# this function will loop a wave file and return an instance of a MusicLooper object that loops music,
# or in the case of Windows it just calls the loop function in the Windows SingleSoundWindows class

"""
def loopsound(fileName,optionalForMp3s_CheckRestartHowOften=.2):
    if system() == "Windows":
        return(windowsPlayer.loopsound(fileName))
    else:
        looper=MusicLooper(fileName)
        looper.startMusicLoopWave(optionalForMp3s_CheckRestartHowOften)
        return(looper)
"""


def loopsound(file_name: str) -> Union[str | MusicLooper]:
    if system() == "Windows":
        return windowsPlayer.loopsound(file_name)
    else:
        looper = MusicLooper(file_name)
        looper.start_music_loop_wave()
        return looper


# pass an instance of a MusicLooper object and stop the loop, in Windows,
# use the Windows SingleSoundWindows class method
def stoploop(looper_object: Union[str | MusicLooper]) -> None:
    if looper_object is not None:
        if system() == "Windows":
            stopsound(looper_object)
        else:
            looper_object.stop_music_loop()
    else:
        pass
        # print("looperObject ", str(looperObject), " not playing")


# checks to see if song process is playing, (or if song alias's
# status is 'playing' in the case of Windows), returns True or False
def get_is_loop_playing(looper_object: Union[str | MusicLooper]) -> bool:
    if looper_object is not None:
        if system() == "Windows":
            return get_is_playing(looper_object)
        else:
            return looper_object.get_playing()
    else:
        return False


# This just references the command 'playsound' to 'soundplay' with
# default to block/sync behaviour in case you want to use this in place
# of the playsound module, which last I checked was not being maintained.
def playsound(file_name: str, block: bool = True) -> PROCESS:
    return soundplay(file_name, block)


# --------------------------------------------------------------------------------------------
if system() == 'Windows':
    windowsPlayer = WinMMSoundPlayer()  # uses a single instance of the WinMMSoundPlayer class
    soundplay = windowsPlayer.soundplay

elif system() == 'Darwin':
    soundplay = _soundplay_mac_os

else:
    soundplay = _soundplay_linux
# --------------------------------------------------------------------------------------------

# definitely these names used by MusicLooper, could also used by end user
playwave = soundplay
stopwave = stopsound
loopwave = loopsound
