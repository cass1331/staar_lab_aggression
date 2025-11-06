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

num_frames = camera_time * FRAME_RATE_HZ  # fps


print('Once the session is running, do not close the GUI or command line/terminal until the camera has finished grabbing images.')


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

try:
    os.mkdir(os.path.join(folder_name, year_month_day,camera_log_folder_name))
except FileExistsError:
    pass

video_file_path = os.path.join(folder_name, year_month_day, name_file + time_rn + '.'+format_file)

# Clarify width/height explicitly to avoid swaps
frame_width = 520   # pixels (width)
frame_height = 520  # pixels (height)
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
# list_attacks = []
start_times = []
attack_stop_times = []
end_times = []
on_status= []

# queue for handing post-stim actions to main thread
post_stim_queue = queue.Queue()

# polling management
_poll_after_id = None
_poll_running = False

# for acquisition thread management
_acq_threads = []

# stop flag that can be checked by acquisition code
stop_flag = threading.Event()

# frame queue for live preview (bounded to avoid memory growth)
frame_queue = queue.Queue(maxsize=16)


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
        start_stim = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
        actually_on = bool(choice)
        print(f"\nProtocols initiated. The entire experiment will last for {TOTAL_DURATION_SECONDS} seconds.")
        time.sleep(TOTAL_DURATION_SECONDS)
        end_stim = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
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
    Polls the queue for post-stim metadata and, when present, records stim metadata.
    Runs on the main thread.
    """
    global _poll_after_id, _poll_running
    try:
        while not post_stim_queue.empty():
            start_stim, end_stim, actually_on = post_stim_queue.get_nowait()
            time_log.append((start_stim, end_stim))
            start_times.append(start_stim)
            end_times.append(end_stim)
            on_status.append(actually_on)
            print(f"Recorded stim: {start_stim} -> {end_stim}, was_on={actually_on}")
    except queue.Empty:
        pass

    # schedule next poll only if still running
    if _poll_running:
        _poll_after_id = root.after(100, _poll_post_stim_queue, root)


def display_frames(root):
    """
    Main-thread display function: pop frames from frame_queue and show them using cv2.imshow.
    Scheduled via root.after so it runs on the main thread (safe for OpenCV GUI).
    """
    try:
        # Drain up to a few frames each tick to keep preview responsive and not lag too far
        drained = 0
        while drained < 2:
            try:
                frame = frame_queue.get_nowait()
            except queue.Empty:
                break
            if frame is not None:
                try:
                    cv2.imshow("Behavior Box Live Feed", frame)
                    # process events, small delay; this must be called on main thread
                    cv2.waitKey(1)
                except Exception as e:
                    print(f"Warning: display failed on main thread: {e}")
            drained += 1
    except Exception as e:
        print(f"Warning in display_frames loop: {e}")

    # keep scheduling while GUI is alive
    try:
        root.after(30, display_frames, root)
    except Exception:
        pass


def _check_threads_then_close(root):
    """
    Called on main thread via root.after. If all acquisition threads have finished,
    destroy the root to exit mainloop. Otherwise keep polling.
    """
    global _acq_threads, _poll_after_id
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

    # signal the acquisition threads to stop
    stop_flag.set()

    # schedule checking whether threads are done
    root.after(100, _check_threads_then_close, root)


def record_attack_stop():
    stop_time = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
    attack_stop_times.append(stop_time)
    print(f'You recorded an attack stop at {stop_time}. Don\'t press the button again during this pulse train.')


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
    threads = []
    _acq_threads = []

    # Create the display window on the main thread
    try:
        cv2.namedWindow("Behavior Box Live Feed", cv2.WINDOW_NORMAL)
    except Exception as e:
        print(f"Warning: could not create display window on main thread: {e}")

    for i, cam in enumerate(cam_list):
        uid = str(cam.GetUniqueID())
        if uid == 'USB\\VID_1E10&PID_4000\\0180439A_0':
            print('This is moon!')
        elif uid == 'USB\\VID_1E10&PID_4000\\01716E32_0':
            print('This is star!')
        else:
            print('I don\'t recognize this camera! Proceeding anyway...')
        acq_decision = input('Proceed with acquisition for camera ' + uid + '? Enter (y/n) and hit enter: ')
        if acq_decision.lower() not in ('yes', 'y'):
            print(f"Skipping acquisition for camera {uid}.")
            continue

        cam_list[i].Init()
        setup_chunk_data(cam_list[i])

        # Start acquisition thread: pass stop_flag and frame_queue for live preview
        thread = ReturnValueThread(
            target=acquire_images,
            args=(cam_list[i], video_writer, frame_height, frame_width, num_frames, FRAME_RATE_HZ, stop_flag, frame_queue),
            daemon=False
        )
        threads.append(thread)
        _acq_threads.append(thread)

        print(f"Started acquisition thread.")
        tk.Label(root, text="Run Stimulation on Demand:").pack()
        run_button = tk.Button(root, text="Run Pulse Train", command=run_trial)
        attack_end_button = tk.Button(root, text="Record Attack Stop", command=record_attack_stop)
        save_button = tk.Button(root, text="Stop and Save", command=lambda r=root: stop_and_save(r))
        run_button.pack(pady=10)
        attack_end_button.pack(pady=10)
        save_button.pack(pady=10)
        thread.start()

    # start the display loop in main thread
    root.after(30, display_frames, root)

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
    stim_dict = {'start_times': start_times, 'attack_stop_times': attack_stop_times, 'end_times': end_times, 'on_status': on_status}
    stim_df = pd.DataFrame.from_dict(stim_dict)
    stim_df.to_csv(log_file_path)
    print(f"Time log saved to {log_file_path}")

    for i in range(len(camera_timelog)):
        with open(camera_log_file_path, 'w') as file:
            for entry in camera_timelog[i]:
                line_content = ' '.join(map(str, entry))
                file.write(line_content + '\n')
        print(f"Camera time log saved to {camera_log_file_path}")

    # Clean up cv windows
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

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