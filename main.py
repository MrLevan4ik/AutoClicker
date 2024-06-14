import keyboard
import mouse
import time

Click = False

def cliker():
    global Click
    Click = not Click

keyboard.add_hotkey('W + S', cliker)

while True:
    if Click:
        mouse.click(button='left')
        time.sleep(0.01)
