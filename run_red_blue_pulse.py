# run_red_blue_pulse.py

from pulse_pal import PulsePalObject, PulsePalError
import time
import random
from tkinter import tk

# --- Parameters You Can Change ---
SERIAL_PORT = 'COM4'                # Your Pulse Pal's port name

TOTAL_DURATION_SECONDS = 10

# --- Channel 1 Parameters (20Hz Pulse Train, BLUE) ---
BLUE = 1
PULSE_VOLTAGE_BLUE = 5.0
PULSE_FREQUENCY_HZ_BLUE = 20

# --- Channel 2 Parameters (2 s ON / 0.5 s OFF, RED) ---
RED = 2
PULSE_VOLTAGE_RED = 5.0
ON_DURATION_SECONDS_RED = 2
OFF_DURATION_SECONDS_RED = 0.5
# --------------------------------------

print("--- Red/Blue 5HT MEA Experiment ---")

#calculate channel settings:

#blue
period = 1.0 / PULSE_FREQUENCY_HZ_BLUE
pulse_duration_blue = period * 0.5
#red

channels = ['BLUE', 'RED']
channel = channels[0] #pick 0 for blue or 1 for red

time_log = [] #log times of stimulations

def run_trial():
    choice = random.random() > 0.5 #choose whether or not the stim will be triggered
    try:
        # 1. Connect to the Pulse Pal
        print(f"Connecting to Pulse Pal on {SERIAL_PORT}...")
        myPulsePal = PulsePalObject(SERIAL_PORT)
        print("Connection successful.")

        if channel == 'BLUE':
            # --- Configure Channel 1: 20Hz Pulse Train ---
            print(f"\nConfiguring Channel {BLUE} for a {PULSE_FREQUENCY_HZ_BLUE}Hz pulse train...")

            myPulsePal.programOutputChannelParam('restingVoltage', channel=BLUE, value=0)
            myPulsePal.programOutputChannelParam('isBiphasic', channel=BLUE, value=0)
            myPulsePal.programOutputChannelParam('phase1Voltage', channel=BLUE, value=PULSE_VOLTAGE_BLUE)
            myPulsePal.programOutputChannelParam('phase1Duration', channel=BLUE, value=pulse_duration_blue)
            myPulsePal.programOutputChannelParam('interPulseInterval', channel=BLUE, value=pulse_duration_blue)
            myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=BLUE, value=TOTAL_DURATION_SECONDS)
            print("Channel 1 configuration complete.")
        
        elif channel == 'RED':

            # --- Configure Channel 2: Continuous Voltage ---
            print(f"\nConfiguring Channel {RED} for a {ON_DURATION_SECONDS_RED} seconds on, {OFF_DURATION_SECONDS_RED} seconds off train...")
            myPulsePal.programOutputChannelParam('restingVoltage', channel=RED, value=0)
            myPulsePal.programOutputChannelParam('isBiphasic', channel=RED, value=0)
            myPulsePal.programOutputChannelParam('phase1Voltage', channel=RED, value=PULSE_VOLTAGE_RED)
            myPulsePal.programOutputChannelParam('phase1Duration', channel=RED, value=ON_DURATION_SECONDS_RED)
            myPulsePal.programOutputChannelParam('interPulseInterval', channel=BLUE, value=OFF_DURATION_SECONDS_RED)
            myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=RED, value=TOTAL_DURATION_SECONDS)
            print("Channel 2 configuration complete.")
        
        else:
            raise ValueError("Invalid channel selection. Choose 'BLUE' or 'RED'.")

        # 3. Trigger either channel
        print("\nTriggering channel now.")
        if choice:
            if channel == 'BLUE':
                print(f" -> Channel {BLUE} will start immediately and run for {TOTAL_DURATION_SECONDS}s.")
                myPulsePal.triggerOutputChannels(channel1=1, channel2=0, channel3=0, channel4=0)
            else:
                print(f" -> Channel {RED} will start immediately and run for {TOTAL_DURATION_SECONDS}s.")
                myPulsePal.triggerOutputChannels(channel1=0, channel2=1, channel3=0, channel4=0)
        else:
            print(" -> No stimulation will be delivered this trial.")
        
        if choice:
            start_stim = time.time()
        else:
            start_stim = float('nan')

        # 4. Wait for the ENTIRE experiment to finish
        print(f"\nProtocols initiated. The entire experiment will last for {TOTAL_DURATION_SECONDS} seconds.")
        print("You can close this script now; the Pulse Pal will complete the protocols on its own.")
        print("Waiting here for demonstration purposes...")
        time.sleep(TOTAL_DURATION_SECONDS)

        if choice:
            end_stim = time.time()
        else:
            end_stim = float('nan')

        time_log.append((start_stim, end_stim))

        print("\nExperiment finished.")

    except PulsePalError as e:
        print(f"\nERROR: A Pulse Pal error occurred: {e}")
    except Exception as e:
        print(f"\nERROR: A general error occurred: {e}")

#make button to run trials on demand
root = tk.Tk()
root.title("Red/Blue Pulse Trigger")
root.geometry("300x150")    
button = tk.Button(root, text="Run Trial", command=run_trial)
button.pack(pady=20)
root.mainloop()     


file_path = 'red_blue_time_log.txt'
with open(file_path, 'w') as file:
    for lines in time_log:
        line_content = ' '.join(map(str, lines))
        file.write(line_content + '\n')