"""
    BFSK ASCII kodiranje i dekodiranje

    python3 bfsk.py enc "Bonsoir Elliot :)" 0.1 output.wav
        enkodira "Bonsoir Elliot :)" koristeci 0.1s za trajanje bita i upisuje rezultat u output.wav
    python3 bfsk.py dec input.wav
        dekodira sadrzaj fajla input.wav i ispisuje rezultat
"""
import audiolib as a
import sys
import itertools

# top level params, can be tuned
freq_lo = 300.0 # frequency that represents 0
freq_hi = 1000.0 # frequency that represents 1

# Binary String -> ASCII Char conversion
def binstr2asciichar(str):
    return chr(int(str, 2))

# Binary String <- ASCII Char conversion
def asciichar2binstr(ch):
    return bin(ord(ch))[2:].zfill(8)

# encodes the message using bit_len as the bit length in seconds and writes it to file
def encode(message, bit_len, wav_filename):
    print('Message:\"' + message + '\"')
    # converts the message to binary ascii
    encoded_message = ''.join([asciichar2binstr(ch) for ch in message])
    print('Binary ASCII:\"' + encoded_message + '\"')
    # creates frames
    frames_per_bit = int(a.framerate * bit_len)
    frames = []
    phase = 0
    # the main ecnoding loop
    for bit in encoded_message:
        # encodes one bit
        freq = freq_hi if bit == '1' else freq_lo
        new_frames, phase = a.create_frames(freq, frames_per_bit, phase)
        frames.extend(new_frames)
    # writes to file
    a.write_wav(frames, wav_filename)
    print('Wrote to file:\"' + wav_filename + '\"')

# this is where the magic happens, takes an array of frames and returns a message string
def extract_bits(frames):
    # gets frequencies from frames
    freqs_frames = a.extract_freqs_noob(frames)

    # converts frequencies to bits, uses the average of all frequencies as a threshold
    sum_all_freqs = sum([freq * frames for (freq, frames) in freqs_frames])
    total_num_frames = sum([frames for (freq, frames) in freqs_frames])
    freq_thresh = sum_all_freqs / total_num_frames
    bits_frames = [( (freq > freq_thresh), frames) for freq, frames in freqs_frames]

    # tuples get expanded and now we get an array of bits, one bit for each frame
    bits_expanded = a.flatten([[freq] * frames for (freq, frames) in bits_frames])
    # groups consecutive blocks of same values and filters out "really short blocks" that might
    # be a result of noise (magic constant 10)
    bits_grouped = [list(g) for k, g in itertools.groupby(bits_expanded)]
    bits_filtered = [ (group[0], len(group)) for group in bits_grouped if len(group) > 10]

    # doesn't know frames_per_bit, assumes that it's equal to the length
    # of the shortest block of same bits (relies on the assumption that input has 101/010 somewhere)
    maybe_frames_per_bit = min( [num_frames for bit, num_frames in bits_filtered] )
    # adds bits to the return string
    bits = a.flatten([[str(int(bit))] * round(num_frames / maybe_frames_per_bit) for bit, num_frames in bits_filtered])
    return ''.join(bits)

# decodes wav_filename.wav
# > ugly hacks that work should get full marks
def decode(wav_filename):
    # opens input file and gets frames
    frames = a.read_wav(wav_filename)
    print('Read from file:\"' + wav_filename + '\"')
    encoded_message = extract_bits(frames)
    print('Binary ASCII:\"' + encoded_message + '\"')
    bin_strings = [''.join(bin_list) for bin_list in a.chunks(encoded_message, 8)]
    message = ''.join([binstr2asciichar(bin_str) for bin_str in bin_strings])
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
