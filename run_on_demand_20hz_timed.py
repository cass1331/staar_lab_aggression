# (Edited file: run_on_demand_20hz_timed.py)
# run_red_blue_pulse.py

from pulse_pal import PulsePalObject, PulsePalError
from CameraTimeToPCTime import calculate_offset_newer, setup_chunk_data, acquire_images
from ReturnValueThread import ReturnValueThread
import time
import random
import datetime
import tkinter as tk
from tkinter import messagebox
import PySpin
import threading
import queue
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

num_frames = camera_time * 60  # fps


print('To stop and save the session at any time, close the GUI window or hit the Stop and Save button.')


time_rn = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
time_rn = re.sub(r'[^a-zA-Z0-9_.-]', '_', time_rn)

year_month_day = time_rn[:8]

# make a subfolder for the day if it doesn't already exist
try:
    os.mkdir(os.path.join(folder_name, year_month_day))
except FileExistsError:
    pass

try:
    os.mkdir(os.path.join(folder_name, year_month_day,log_folder_name))
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

time_log = [] # log times of stimulations
camera_timelog =[] # save camera-to-PC time conversions

# collect data
list_attacks = []
start_times = []
end_times = []
on_status= []

# queue for handing post-stim actions to main thread
post_stim_queue = queue.Queue()

# polling management
_poll_after_id = None
_poll_running = False

# for acquisition thread management
_acq_threads = []

# stop flag that can be checked by acquisition code if you add support
stop_flag = threading.Event()

def run_trial_background(choice):
    """
    Run PulsePal in a background thread. After the stim ends, put the
    stim metadata into post_stim_queue for the main thread to handle.
    """
    try:
        print(f"Background thread: Connecting to Pulse Pal on {SERIAL_PORT}...")
        myPulsePal = PulsePalObject(SERIAL_PORT)
        print("Connection successful.")
        print(f"\nConfiguring Channel {BLUE} for a {ON_DURATION_SECONDS_BLUE} seconds on, {OFF_DURATION_SECONDS_BLUE} seconds off train...")
        myPulsePal.programOutputChannelParam('restingVoltage', channel=BLUE, value=0)
        myPulsePal.programOutputChannelParam('isBiphasic', channel=BLUE, value=0)
        myPulsePal.programOutputChannelParam('phase1Voltage', channel=BLUE, value=PULSE_VOLTAGE_BLUE)
        myPulsePal.programOutputChannelParam('phase1Duration', channel=BLUE, value=ON_DURATION_SECONDS_BLUE)
        myPulsePal.programOutputChannelParam('interPulseInterval', channel=BLUE, value=OFF_DURATION_SECONDS_BLUE)
        myPulsePal.programOutputChannelParam('pulseTrainDuration', channel=BLUE, value=TOTAL_DURATION_SECONDS)
        print("Channel configuration complete.")
        print("\nTriggering channel now.")
        print(f" -> Stimulation will start immediately and run for {TOTAL_DURATION_SECONDS}s.")
        if choice:
            myPulsePal.triggerOutputChannels(channel1=0,channel2=1,channel3=0, channel4=0)
        start_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
        actually_on = bool(choice)
        print(f"\nProtocols initiated. The entire experiment will last for {TOTAL_DURATION_SECONDS} seconds.")
        # During the sleep we could optionally check stop_flag if immediate abort is needed;
        # for now we simply sleep the duration since pulse pal runs autonomously.
        time.sleep(TOTAL_DURATION_SECONDS)
        end_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
        # Put stim metadata on queue for the main thread to ask the user via Tk dialog
        post_stim_queue.put((start_stim, end_stim, actually_on))
        print("\n Pulse train finished. Ready for next trial (main thread will ask about attack).")
    except PulsePalError as e:
        print(f"\nERROR: A Pulse Pal error occurred: {e}")
    except Exception as e:
        print(f"\nERROR: A general error occurred in pulse thread: {e}")

