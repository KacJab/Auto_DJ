import os
import sys
import time

import librosa
import matplotlib.pyplot as plt
import pychorus
import pandas as pd
import numpy as np
import seaborn as sns
import IPython.display as ipd
import glob
from itertools import cycle
from track import Track, load_tracks, merge_tracks, change_volume, mix_tracks_together
from playsound import playsound
import vlc
import time
from pydub import AudioSegment
import scipy

if __name__ == '__main__':

    audio_files = glob.glob("tracks/*.mp3")

    tracklist = []

    load_tracks(tracklist, audio_files)
    tracklist[1].create_similarity_matrix(tracklist)
    track_order = tracklist[0].determine_order(tracklist)
    mix_tracks_together(track_order, tracklist)

