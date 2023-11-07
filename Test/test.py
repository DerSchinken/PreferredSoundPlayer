import os; print(os.getcwd())

from preferredsoundplayer import soundplay, stopsound, loopsound, stoploop, get_is_playing, get_is_loop_playing
import time

x = soundplay("test-music.mp3", block=False)  # got it from https://pixabay.com/de/music/spannung-epic-hybrid-trailer-test-of-the-brave-128341/
assert get_is_playing(x) == True
time.sleep(10)
stopsound(x)
assert get_is_playing(x) == False

y = loopsound("loop-music.mp3")  # got it from https://www.zedge.net/ringtone/845f4027-7e77-4022-a949-e180beddbc27
assert get_is_loop_playing(y) == True
time.sleep(30)
stoploop(y)
assert get_is_loop_playing(y) == False

soundplay("test-music.mp3", block=True)