def run_trial():
    """
    Non-blocking wrapper that decides whether to stimulate, then starts the background thread.
    """
    print(f"You triggered the stimulation. A 20 Hz 465 nm pulse train will run for {TOTAL_DURATION_SECONDS} seconds.")
    choice = random.random() > 0.5 # choose whether or not the stim will be triggered
    t = threading.Thread(target=run_trial_background, args=(choice,), daemon=True)
    t.start()

def _poll_post_stim_queue(root):
    """
    Polls the queue for post-stim metadata and, when present, shows a Tkinter dialog
    to record whether the attack stopped. This must run on the main thread.
    Call root.after(100, _poll_post_stim_queue, root) once to start polling.
    """
    global _poll_after_id, _poll_running
    try:
        while not post_stim_queue.empty():
            start_stim, end_stim, actually_on = post_stim_queue.get_nowait()
            resp = messagebox.askquestion("Attack ended?", "Did the attack stop? (Yes = stopped, No = not stopped)")
            effective = 'y' if resp == 'yes' else 'n'
            # append to global lists (safe because running in main thread)
            time_log.append((start_stim, end_stim))
            start_times.append(start_stim)
            end_times.append(end_stim)
            on_status.append(actually_on)
            list_attacks.append(effective)
            print(f"Recorded stim: {start_stim} -> {end_stim}, was_on={actually_on}, attack_stopped={effective}")
    except queue.Empty:
        pass

    # schedule next poll only if still running
    if _poll_running:
        # pass function and arg directly (no lambda); store handle so we can cancel
        _poll_after_id = root.after(100, _poll_post_stim_queue, root)

def _check_threads_then_close(root):
    """
    Called on main thread via root.after. If all acquisition threads have finished,
    destroy the root to exit mainloop. Otherwise keep polling.
    """
    global _acq_threads, _poll_after_id
    # if there are no threads to wait for, safe to destroy
    if not _acq_threads:
        try:
            root.destroy()
        except Exception:
            pass
        return

    any_alive = any(t.is_alive() for t in _acq_threads)
    if any_alive:
        _poll_after_id = root.after(200, _check_threads_then_close, root)
    else:
        try:
            root.destroy()
        except Exception:
            pass

def stop_and_save(root):
    """
    Signal acquisition to stop, stop the messagebox poller, then wait for
    acquisition threads to end. When they're done, destroy the root so main()
    can continue and save files.
    """
    global _poll_after_id, _poll_running, _acq_threads, stop_flag
    # stop polling for post-stim dialogs
    _poll_running = False
    try:
        if _poll_after_id is not None:
            root.after_cancel(_poll_after_id)
            _poll_after_id = None
    except Exception:
        pass

    # signal the acquisition threads to stop if they respect stop_flag
    stop_flag.set()

    # schedule checking whether threads are done
    root.after(100, _check_threads_then_close, root)

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

    # start polling the post_stim_queue so messageboxes run on the main thread
    global _poll_running, _poll_after_id, _acq_threads
    _poll_running = True
    _poll_after_id = root.after(100, _poll_post_stim_queue, root)

    camera_timelog = []
    stopwatch = time.time()
    threads = []
    _acq_threads = []

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
        # Note: acquire_images doesn't currently accept a stop_flag; if you refactor it,
        # pass stop_flag into it so it can exit early when stop_flag.is_set() is True.
        thread = ReturnValueThread(target=acquire_images, args=(cam_list[i], video_writer, frame_height, frame_width,num_frames,FRAME_RATE_HZ), daemon=True)
        threads.append(thread)
        _acq_threads.append(thread)

        print(f"Started acquisition thread.")
        tk.Label(root, text="Run Stimulation on Demand:").pack()
        run_button = tk.Button(root, text="Run Pulse Train", command=run_trial)
        save_button = tk.Button(root, text="Stop and Save", command=lambda r=root: stop_and_save(r))
        run_button.pack(pady=10)
        save_button.pack(pady=10)
        thread.start()
    
    # enter GUI loop; stop_and_save will destroy root when threads are done
    root.mainloop()

    print('sanity check to ensure exited mainloop')

    # join acquisition threads and collect camera timestamps
    for thread in threads:
        camera_timelog.append(thread.join())

    print('sanity check to ensure collected camera timestamps')

    # release writer and save logs
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









