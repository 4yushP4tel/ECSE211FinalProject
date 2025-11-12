from utils.sound import Sound

class Speaker:
    def __init__(self):
        self.speaker = Sound()
        
    def play_delivery_tone(self):
        tone1 = Sound(pitch="C5", duration=0.2, volume=70)
        tone2 = Sound(pitch="E5", duration=0.2, volume=70)
        tone1.play().wait_done()
        tone2.play().wait_done()