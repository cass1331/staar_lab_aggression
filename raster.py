import seaborn as sns
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cv2
from tqdm import tqdm

#pseudocode
def absolute_attack_times(video_name, log_name, camera_log_name):
    print('hi!')
    cap = cv2.VideoCapture(video_name)
    if not cap.isOpened():
        print(f"Error opening video file: {video_name}")
        return
    
    camera_times_df = pd.read_csv(camera_log_name,header=None,names=['times'])  #assumes csv with frame # and camera timestamp columns
    #convert to list
    camera_times = list(camera_times_df['times'])
    attack_times = [[],[]]  #2D list to hold attack start and end times  

    
    print('Video opened successfully. You\'ll now see the video displayed frame by frame. Press the spacebar to run through frames, hit \'A\' to mark the beginning of an attack, and hit \'K\' TO mark the end of an attack. Press \'F\' to mark a false alarm and discard attack. Close the video window when you are done marking attacks.')
    cv2.namedWindow("Hand code attacks", cv2.WINDOW_NORMAL)
    #using cv2, iterate through video frames and show window with frame # and camera timestamp displayed
    i=0
    progress_bar = tqdm(total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    while cap.isOpened():
        progress_bar.update(1)
        ret, frame = cap.read()
        key = cv2.waitKey(0) & 0xFF  # Wait indefinitely for a key press
        if key == ord('a'):  # 'A' key to mark attack start
            attack_times[0].append(camera_times[i])  #append camera timestamp for frame i
            print(f"Marked attack start at frame {i}, timestamp {camera_times[i]}")
        elif key == ord('f'):
            if attack_times[0]:  # Ensure there's a start time to remove
                removed_time = attack_times[0].pop()  #remove last attack start time
                print(f"Removed last marked attack start at timestamp {removed_time}")
            else:
                print("No attack start time to remove.")
        elif key == ord('k'):  # 'K' key to mark attack end
            attack_times[1].append(camera_times[i])  #append camera timestamp for frame i
            print(f"Marked attack end at frame {i}, timestamp {camera_times[i]}")
        elif key == 32:  # Spacebar to continue to next frame
            pass  # Just continue to next frame
        else:
            pass  # Ignore other keys
        i += 1  
        cv2.imshow('Hand code attacks', frame)
        if not ret:
            break
    cap.release()
    cv2.destroyAllWindows()
    #input (into terminal) which frame # attack begins and which frame # attack ends
    #append timestamps to 2D
    #save to csv and return list
    
    return attack_times

def main():
    video_name = '/Users/jmanasse/Desktop/stanford/2025-2026/staar_lab_code/video_data/aggression_data/20251117/20251117_PJA122_intruder3_day14_withphotostim20251117_14_58_11.avi'
    log_name = '/Users/jmanasse/Desktop/stanford/2025-2026/staar_lab_code/video_data/aggression_data/20251117/logs/20251117_PJA122_intruder3_day14_withphotostim20251117_14_58_11_time_log.csv'
    camera_log_name = '/Users/jmanasse/Desktop/stanford/2025-2026/staar_lab_code/video_data/aggression_data/20251117/camera_logs/20251117_PJA122_intruder3_day14_withphotostim20251117_14_58_11_camera_log.txt'
    attacks=absolute_attack_times(video_name, log_name, camera_log_name)
    # print(attacks)

if __name__ == '__main__':
    main()


# def plot_raster(attack_times, log_name):
#     #get light on, stop, and light off from log file
#     #create raster plot with lines=absolute attack times, vertical line for stop time, shaded region for light on to light off
#     ax.eventplot(orientation='horizontal')  # Placeholder for actual plotting code
#     pass