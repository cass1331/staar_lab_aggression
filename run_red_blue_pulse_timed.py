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


# Usage in your test code


NS_PER_S = 1000000000  # Double check this but I'm p sure we have Blackfly S
NEWER_CAMERAS = ['Blackfly S', 'Oryx', 'DL'] 
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

##########for testing without PulsePal ###########
# class MockPulsePalObject:
#     def __init__(self, *args, **kwargs):
#         # Initialize the mock object with any necessary arguments
#         pass

#     def programOutputChannelParam(self, *args, **kwargs):
#         # Simulate the behavior of the programOutputChannelParam method
#         pass
#     def triggerOutputChannels(self, *args, **kwargs):
#         pass

##################################################

print("--- Red/Blue 5HT MEA Experiment ---")

#calculate channel settings:

#blue
period = 1.0 / PULSE_FREQUENCY_HZ_BLUE
pulse_duration_blue = period * 0.5

# time_log will be initialized per-camera in main()
time_log = []

#button control for later
stop=False
# note: GUI root is created in main() so importing this module doesn't open windows

def run_trial(cam_index, channel_var):
    """Trigger a trial for camera `cam_index` using the selected channel_var.

    This function appends the (start, end) tuple to time_log[cam_index].
    """
    channel = channel_var.get()
    print(f"You picked the {channel} channel.")
    choice = random.random() > 0.5 #choose whether or not the stim will be triggered
    try:
        # 1. Connect to the Pulse Pal
        print(f"Connecting to Pulse Pal on {SERIAL_PORT}...")
        myPulsePal = PulsePalObject(SERIAL_PORT)
        # myPulsePal = MockPulsePalObject() # Use mock for testing
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
            myPulsePal.programOutputChannelParam('interPulseInterval', channel=RED, value=OFF_DURATION_SECONDS_RED)
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
            start_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
            print('Stim ON: ' + str(start_stim))
        else:
            start_stim = float('nan')

        # 4. Wait for the ENTIRE experiment to finish
        print(f"\nProtocols initiated. The entire experiment will last for {TOTAL_DURATION_SECONDS} seconds.")
        print("You can close this script now; the Pulse Pal will complete the protocols on its own.")
        # print("Waiting here for demonstration purposes...")
        time.sleep(TOTAL_DURATION_SECONDS)

        if choice:
            end_stim = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
            print('Stim OFF: ' + str(end_stim))
        else:
            end_stim = float('nan')

        # store into the per-camera log
        try:
            time_log[cam_index].append((start_stim, end_stim))
        except Exception:
            # fallback: if time_log wasn't properly initialized, append to a global flat log
            time_log.append((start_stim, end_stim))

        print("\nExperiment finished.")

    except PulsePalError as e:
        print(f"\nERROR: A Pulse Pal error occurred: {e}")
    except Exception as e:
        print(f"\nERROR: A general error occurred: {e}")

def stop_button():
    stop = True


def main():
    # get the setup for the cameras
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    num_cams = cam_list.GetSize()
    if num_cams == 0:
        print("No cameras detected. Exiting.")
        system.ReleaseInstance()
        return

    ############ for testing without cameras #############
    # num_cams = 2  
    # mock_camera1 = mock.Mock()
    # mock_camera1.Init = mock.MagicMock(return_value=None)
    # mock_camera1.BeginAcquisition = mock.MagicMock(return_value=None)

    # mock_camera2 = mock.Mock()
    # mock_camera2.Init = mock.MagicMock(return_value=None)
    # mock_camera2.BeginAcquisition = mock.MagicMock(return_value=None)

    # cam_list = [mock_camera1, mock_camera2]

    #######################################################

    # initialize per-camera logs
    global time_log
    time_log = [[] for _ in range(num_cams)]

    # initialize cameras and report compatibility
    for i, cam in enumerate(cam_list):
        cam.Init()
        # camera_model = cam.DeviceModelName.GetValue()
        # if camera_model in NEWER_CAMERAS:
        #     print(f"Camera model {camera_model} detected. Proceeding with Pulse Pal trials.")
        # else:
        #     print(f"Camera model {camera_model} may not be compatible. Please check settings.")

    # Build one GUI window (Toplevel) per camera, each with independent controls
    # create GUI root here (so importing the module won't create windows)
    root = tk.Tk()
    root.title("Red/Blue Pulse Trigger")
    root.geometry("300x150")

    tk.Label(root, text="Per-camera Red/Blue Pulse Trigger").pack()
    camera_timelog = []
    stopwatch = time.time()
    threads = []

    for i in range(num_cams):
        cam_name = cam_list[i].DeviceModelName.GetValue()
        win = tk.Toplevel(root)
        win.title(f"Camera {i} - {cam_name}")

        cam_list[i].Init()
        setup_chunk_data(cam_list[i])
        thread = ReturnValueThread(target=acquire_images,args=(cam_list[i]))
        threads.append(thread)
        thread.start()
        print(f"Started acquisition thread for Camera {i}.")
        camera_timelog.append(thread.join())

        channel_var_local = tk.StringVar(value="BLUE")
        tk.Label(win, text=f"Camera {i} - Select Channel:").pack()
        tk.Radiobutton(win, text="BLUE", variable=channel_var_local, value="BLUE").pack(anchor='w')
        tk.Radiobutton(win, text="RED", variable=channel_var_local, value="RED").pack(anchor='w')
        tk.Button(root, text=f"End Camera {i} Session Now (Close GUI) and Save", command=stop_button).pack()

        # Button uses a lambda to capture camera index and its channel_var
        button = tk.Button(win, text="Run Trial", command=lambda idx=i, var=channel_var_local: run_trial(idx, var))
        # button = tk.Button(win, text="Run Trial", command=lambda idx=i, var=channel_var_local: Thread(target=run_trial, args=(idx,var), daemon=True).start())
        button.pack(pady=10)

        if stop:
            break

        

    # start the GUI loop once (windows are displayed for each camera)
    root.mainloop()

    
    #run cameras in parallel
    
    # for i, cam in enumerate(cam_list):
        

        # if time.time() - stopwatch > TOTAL_ACQUISITION_SECONDS:
        #     print(f"Total acquisition time of {TOTAL_ACQUISITION_SECONDS} seconds reached. Stopping further GUI windows.")
        #     cam_list[i].EndAcquisition()
        # elif stop:
        #     print("Stop button pressed. Ending acquisition.")
        #     stop = False
        # else:
        #     pass
            

    

    # After GUI closes, save pulse logs
    time_rn = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
    for i in range(num_cams):
        file_path = f'red_blue_time_log_pulse{i}_' + time_rn + '.txt'
        with open(file_path, 'w') as file:
            for entry in time_log[i]:
                # entry is (start, end)
                line_content = ' '.join(map(str, entry))
                file.write(line_content + '\n')
        print(f"Pulse time log saved to {file_path}")

    #After GUI closes, save camera time logs
    time_rn = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
    for i in range(num_cams):
        file_path = f'red_blue_time_log_cam{i}_' + time_rn + '.txt'
        with open(file_path, 'w') as file:
            for entry in camera_timelog[i]:
                # entry is (start, end)
                line_content = ' '.join(map(str, entry))
                file.write(line_content + '\n')
        print(f"Camera time log saved to {file_path}")


    

    # Clean up cameras properly
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


