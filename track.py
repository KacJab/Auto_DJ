import time
from pathlib import Path
import librosa as lr
from pydub import AudioSegment
import numpy as np
import soundfile as sf
import glob


def convert(track):
    y = track.file
    sr = track.sample_rate

    y = np.array(y * (1 << 15), dtype=np.int16)
    audio_segment = AudioSegment(
        y.tobytes(),
        frame_rate=sr,
        sample_width=y.dtype.itemsize,
        channels=1
    )
    return audio_segment


def load_tracks(tracklist, track_sources):
    for i, src in enumerate(track_sources):
        tracklist.append(Track(src))


def merge_tracks(src1, src2, export_as):
    sound1 = AudioSegment.from_file(src1)
    sound2 = AudioSegment.from_file(src2)

    merged = sound1.overlay(sound2)
    merged.export(export_as, format="mp3")


def change_volume(track, up_or_down, export_as):
    if up_or_down == "up":
        for i, el in enumerate(track.file):
            track.file[i] = el * i / len(track.file)

        converted = convert(track)
        converted.export(export_as, format="mp3")
    else:
        for i, el in enumerate(track.file):
            track.file[i] = el * (1 - i / len(track.file))

        converted = convert(track)
        converted.export(export_as, format="mp3")


class Track:

    def __init__(self, source):
        self.source = source
        self.name = Path(source).stem
        self.file, self.sample_rate = lr.load(source, sr=44100)
        self.tempo, self.beats = self.measure_the_tempo(self.file)
        self.intensity = self.measure_the_intensity(self.file)
        self.avg_intensity = sum(self.intensity) / len(self.intensity)
        # self.vims = self.find_vims()

    def measure_the_tempo(self, track):
        tempo, beats = lr.beat.beat_track(track, units='samples')
        return tempo, beats

    def measure_the_intensity(self, track):
        intensity = lr.amplitude_to_db(abs(self.file))
        return intensity

    def find_vims(self):
        return vims

    def create_similarity_matrix(self, tracks):
        similarity_matrix = [[1 for j in range(len(tracks))] for i in range(len(tracks))]
        for i, track_i in enumerate(tracks):
            for j, track_j in enumerate(tracks):
                tempo_diff = abs(track_i.tempo - track_j.tempo)
                avg_intensity_diff = abs(track_i.avg_intensity - track_j.avg_intensity)
                points = 50 - tempo_diff
                points = points + 30 - avg_intensity_diff * 2
                if points == 80:
                    points = 0
                similarity_matrix[i][j] = points

        return similarity_matrix

    def determine_order(self, tracks):
        similarity_matrix = self.create_similarity_matrix(tracks)
        free_spaces = [[0 for j in range(2)] for i in range(len(tracks))]
        max_value_in_rows = [0 for j in range(len(tracks))]
        track_order = []

        ###pierwsza tura szukania -szukamy najwyższego powiązania
        for i, track in enumerate(similarity_matrix):
            max_value_in_rows[i] = max(similarity_matrix[i])

        for j in range(2):
            track_id = max_value_in_rows.index(max(max_value_in_rows))
            track_order.append(track_id)
            free_spaces[track_id][j] = 1
            similarity_matrix[track_id] = [0 for e in similarity_matrix[track_id]]
            max_value_in_rows[track_id] = 0

        x = len(free_spaces) * 2 - 2
        y = sum(sum(free_spaces, []))

        while len(track_order) < len(free_spaces):
            left_side = []
            right_side = []
            for el in similarity_matrix:
                left_side.append(el[track_order[0]])
            next_max_left = max(left_side)
            for el in similarity_matrix:
                right_side.append(el[track_order[-1]])
            next_max_right = max(right_side)

            if next_max_left >= next_max_right:
                track_1_id = track_order[0]
                track_2_id = left_side.index(next_max_left)
                track_order.insert(0, track_2_id)
                similarity_matrix[track_2_id] = [0 for e in similarity_matrix[track_id]]
                for el in similarity_matrix:
                    right_side.append(el[track_2_id])
                free_spaces[track_1_id][1] = 1
                free_spaces[track_2_id][0] = 1

            else:
                track_1_id = track_order[-1]
                track_2_id = right_side.index(next_max_right)
                track_order.append(track_2_id)
                similarity_matrix[track_2_id] = [0 for e in similarity_matrix[track_id]]
                for el in similarity_matrix:
                    right_side.append(el[track_2_id])
                free_spaces[track_1_id][0] = 1
                free_spaces[track_2_id][1] = 1

        # print("kolejność", track_order, len(max_value_in_rows))

        return track_order

    # def merge_tracks(self, track2):
    #
    #     sound1 = AudioSegment.from_file(self.source)
    #     sound2 = AudioSegment.from_file(track2.source)
    #
    #     merged = sound1.overlay(sound2)
    #     source_to_save_to = "final_tracks/" + "1+2"+ "_final.mp3"
    #     ready_track.export(source_to_save_to, format="mp3")
    #     return merged

    def count_cut_length(self, track2, length):
        tempo_diff = self.tempo - track2.tempo
        avg_tempo = self.tempo + track2.tempo / 2

        return avg_tempo / (60 / length)

    def change_speed(self):
        pass

    def cut_track(self, cutting_point_1, cutting_point_2, source_to_save_to):

        sound = AudioSegment.from_file(self.source)
        samp = len(sound) - cutting_point_1
        lengh = len(sound)
        ready_track = sound[len(sound) * cutting_point_1:len(sound) * cutting_point_2]
        # source_to_save_to = "final_tracks/" + self.name + "_final.mp3"
        ready_track.export(source_to_save_to, format="mp3")
        # self.source = source_to_save_to
        # self = Track(source_to_save_to)

    #####ucinanie każdego kawałka przed ostatnim beatem i żeby zaczynał się od bitu
    def cut_at_beat(self, length, track_ordered):

        search_point = len(self.intensity) - (self.sample_rate * length)

        # for i in range(self.beats[2] - self.beats[0]):
        #     cut_point = search_point - i
        #     if cut_point in self.beats:
        #         break
        #
        # for i in range(self.beats[2] - self.beats[0]):
        #     cut_point_beg = i
        #     if cut_point in self.beats:
        #         break

        self.cut_track(0, (length * self.sample_rate) / len(self.intensity), 'working/' + str(track_ordered) + '_1.mp3')

        self.cut_track((length * self.sample_rate) / len(self.intensity),
                       (search_point) / len(self.intensity), 'working/' + str(track_ordered) + '_2.mp3')

        self.cut_track((search_point) / len(self.intensity),
                       1, 'working/' + str(track_ordered) + '_3.mp3')


