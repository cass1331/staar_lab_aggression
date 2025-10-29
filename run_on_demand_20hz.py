from pulse_pal import PulsePalObject, PulsePalError
import time
import random
import datetime
import tkinter as tk
import re
import threading
import pandas as pd

# --- Parameters You Can Change ---
SERIAL_PORT = 'COM4'                # Your Pulse Pal's port name

TOTAL_DURATION_SECONDS = 10

# --- Channel 1 Parameters (20Hz Pulse Train, BLUE) --- 

#we only have channelrhodopsin mice
BLUE = 2
PULSE_VOLTAGE_BLUE = 5.0
PULSE_FREQUENCY_HZ_BLUE = 20
ON_DURATION_SECONDS_BLUE = 1/(PULSE_FREQUENCY_HZ_BLUE*2)  # ON duration for 20Hz pulse train
OFF_DURATION_SECONDS_BLUE = 1/(PULSE_FREQUENCY_HZ_BLUE*2)  # OFF duration for 20Hz pulse train


print("--- 20 Hz 465 nm 5HT MEA Experiment ---")
name_file = input('Input the name of the video (formatted something like 20251025_PJA121_intruder5_day4_nophotostim) and hit enter to start: ')

time_log = [] #log times of stimulations

#set up GUI window to run trials on demand
root = tk.Tk()
channel_var = tk.StringVar(value="BLUE")
root.title("20 Hz 465 nm Pulse Trigger")
root.geometry("300x150") 

#collect data
list_attacks = []
start_times = []
end_times = []
on_status= []


def run_trial(): 
    print(f"You triggered the stimulation. A 20 Hz 465 nm pulse train will run for 10 seconds.")
    choice = random.random() > 0.5 #choose whether or not the stim will be triggeBLUE
    try:
        # 1. Connect to the Pulse Pal
        print(f"Connecting to Pulse Pal on {SERIAL_PORT}...")
        myPulsePal = PulsePalObject(SERIAL_PORT)
        print("Connection successful.")

        #{ --- Configure pulse train ---
        print(f"\nConfiguring Channel {BLUE} for a {ON_DURATION_SECONDS_BLUE} seconds on, {OFF_DURATION_SECONDS_BLUE} seconds off train...")
        myPulsePal.programOutputChannelParam('restingVoltage', channel=BLUE, value=0)
        myPulsePal.programOutputChannelParam('isBiphasic', channel=BLUE, value=0)
        myPulsePal.programOutputChannelParam('phase1Voltage', channel=BLUE, value=PULSE_VOLTAGE_BLUE)
        myPulsePal.programOutputChannelParam('phase1Duration', channel=BLUE, value=ON_DURATION_SECONDS_BLUE)
        myPulsePal.programOutputChannelParam('interPulseInterval', channel=BLUE, value=OFF_DURATION_SECONDS_BLUE)
        myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=BLUE, value=TOTAL_DURATION_SECONDS)
        print("Channel 2 configuration complete.")

        # 3. Trigger either channel
        print("\nTriggering channel now.")
   
        print(f" -> Stimulation will start immediately and run for {TOTAL_DURATION_SECONDS}s.")
        myPulsePal.triggerOutputChannels(channel1=0,channel2=1,channel3=0, channel4=0)

        start_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
        actually_on = None
        if choice:
            actually_on = True
        else:
            actually_on = False

        # 4. Wait for the ENTIRE experiment to finish
        print(f"\nProtocols initiated. The entire experiment will last for {TOTAL_DURATION_SECONDS} seconds.")
        print("You can close this script now; the Pulse Pal will complete the protocols on its own.")
        print("Waiting here for demonstration purposes...")
        time.sleep(TOTAL_DURATION_SECONDS)

        end_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
        effective = input('Did the attack stop? y/n and hit enter: ')
        actually_on = None
        if choice:
            actually_on = True
        else:
            actually_on = False
        start_times.append(start_stim)
        end_times.append(end_stim)
        on_status.append(actually_on)
        list_attacks.append(effective)

        print("\nExperiment finished.")

    except PulsePalError as e:
        print(f"\nERROR: A Pulse Pal error occurBLUE: {e}")
    except Exception as e:
        print(f"\nERROR: A general error occurBLUE: {e}")

#make button to run trials on demand
tk.Label(root, text="Run Stimulation on Demand:").pack()

button = tk.Button(root, text="Run Trial", command=run_trial)
button.pack(pady=20)
root.mainloop()  

time_rn = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
file_path = name_file +re.sub(r'[^a-zA-Z0-9_.-]', '_', time_rn)+'.csv'

stim_dict = {'start_times': start_times, 'end_times': end_times, 'on_status': on_status, 'stim_stopped_attack': list_attacks}
stim_df = pd.DataFrame.from_dict(stim_dict)

stim_df.to_csv(file_path)

print(f"Time log saved to {file_path}")

