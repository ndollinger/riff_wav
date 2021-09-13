"""Riff file representation of a wave file."""
import wave
import collections

hex_wave = b'\x57\x41\x56\x45' # "WAVE"
hex_riff = b'\x52\x49\x46\x46' # "RIFF"
hex_fmt = b'\x66\x6d\x74\x20' # "fmt "

# Format codes
WAVE_FORMAT_PCM = b'\x01'	# PCM
WAVE_FORMAT_IEEE_FLOAT = b'\x03' # IEEE float
WAVE_FORMAT_ALAW = b'\x06' # 8-bit ITU-T G.711 A-law
WAVE_FORMAT_MULAW = '\x07' # 8-bit ITU-T G.711 µ-law
WAVE_FORMAT_EXTENSIBLE = b'\xFFFE' # Determined by SubFormat



WAVE_FORMAT = {
    b'\x01' : "WAVE_FORMAT_PCM"
}

SUPPORTED_WAVE_FORMATS = [WAVE_FORMAT_PCM]

class riff_wav: # TODO: Revisit the name of this class
    """File implementation of a wave."""
    
    def __init__(self, *args) -> None:
        """Create a new wave_riff."""
        # path to a wav file
        if isinstance(args[0], str):
            with open(args[0], mode="rb") as wav_file:
                wav_file_content = wav_file.read()
        # bytes assumed to be a wave file
        elif isinstance(args[0], bytearray):
            wav_file_content = args[0]
        self.riff_wav_chunk = riff_chunk(wav_file_content)
        self.format_chunk = format_chunk(self.riff_wav_chunk.child_chunks)
        self.data_chunk = integer_pcm_data_chunk(self.format_chunk.chunk_data)


    def __str__(self) -> str:
        """Print a String Representation of a wav RIFF File.
        
        This is kind of the point of this module, to graphically represent this file.
        
        """
        final_string = ""
        # There is the RIFF Wave/Chunk that is in front of the whole thing
        output_string = f'| ID: {self.riff_wav_chunk.chunk_id} | Body Size: {self.riff_wav_chunk.chunk_size} | Format: {self.riff_wav_chunk.riff_format_code}|'
        outline = "-" * len(output_string)
        final_string = outline + "\n" + output_string + "\n" + outline

        # Next is The format Chunk
        output_string = f'| ID: {self.format_chunk.chunk_id} | Body Size: {self.format_chunk.chunk_size} | Format: {self.format_chunk.format_code} | Channels: {self.format_chunk.num_channels} | Samples/second: {self.format_chunk.samples_per_second} | bytes/second: {self.format_chunk.bytes_per_second} | bytes/sample frame: {self.format_chunk.bytes_per_sample_frame} | bits/sample {self.format_chunk.bits_per_sample} |' # there might be additional fileds here if the format isn't 0x1
        outline = "-" * len(output_string)
        final_string += "\n" + outline + "\n" + output_string + "\n" + outline

        # And then the data chunk 
        output_string = f'| ID: {self.data_chunk.chunk_id} | Body Size: {self.data_chunk.chunk_size} | BYTES OF DATA |'
        outline = "-" * len(output_string)
        final_string += outline + "\n" + output_string + "\n" + outline

        return final_string

    def __repr__(self):
        """Fancy Representation."""
        # TODO: implement

class chunk:
    """Represent a 'chunk' within a RIFF file."""

    def __init__(self, chunk: bytearray) -> None:
        """Initialize a chunk."""
        self.chunk_id = chunk[0:4] # First four bytes are the id
        # Second four bytes are the size
        self.chunk_size = int.from_bytes(bytes(chunk[4:8]), byteorder='little') 
        self.chunk_data = chunk[8:] # The rest is "data"

    def __str__(self):
        """Represent chunk as human readable string."""
        return f'Byte Array with Chunk ID {self.chunk_id}'

class riff_chunk(chunk):
    """Represent the 'RIFF' chunk."""

    def __init__(self, chunk: bytearray) -> None:
        """Take an arbitrary chunk and parse as a RIFF."""
        super().__init__(chunk)
        self.riff_format_code = chunk[8:12]
        self.child_chunks = chunk[12:]

        if self.chunk_id != hex_riff:
            raise TypeError(f'{self} is not a RIFF file')        