def mix_tracks_together(track_order, tracks):
    for i, track in enumerate(tracks):
        track.cut_at_beat(25, track_order.index(i))

    downshifters = glob.glob('working/*_3.mp3')
    upshifters = glob.glob('working/*_1.mp3')

    for downsh in downshifters:
        track = Track(downsh)
        change_volume(track, 'down', downsh)

    for upsh in upshifters:
        track = Track(upsh)
        change_volume(track, 'up', upsh)

    for i in range(len(track_order) - 1):
        merge_tracks('working/' + (str(i) + '_3.mp3'), 'working/' + (str(i + 1) + '_1.mp3'),
                     'working/inter' + str(i) + '.mp3')


    for i in range(len(track_order) * 2):
        if i % 2 == 0:
            if i == 0:
                final_mix = AudioSegment.from_file('working/0_1.mp3')
            else:
                snd = AudioSegment.from_file('working/inter' + str(int(i/2)-1)+'.mp3')
                final_mix = final_mix + snd
        if i % 2 != 0:
            snd = AudioSegment.from_file('working/' + str(int((i + 1)/2)-1) + '_2.mp3')
            final_mix = final_mix + snd

    snd = AudioSegment.from_file('working/'+str(len(track_order)-1)+'_3.mp3')
    final_mix = final_mix + snd

    final_mix.export('final_tracks/final_mix.mp3', format='mp3')

