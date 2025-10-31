# (Only the modified file is shown; unchanged parts remain the same in your repo)
# run_red_blue_pulse.py

from pulse_pal import PulsePalObject, PulsePalError
from CameraTimeToPCTime import calculate_offset_newer, setup_chunk_data, acquire_images
from ReturnValueThread import ReturnValueThread 
import time
import random
import datetime
import tkinter as tk
import PySpin
import threading
import unittest.mock as mock
import cv2
import os
import pandas as pd
import re

NS_PER_S = 1000000000  # Double check this but I'm p sure we have Blackfly S
NEWER_CAMERAS = ['Blackfly S', 'Oryx', 'DL'] 
# --- Parameters You Can Change ---
SERIAL_PORT = 'COM4'                # Your Pulse Pal's port name
TOTAL_DURATION_SECONDS = 10
FRAME_RATE_HZ = 20                  # Camera frame rate in Hz

# --- Channel 1 Parameters (20Hz Pulse Train, BLUE) --- 
BLUE = 2
PULSE_VOLTAGE_BLUE = 5.0
PULSE_FREQUENCY_HZ_BLUE = 20
ON_DURATION_SECONDS_BLUE = 1/(PULSE_FREQUENCY_HZ_BLUE*2)  # ON duration for 20Hz pulse train
OFF_DURATION_SECONDS_BLUE = 1/(PULSE_FREQUENCY_HZ_BLUE*2)  # OFF duration for 20Hz pulse train

print(f"--- {PULSE_FREQUENCY_HZ_BLUE} Hz 465 nm 5HT MEA Experiment ---")
folder_name = input('Input the full folder path where you want to save the video and hit enter: ')
name_file = input('Input the name of the video (formatted something like 20251025_PJA121_intruder5_day4_nophotostim) and hit enter to start: ')
format_file = input('Input the video format (avi, mp4, etc) and hit enter: ')
log_folder_name = 'logs'
camera_log_folder_name = 'camera_logs'

camera_time = input('How long would you like to record for (in seconds)? The default is 10 minutes (600 seconds). For reference, the capture frame rate is ' + str(FRAME_RATE_HZ) + ' Hz: ')
if camera_time == '':
    camera_time = 600
else:
    camera_time = int(camera_time)

num_frames = camera_time * FRAME_RATE_HZ  #20 fps


print('To stop and save the session at any time, close the GUI window or hit the Stop and Save button.')

if not os.path.exists(folder_name):
    os.makedirs(folder_name)
if not os.path.exists(log_folder_name):
    os.makedirs(log_folder_name)

time_rn = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
time_rn = re.sub(r'[^a-zA-Z0-9_.-]', '_', time_rn)

year_month_day = time_rn[:8]

#make a subfolder for the day if it doesn't already exist
try:
    os.mkdir(os.path.join(folder_name, year_month_day))
except FileExistsError:
    pass

try:
    os.mkdir(os.path.join(log_folder_name, year_month_day))
except FileExistsError:
    pass

video_file_path = os.path.join(folder_name, year_month_day, name_file + time_rn + '.'+format_file)

# Clarify width/height explicitly to avoid swaps
frame_width = 720   # pixels (width)
frame_height = 540  # pixels (height)
fourcc = cv2.VideoWriter_fourcc(*'XVID')

# VideoWriter expects frameSize=(width, height)
video_writer = cv2.VideoWriter(video_file_path, fourcc, 20.0, (frame_width, frame_height), isColor=False)

# Check writer opened successfully
if not video_writer.isOpened():
    print(f"ERROR: VideoWriter failed to open for path={video_file_path}, FOURCC='XVID', size=({frame_width},{frame_height})")
    print("Try a different FOURCC (e.g., 'MJPG' and .avi) or confirm codecs on this machine.")
    raise SystemExit(1)

log_file_path = os.path.join(folder_name, year_month_day, log_folder_name, name_file +  time_rn + '_time_log.csv')
camera_log_file_path = os.path.join(folder_name, year_month_day, camera_log_folder_name, name_file +  time_rn + '_camera_log.txt') #save list of PC timestamps that correspond to frames

print('Okay, proceeding. Saving video to ' + video_file_path + ' and time log to ' + log_file_path + '_time_log.csv and camera time log to' + camera_log_file_path )

time_log = [] #log times of stimulations
camera_timelog =[] #save camera-to-PC time conversions

#collect data
list_attacks = []
start_times = []
end_times = []
on_status= []

stop=False

