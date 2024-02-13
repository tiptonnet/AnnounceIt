from gtts import gTTS
import os
import wave

def speak_text(text, filename):
    # Create a gTTS object
    tts = gTTS(text=text, lang='en')

    # Save the synthesized speech as a WAV file
    tts.save(f"{filename}.mp3")
    os.system(f"ffmpeg -i {filename}.mp3 -acodec pcm_u8 -ar 8000 {filename}.wav")

# Usage
speak_text("Wrong pin, please try again.", "PinWrong")
#PlayIt("EnterPin.wav")
