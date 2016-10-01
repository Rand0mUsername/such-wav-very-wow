"""
    Osnovne audio funkcije i promenljive koje su manje vise potrebne u svakom fajlu.
    Dodate jos neke funkcije koje nisu striktno u vezi sa zvukom ali su potrebne na
    vise mesta. Pravljenje jos jedne biblioteke zbog dve male fje bi bilo previse bahato.
"""
import math
import struct
import wave

# global consts, no real reason to ever change these
nchannels = 1 # number of channels
bitdepth = 2 # bits per sample
framerate = 44100.0 # samples/frames per second
comptype = "NONE" # compression type
compname = "not compressed" # compression name
amp_range = 64000.0 # multiplier for amplitude, amplitude range

# splits list L into chunks of size sz and returns a list of lists
def chunks(L, sz):
    return [L[start:start+sz] for start in range(0, len(L), sz)]

# usual flatten operation, converts nested list to a regular list
def flatten(L):
    return [elem for inner in L for elem in inner]

# helper function that converts length in ms to frames
def s2f(ms):
    return round(framerate * ms / 1000)  

# noob approach to extracting frequencies from an array of frames
def extract_freqs_noob(frames):
    # monitors every time waveform crosses X axis while going upwards
    # and calculates frequencies for each period
    freqs_frames = [] # (frequency, number of frames) tuple
    last_frame = curr_num_frames = 0
    for frame in frames:
        if last_frame < 0 and frame >= 0:
            # one period is over
            freqs_frames.append((round(framerate / curr_num_frames), curr_num_frames))
            curr_num_frames = 0
        curr_num_frames += 1
        last_frame = frame
    return freqs_frames

# uses provided starting phase and frequency to generate num_frames audio frames
# returns a tuple (list of frames, phase for the next part of the waveform)
def create_frames(freq, num_frames, phase):
    ret = []
    delta = 0 if freq == 0 else (framerate / freq) * (phase / (2 * math.pi))
    for x in range(num_frames):
        phase = (2*math.pi*freq*((x+delta)/framerate)) % (2*math.pi)
        ret.append(math.sin(phase)) # [-1, 1], will be multiplied by amp
    out_phase = (2*math.pi*freq*((num_frames+delta)/framerate)) % (2*math.pi)
    return (ret, out_phase)

# writes input frames to the specified wav file
def write_wav(frames, wav_filename):
    # opens output file and sets params
    wav_file = wave.open(wav_filename, "w")
    wav_file.setparams((nchannels, bitdepth, int(framerate), len(frames),
        comptype, compname))

    # writes audio frames to file and closes it afterwards
    for frame in frames:
        wav_file.writeframes(struct.pack('h', int(frame*amp_range/2)))
    wav_file.close()

# returns frames from the specified wav file
def read_wav(wav_filename):
    wav_file = wave.open(wav_filename, "r")
    nframes = wav_file.getnframes()
    if wav_file.getparams() != (nchannels, bitdepth, int(framerate), nframes, comptype, compname):
        raise Exception('input file has different params from what we use to generate them')
    wav_frames = wav_file.readframes(wav_file.getnframes())
    frames = list(struct.unpack_from("%dh" % nframes, wav_frames))
    return frames