def run_trial(): 
    print(f"You triggered the stimulation. A 20 Hz 465 nm pulse train will run for 10 seconds.")
    choice = random.random() > 0.5 #choose whether or not the stim will be triggred
    try:
        print(f"Connecting to Pulse Pal on {SERIAL_PORT}...")
        myPulsePal = PulsePalObject(SERIAL_PORT)
        print("Connection successful.")
        print(f"\nConfiguring Channel {BLUE} for a {ON_DURATION_SECONDS_BLUE} seconds on, {OFF_DURATION_SECONDS_BLUE} seconds off train...")
        myPulsePal.programOutputChannelParam('restingVoltage', channel=BLUE, value=0)
        myPulsePal.programOutputChannelParam('isBiphasic', channel=BLUE, value=0)
        myPulsePal.programOutputChannelParam('phase1Voltage', channel=BLUE, value=PULSE_VOLTAGE_BLUE)
        myPulsePal.programOutputChannelParam('phase1Duration', channel=BLUE, value=ON_DURATION_SECONDS_BLUE)
        myPulsePal.programOutputChannelParam('interPulseInterval', channel=BLUE, value=OFF_DURATION_SECONDS_BLUE)
        myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=BLUE, value=TOTAL_DURATION_SECONDS)
        print("Channel 2 configuration complete.")
        print("\nTriggering channel now.")
        print(f" -> Stimulation will start immediately and run for {TOTAL_DURATION_SECONDS}s.")
        if choice:
            myPulsePal.triggerOutputChannels(channel1=0,channel2=1,channel3=0, channel4=0)
        start_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
        actually_on = bool(choice)
        print(f"\nProtocols initiated. The entire experiment will last for {TOTAL_DURATION_SECONDS} seconds.")
        time.sleep(TOTAL_DURATION_SECONDS)
        end_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
        effective = input('Did the attack stop? y/n and hit enter: ')
        time_log.append((start_stim, end_stim))
        start_times.append(start_stim)
        end_times.append(end_stim)
        on_status.append(actually_on)
        list_attacks.append(effective)
        print("\n Pulse train finished. Ready for next trial.")
    except PulsePalError as e:
        print(f"\nERROR: A Pulse Pal error occurred: {e}")
    except Exception as e:
        print(f"\nERROR: A general error occurred: {e}")

def main():
    # get the setup for the cameras
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    num_cams = cam_list.GetSize()
    if num_cams == 0:
        print("No cameras detected. Exiting.")
        system.ReleaseInstance()
        return

    for i, cam in enumerate(cam_list):
        cam.Init()

    root = tk.Tk()
    root.title("Pulse Trigger")
    root.geometry("300x150")

    camera_timelog = []
    stopwatch = time.time()
    threads = []

    for i,cam in enumerate(cam_list):
        if str(cam.GetUniqueID()) == 'USB\\VID_1E10&PID_4000\\0180439A_0':
            print('This is moon!')
        elif str(cam.GetUniqueID()) == 'USB\\VID_1E10&PID_4000\\01716E32_0':
            print('This is star!')
        else:
            print('I don\'t recognize this camera! Proceeding anyway...')
        acq_decision = input('Proceed with acquisition for camera ' + str(cam.GetUniqueID()) + '? Enter (y/n) and hit enter: ')
        if acq_decision.lower() not in ('yes', 'y'):
            print(f"Skipping acquisition for camera {cam.GetUniqueID()}.")
            continue

        cam_list[i].Init()
        setup_chunk_data(cam_list[i])

        # Pass height, width in the order that acquire_images expects
        # acquire_images(cam, writer, height, width)
        thread = ReturnValueThread(target=acquire_images, args=(cam_list[i], video_writer, frame_height, frame_width,num_frames,FRAME_RATE_HZ), daemon=True)
        threads.append(thread)

        print(f"Started acquisition thread.")
        tk.Label(root, text="Run Stimulation on Demand:").pack()
        run_button = tk.Button(root, text="Run Pulse Train", command=run_trial)
        save_button = tk.Button(root, text="Stop and Save", command=root.destroy)
        run_button.pack(pady=10)
        save_button.pack(pady=10)
        thread.start()

        if stop:
            break

    
    root.mainloop()

    for thread in threads:
        camera_timelog.append(thread.join())


    video_writer.release()
    print('Video saved to ' + video_file_path)
    
    stim_dict = {'start_times': start_times, 'end_times': end_times, 'on_status': on_status, 'stim_stopped_attack': list_attacks}
    stim_df = pd.DataFrame.from_dict(stim_dict)
    stim_df.to_csv(log_file_path)
    print(f"Time log saved to {log_file_path}")

    for i in range(len(camera_timelog)):
        with open(camera_log_file_path, 'w') as file:
            for entry in camera_timelog[i]:
                line_content = ' '.join(map(str, entry))
                file.write(line_content + '\n')
        print(f"Camera time log saved to {camera_log_file_path}")

    for cam in cam_list:
        try:
            cam.DeInit()
        except Exception:
            pass
        try:
            del cam
        except NameError:
            pass
    cam_list.Clear()
    system.ReleaseInstance()

if __name__ == '__main__':
    main()