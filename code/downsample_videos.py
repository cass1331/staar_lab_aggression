import cv2
import os

def downsample_video(video_path, output_path, target_width=520, target_height=520):
    #720x540 --> 520x520
    og_width = 720
    og_height = 540

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file: {video_path}")
        return

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (target_height, target_width))
    
    cv2.namedWindow("Show video", cv2.WINDOW_NORMAL) 

    i = 0
    while cap.isOpened():
        ret, frame = cap.read()
        i += 1
        if i % 1000 == 0:
            print(f"Processed {i} frames")
        if i % 3 != 0:
            continue  # Skip frames to achieve 20Hz (assuming original is 60Hz)
        # print(frame[0][0])
        frame_resized = frame[(og_height)//2 - target_height//2:(og_height)//2 + target_height//2,
                              (og_width)//2 - target_width//2:(og_width)//2 + target_width//2]
        # cv2.imshow('Frame', frame_resized)
        # cv2.waitKey(1) 
        if not ret:
            break
        
        out.write(frame_resized)

    cap.release()
    out.release()

def main():
    downsample_video('/Users/jmanasse/Desktop/20251103_PJA123_intruder2_day6_withphotostim20251103_17_18_04.avi','/Users/jmanasse/Desktop/20251103_PJA123_intruder2_day6_withphotostim20251103_17_18_04_downsampled.avi')


if __name__ == '__main__':
    main()
