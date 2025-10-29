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


# Usage in your test code


NS_PER_S = 1000000000  # Double check this but I'm p sure we have Blackfly S
NEWER_CAMERAS = ['Blackfly S', 'Oryx', 'DL'] 
# --- Parameters You Can Change ---
SERIAL_PORT = 'COM4'                # Your Pulse Pal's port name
TOTAL_DURATION_SECONDS = 10
#calculate channel settings:

# --- Channel 1 Parameters (20Hz Pulse Train, BLUE) --- 

#we only have channelrhodopsin mice
BLUE = 2
PULSE_VOLTAGE_BLUE = 5.0
PULSE_FREQUENCY_HZ_BLUE = 20
ON_DURATION_SECONDS_BLUE = 1/(PULSE_FREQUENCY_HZ_BLUE*2)  # ON duration for 20Hz pulse train
OFF_DURATION_SECONDS_BLUE = 1/(PULSE_FREQUENCY_HZ_BLUE*2)  # OFF duration for 20Hz pulse train

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

stop=False

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
        
        # store into the per-camera log
        try:
            time_log.append((start_stim, end_stim))
        except Exception:
            # fallback: if time_log wasn't properly initialized, append to a global flat log
            time_log.append((start_stim, end_stim))

        start_times.append(start_stim)
        end_times.append(end_stim)
        on_status.append(actually_on)
        list_attacks.append(effective)

        print("\nExperiment finished.")

    except PulsePalError as e:
        print(f"\nERROR: A Pulse Pal error occurBLUE: {e}")
    except Exception as e:
        print(f"\nERROR: A general error occurBLUE: {e}")



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
    root.title("Pulse Trigger")
    root.geometry("300x150")

    camera_timelog = []
    stopwatch = time.time()
    threads = []

    for i in range(num_cams):
        cam_name = cam_list[i].DeviceModelName.GetValue()
        win = tk.Toplevel(root)
        win.title(f"Camera {i} - {cam_name}")

        cam_list[i].Init()
        setup_chunk_data(cam_list[i])
        thread = ReturnValueThread(target=acquire_images,args=([cam_list[i]]),daemon=True)
        threads.append(thread)
       
        print(f"Started acquisition thread.")
        
        print('Made it past, executing normally!')
        
        tk.Label(root, text="Run Stimulation on Demand:").pack()
        tk.Button(root, text=f"End Session Now (Close GUI) and Save", command=stop_button).pack()

        button = tk.Button(root, text="Run Trial", command=run_trial)
        # button = tk.Button(win, text="Run Trial", command=lambda idx=i, var=channel_var_local: Thread(target=run_trial, args=(idx,var), daemon=True).start())
        button.pack(pady=10)
        thread.start()

        if stop:
            break

    # for thread in threads:
    #     camera_timelog.append(thread.join())

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


