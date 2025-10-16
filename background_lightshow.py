# This script runs a continuous 'Random ARGB Rain' light show 
# on the Novation Launchkey 25 MK2 pads in the Windows background.
# 
# Requires: Python, and the 'mido' and 'python-rtmidi' libraries.
# Installation: pip install mido python-rtmidi
#
# --- IMPORTANT: PORT NAME IS NOW READ FROM config.json ---

import mido
import time
import random
import sys
import json
import os

# Configuration constants
CONFIG_FILE = 'config.json'
DEFAULT_PORT = 'Launchkey 25 MK2 MIDI 2'
MIDI_CHANNEL = 0 # MIDI Channel 1 (index 0)
PAD_NOTES = list(range(36, 52)) # MIDI Notes 36 (C1) to 51 (D#2)

# Velocity values for colors (Based on Novation's color map)
# We only use velocities > 0 for random colors.
COLOR_VELOCITIES = [5, 13, 21, 56, 60, 64, 80, 127] # Red, Orange, Yellow, Green, Cyan, Blue, Purple, White

def load_midi_port_name():
    """Reads the MIDI port name from config.json or returns the default."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                port_name = config.get('MIDI_PORT_NAME', DEFAULT_PORT)
                print(f"Configuration loaded from {CONFIG_FILE}: Port '{port_name}'")
                return port_name
        except Exception as e:
            print(f"Warning: Failed to read or parse {CONFIG_FILE}. Using default port '{DEFAULT_PORT}'. Error: {e}")
            return DEFAULT_PORT
    else:
        print(f"Warning: Configuration file {CONFIG_FILE} not found. Using default port '{DEFAULT_PORT}'.")
        return DEFAULT_PORT

def send_led_message(port, note, velocity):
    """Sends a MIDI Note On message (color setting) to the Launchkey pad."""
    # Note On status byte is 0x90 (144) for channel 1 (index 0)
    msg = mido.Message('note_on', channel=MIDI_CHANNEL, note=note, velocity=velocity)
    port.send(msg)

def clear_all_pads(port):
    """Turns off all the pad LEDs."""
    print("Clearing all pads...")
    for note in PAD_NOTES:
        send_led_message(port, note, 0) # Velocity 0 turns the LED off

def run_rain_pattern(port):
    """Runs the continuous random ARGB rain light show."""
    print(f"Starting 'Random ARGB Rain' on {port.name}. Press Ctrl+C to stop.")
    
    active_lights = {} 
    INTERVAL_SECONDS = 0.05 
    LIGHT_DURATION = 0.5 

    try:
        while True:
            # 1. Check and turn off lights that have expired
            now = time.time()
            notes_to_clear = [note for note, expiry_time in active_lights.items() if now >= expiry_time]
            
            for note in notes_to_clear:
                send_led_message(port, note, 0)
                del active_lights[note]

            # 2. Pick a random pad and color for the new 'rain drop'
            random_note = random.choice(PAD_NOTES)
            random_velocity = random.choice(COLOR_VELOCITIES)
            
            # 3. Light up the pad and set its expiry time
            send_led_message(port, random_note, random_velocity)
            active_lights[random_note] = now + LIGHT_DURATION

            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStopping script...")
    except Exception as e:
        print(f"\nAn error occurred during pattern execution: {e}")
    finally:
        clear_all_pads(port)

if __name__ == "__main__":
    
    MIDI_PORT_NAME = load_midi_port_name()

    try:
        # 1. Open the MIDI port
        output_port = mido.open_output(MIDI_PORT_NAME)
        print(f"Successfully connected to MIDI port: {MIDI_PORT_NAME}")
        
        # 2. Run the light show
        run_rain_pattern(output_port)

    except ValueError:
        print(f"Error: Could not find or open the MIDI port named '{MIDI_PORT_NAME}'.")
        print("Please use the 'launchkey_controller.html' GUI to find and set the correct port name in 'config.json'.")
    except Exception as e:
        print(f"An unexpected error occurred during setup: {e}")
    finally:
        if 'output_port' in locals() and output_port.opened:
            output_port.close()
