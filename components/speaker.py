from utils.sound import Sound

class Speaker:
    def __init__(self):
        self.tone1 = Sound(pitch="C5", duration=0.5, volume=100)
        
    def play_delivery_tone(self):
        self.tone1.play()
        print("Played tone 1")