class format_chunk(chunk):
    """Represent the 'fmt' chunk."""

    def __init__(self, chunk: bytearray) -> None:
        """Take an arbitrary set of bytes and parse it as a fmt chunk."""
        # Field     Bytes       Description
        # ----------------------------------
        # Chunk ID	4	        0x66 0x6d 0x74 0x20 (i.e. "fmt ")
        # Chunk Body Size	4	32-bit unsigned integer
        # Format Code	2	    16-bit unsigned integer
        # Number of Channels	2	16-bit unsigned integer
        # Samples per second	4	32-bit unsigned integer
        # Bytes per Second
        #    (a.k.a byte rate)	4	32-bit unsigned integer
        # Bytes per Sample Frame
        #    (a.k.a block align)	2	16-bit unsigned integer
        #Bits per sample	2	        16-bit unsigned integer

        # These fields are only present if format code is not 1:
        # Extension Size	2	16-bit unsigned integer
        # Extra fields	Variable	It depends on the format code
        super().__init__(chunk)
        self.format_code = bytes(self.chunk_data[0:1])
        # TODO: This seems like a lot of conversion, not sure I'm thinking about this correctly...
        self.num_channels = int.from_bytes(bytes(self.chunk_data[2:4]), byteorder="little")
        self.samples_per_second = int.from_bytes(bytes(self.chunk_data[4:8]), byteorder="little")
        self.bytes_per_second = int.from_bytes(bytes(self.chunk_data[8:12]), byteorder="little")
        self.bytes_per_sample_frame = int.from_bytes(bytes(self.chunk_data[12:14]), byteorder="little")
        self.bits_per_sample = int.from_bytes(bytes(self.chunk_data[14:16]), byteorder="little")
        
        try:
            self.format_type = WAVE_FORMAT[self.format_code]
        except KeyError: # TODO: Is this a legit thing to do?
            raise TypeError(f'Wave Format Code {self.format_code} not supported.  Only PCM Format supported')

class fact_chunk(chunk):
    """Sometimes there is a 'fact' chunk for certain formats. TODO: Implement this class."""

    def __init__(self):
        """Initialize a fact chunk."""
        pass

class floating_point_pcm_data_chunk(chunk):
    """TODO: Implement this class."""

class extensible_data_chunk(chunk):
    """TODO: Implement this class."""

class integer_pcm_data_chunk(chunk):
    """This chunk holds PCM data.

    This is the most common format, and consists of raw PCM samples as integers
    """

    """
    Samples in a multi-channel PCM wave file are interleaved. That is, in a stereo file, one sample for the left channel will be followed by one sample for the right channel, followed by another sample for the left channel, then right channel, and so forth.

    One set of interleaved samples is called a sample frame (also called a block). A sample frame will contain one sample for each channel. In a monophonic file, a sample frame will consist of 1 sample. In a stereo file, a sample frame has 2 samples (one for the left channel, one for the right channel). In a 5-channel file, a sample frame has 5 samples. The bytes per sample frame field in the format chunk gives the size in bytes of each sample frame. This can be useful when seeking to a particular sample frame in the file.
    """

    def __init__(self, chunk) -> None:
        """Create a PCM Data Chunk."""
        super().__init__(chunk)
        # This is pretty much just a pure chunk with a pad byte on the end
        self.pcm_data = self.chunk_data
        # Padding byte if M*Nc*Ns is odd, else 0 TODO: not sure how this actually works
        self.pad_byte = self.chunk_data[-1]

if __name__ == '__main__':
    """
    This is for testing purposes, should eventually be moved into tests or made into something that makes sense
    """
    import argparse
    parser = argparse.ArgumentParser(description='Generate a wave_riff file from a ')
    parser.add_argument("--wav_file", 
                        help="File Name of Wav file to translate",
                        type=str,
                        default="./tests/test_wavs/test_sample.wav")
    args = parser.parse_args()
    wav_file_name = args.wav_file
    wave_riff_file = riff_wav(wav_file_name)
    print(wave_riff_file)