import keyboard
import mouse
import time

clicking = False
delay = 0.01  # custom delay

def toggle_clicker():
    global clicking
    clicking = not clicking
    print("Autoclicker " + ("enabled" if clicking else "disabled"))

# allow the user to set the hotkey
hotkey = input("Enter the hotkey to toggle the autoclicker (e.g., 'W + S'): ")
keyboard.add_hotkey(hotkey, toggle_clicker)

# allow the user to set the delay
delay = float(input("Enter the delay between clicks (in seconds, e.g., 0.01): "))

print(f"Autoclicker ready. Use {hotkey} to toggle on/off.")

while True:
    if clicking:
        mouse.click(button='left')
        time.sleep(delay)
    else:
        time.sleep(0.1)  # small delay to reduce processor load
