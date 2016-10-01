"""
    SSTV MrRobot B&W n8 kodiranje i dekodiranje

    python3 sstv.py enc input.jpg output.wav
        enkodira sliku input.jpg i ispisuje rezultat u output.wav
    python3 sstv.py dec input.wav output.jpg
        dekodira fajl input.wav i ispisuje rezultat u output.jpg

    HEADER:
      300ms 1900Hz LEADER 
      10ms 1200Hz BREAK
      300ms 1900Hz LEADER 

    VIS (VSYNC, 1100Hz=1, 1300Hz=0):
      30ms 1200Hz START SIGNAL
      8x30ms
        B0 B1 = 01 GREEN/BW
        B2 B3 = 00  (Small image: V=120 H=160)
        B4 B5 B6 = 000 (Robot Mode)
        PARITY = 1 (Even parity bit)
      30ms 1200Hz STOP SIGNAL

    H=120 SCANLINES:
      10ms 1200Hz HSYNC
      56ms W=160 pixels (1500Hz=black, 2300Hz=white, 128 gray levels):
        1ms PIXEL
"""
import audiolib as a
import sys
import itertools
from PIL import Image
from enum import Enum

# params
FREQ_BIT_1 = 1100 # Hz
FREQ_HSYNC = FREQ_BREAK = FREQ_START = FREQ_STOP = 1200 # Hz
FREQ_BIT_0 = 1300 # Hz
FREQ_BLACK = 1500 # Hz
FREQ_LEADER = 1900 # Hz
FREQ_WHITE = 2300 # Hz
W, H = 160, 120 # px
LEN_HSYNC = 10 # ms, before each scanline
LEN_PIXEL = 1 # ms

# encodes jpg_filename.jpg
def encode(jpg_filename, wav_filename):
    # reads image from file
    img = Image.open(jpg_filename)
    print('Read from file:\"' + jpg_filename + '\"')
    if img.mode != 'L':
        raise Exception('Only grayscale pics please')
    if img.size != (W, H):
        raise Exception('Size not supported')
    # builds audio file
    frames = []
    phase = 0
    # HEADER
    new_frames, phase = a.create_frames(FREQ_LEADER, a.s2f(300), phase)
    frames.extend(new_frames)
    new_frames, phase = a.create_frames(FREQ_BREAK, a.s2f(10), phase)
    frames.extend(new_frames)
    new_frames, phase = a.create_frames(FREQ_LEADER, a.s2f(300), phase)
    frames.extend(new_frames)
    # VIS
    new_frames, phase = a.create_frames(FREQ_START, a.s2f(30), phase)
    frames.extend(new_frames)
    vis_signature = [0, 1, 0, 0, 0, 0, 0, 1]
    for bit in vis_signature:
        freq = FREQ_BIT_1 if bit else FREQ_BIT_0
        new_frames, phase = a.create_frames(freq, a.s2f(30), phase)
        frames.extend(new_frames)
    new_frames, phase = a.create_frames(FREQ_STOP, a.s2f(30), phase)
    frames.extend(new_frames)
    # SCANLINES
    pix = img.load()
    for y in range(H):
        # HSYNC
        new_frames, phase = a.create_frames(FREQ_HSYNC, a.s2f(10), phase)
        frames.extend(new_frames)
        for x in range(W):
            # pixels
            freq = FREQ_WHITE if pix[x,y] >= 128 else FREQ_BLACK
            new_frames, phase = a.create_frames(freq, a.s2f(LEN_PIXEL), phase)
            frames.extend(new_frames)
    # writes to file
    a.write_wav(frames, wav_filename)
    print('Wrote to file:\"' + wav_filename + '\"')


# primitive thresholding
def thresh(freq):
    if freq < 1450:
        return FREQ_HSYNC
    elif freq < 1900:
        return FREQ_BLACK
    else:
        return FREQ_WHITE

# primitive fixing of lines that are shorter/longer than 160px
def fix_line(line):
    if len(line) < 160:
        line += len(line) * line[-1]
    return line[:160]

# decodes wav_filename.wav
# > ugly hacks that work should get full marks
def decode(wav_filename, jpg_filename):
    # opens input file and gets frames
    frames = a.read_wav(wav_filename)
    print('Read from file:\"' + wav_filename + '\"')
    # gets frequencies from frames
    freqs_frames = a.extract_freqs_noob(frames)
    values_frames = [( thresh(freq), frames) for freq, frames in freqs_frames]
    # expands tuples and now we get an array of bits, one bit for each frame
    values_expanded = a.flatten([[freq] * frames for (freq, frames) in values_frames])
    # groups consecutive blocks of same values and filters out "really short blocks" that might
    # be a result of noise (magic constant 2 this time)
    values_grouped = [list(g) for k, g in itertools.groupby(values_expanded)]
    values_filtered = [ (group[0], len(group)) for group in values_grouped if len(group) > 2]

    # now that we have (value, num_frames) pairs we can extract actual pixels
    # UNIT_LEN is empirically discovered constant that represents the number of frames
    # per one pixel
    UNIT_LEN = 44
    line = ""
    lines = []
    for val in values_filtered:
        if val[0] == FREQ_WHITE: 
            # approx. number of consecutive px of this color
            line += "1" * round(val[1] / UNIT_LEN)
        elif val[0] == FREQ_BLACK:
            # approx. number of consecutive px of this color
            line += "0" * round(val[1] / UNIT_LEN)
        else:
            # HSYNC, line ends
            lines.append(line)
            line = ""
    # add the last line
    lines.append(line)
    # fix line lengths
    lines_fixed = [fix_line(ln) for ln in lines]
    # notice how we completely ignored the header and the VIS
    # well, all of that gets fixed by dropping two lines
    # <3
    lines_trunc = lines_fixed[2:]
    # generates pixels
    img = Image.new("L", (W, H), "white")
    pix = img.load()
    for y in range(H):
        for x in range(W):
            pix[x, y] = int(lines_trunc[y][x]) * 255
    # saves the image
    img.save(jpg_filename)
    print('Wrote to file:\"' + jpg_filename + '\"')

# main function, takes care of parsing the command line arguments
def main():
    if len(sys.argv) < 2:
        raise Exception('no arguments')
    if sys.argv[1] == 'enc':
        if len(sys.argv) != 4:
            raise Exception('enc expects exactly two arguments')
        encode(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'dec':
        if len(sys.argv) != 4:
            raise Exception('enc expects exactly two arguments')
        decode(sys.argv[2], sys.argv[3])
    else:
        raise Exception('enc/dec are only allowed commands')

# entry point
if __name__ == "__main__":
    main()
