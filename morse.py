"""
    Morse kodiranje i dekodiranje

    python3 morse.py enc "HELLO FRIEND" 0.06 output.wav
        enkodira "HELLO FRIEND" koristeci 0.06s za trajanje tacke i upisuje rezultat u output.wav
    python3 morse.py dec input.wav
        dekodira sadrzaj fajla input.wav i ispisuje rezultat
"""
import audiolib as a
import sys

# top level params, can be tuned
freq = 300.0 # frequency

# morse code dictionary, space maps to space for convenience
morse = {'A': '.-',     'B': '-...',   'C': '-.-.',
         'D': '-..',    'E': '.',      'F': '..-.',
         'G': '--.',    'H': '....',   'I': '..',
         'J': '.---',   'K': '-.-',    'L': '.-..',
         'M': '--',     'N': '-.',     'O': '---',
         'P': '.--.',   'Q': '--.-',   'R': '.-.',
         'S': '...',    'T': '-',      'U': '..-',
         'V': '...-',   'W': '.--',    'X': '-..-',
         'Y': '-.--',   'Z': '--..',
         '0': '-----',  '1': '.----',  '2': '..---',
         '3': '...--',  '4': '....-',  '5': '.....',
         '6': '-....',  '7': '--...',  '8': '---..',
         '9': '----.',
         ' ': ' ', '.': '.-.-.-', ',': '--..--', ':': '---...'
        }

# encodes the message using tick_len as the unit length and creates wav_filename.wav
def encode(message, tick_len, wav_filename):
    print('Message:\"' + message + '\"')
    # converts the message to text morse
    # after encoding we get 1 space between letters and 3 between words
    encoded_message = ''.join([symbol for letter in ' '.join(message) for symbol in morse[letter]])

    print('Text morse:\"' + encoded_message + '\"')

    # builds the array of frames
    frames_per_tick = int(a.framerate * tick_len)
    frames = []
    phase = 0
    # the main ecnoding loop
    for symbol in encoded_message:
        if symbol == ' ':
            new_frames, phase = a.create_frames(0, 2*frames_per_tick, phase)
            frames.extend(new_frames) # letter break = 3, word break = 7
        if symbol == '.':
            new_frames, phase = a.create_frames(0, 1*frames_per_tick, phase)
            frames.extend(new_frames) # symbol break = 1
            new_frames, phase = a.create_frames(freq, 1*frames_per_tick, phase)
            frames.extend(new_frames) # dit = 1
        elif symbol == '-':
            new_frames, phase = a.create_frames(0, 1*frames_per_tick, phase)
            frames.extend(new_frames) # symbol break = 1
            new_frames, phase = a.create_frames(freq, 3*frames_per_tick, phase)
            frames.extend(new_frames) # dah = 3

    # writes to file
    a.write_wav(frames, wav_filename)
    print('Wrote to file:\"' + wav_filename + '\"')

# adds one block to the array of blocks
def add_block(blocks, curr_block):
    blocks.append(curr_block)
    # if there is a really short useless block, removes it and merges two surrounding ones
    if len(blocks) >= 3 and abs(blocks[-2]) == 1:
        blocks.pop()
        blocks.pop()
        blocks[-1] += curr_block+1

# goes through frames and extracts blocks of sines/silences
def extract_blocks(frames):
    # tries to adapt to various tick_lenghts
    # kicks really short blocks out (probably noise)
    blocks = []
    curr_block = 0 # silent blocks are represented by negative values
    last_frame = 0
    for frame in frames:
        if frame == 0: # silent frame
            # registers the end of the sine block
            if curr_block > 0:
                add_block(blocks, curr_block)
                curr_block = 0;
            curr_block -= 1
        else: # sine frame
            # registers the end of the silent block
            if curr_block < 0:
                add_block(blocks, curr_block)
                curr_block = 0;
            curr_block += 1
    # last block
    add_block(blocks, curr_block)
    # if last blocks is +-1, delete it
    if len(blocks) and abs(blocks[-1]) == 1:
        blocks.pop()
    return blocks

# decodes wav_filename.wav
# > ugly hacks that work should get full marks
def decode(wav_filename):
    # opens input file and gets frames
    frames = a.read_wav(wav_filename)
    print('Read from file:\"' + wav_filename + '\"')
    # goes through frames and extracts blocks of sines/silences
    blocks = extract_blocks(frames)
    # determines the lengths of 5 possible atoms: word_break, letter_break, symbol_break, dit, dah
    block_lengths = sorted(set(blocks))
    if len(block_lengths) != 5:
        print(block_lengths)
        raise Exception('more or less than 5 different block lengths, oops')
        # yes, I know what you're thinking, another crazy assumption
        # we can be clever with less than 5 different block lengths but let's
        # just leave it for now and assume that all 5 block types will be present
    # we have 5 sorted block lengths
    len_to_atom = {
         block_lengths[0]: '# #', # word_break
         block_lengths[1]: '#', # letter_break
         block_lengths[2]: '', # symbol_break, not needed anymore
         block_lengths[3]: '.', # dit
         block_lengths[4]: '-' # dah
        }
    encoded_message = ''.join([len_to_atom[block] for block in blocks])
    print('Text morse:\"' + encoded_message.replace('#', ' ') + '\"') # debug print
    # makes an inverse mapping and decodes text morse to plaintext
    inv_morse = {v: k for k, v in morse.items()}
    message = ''.join([inv_morse[letter] for letter in encoded_message.split('#')])
    print('Message:\"' + message + '\"') # solution

# main function, takes care of parsing the command line arguments
def main():
    if len(sys.argv) < 2:
        raise Exception('no arguments')
    if sys.argv[1] == 'enc':
        if len(sys.argv) != 5:
            raise Exception('enc expects exactly three arguments')
        encode(sys.argv[2], float(sys.argv[3]), sys.argv[4])
    elif sys.argv[1] == 'dec':
        if len(sys.argv) != 3:
            raise Exception('dec expects exactly one argument')
        decode(sys.argv[2])
    else:
        raise Exception('enc/dec are only allowed commands')

# entry point
if __name__ == "__main__":
    main()
