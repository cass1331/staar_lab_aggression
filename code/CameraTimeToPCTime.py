# ============================================================================
# Copyright (c) 2001-2020 FLIR Systems, Inc. All Rights Reserved.
# (license header kept)
# ============================================================================
#
# This example shows how to converts the camera's timestamp to system time.
#
import time
import datetime
import PySpin
import cv2
import numpy as np
import queue

NUM_IMAGES = 999999999
NEWER_CAMERAS = ['Blackfly S', 'Oryx', 'DL']
NS_PER_S = 1000000000  # The number of nanoseconds in a second


def is_newer(cam_name: str) -> bool:
    """
    Determine whether the given cam_name is one of the newer cameras.
    """
    for cur_cam_name in NEWER_CAMERAS:
        if cur_cam_name in cam_name:
            return True
    return False


def calculate_offset_older_usb(cam: PySpin.CameraPtr) -> int:
    try:
        cam.TimestampLatch.Execute()
        camera_time = cam.Timestamp.GetValue()
        print('Current camera time:', camera_time)
        system_time = time.time()
        print('Current system time:', system_time)
        offset = system_time - camera_time / NS_PER_S
        return offset
    except PySpin.SpinnakerException as ex:
        print('ERROR:', ex)
        return None


def calculate_offset_older_gev(cam: PySpin.CameraPtr) -> int:
    try:
        nodemap = cam.GetNodeMap()
        nodemap.GetNode('GevTimestampControlLatch').Execute()
        camera_time = nodemap.GetNode('GevTimestampValue').GetValue()
        print('Current camera time:', camera_time)
        system_time = time.time()
        print('Current system time:', system_time)
        offset = system_time - camera_time / NS_PER_S
        return offset
    except PySpin.SpinnakerException as ex:
        print('ERROR:', ex)
        return None


def calculate_offset_newer(cam: PySpin.CameraPtr) -> int:
    try:
        cam.TimestampLatch.Execute()
        camera_time = cam.TimestampLatchValue.GetValue()
        system_time = time.time()
        offset = system_time - camera_time / NS_PER_S
        return offset
    except PySpin.SpinnakerException as ex:
        print('ERROR:', ex)
        return None


def acquire_images(cam, writer, height, width, num_frames, frame_rate_hz, stop_flag=None, frame_queue: queue.Queue = None):
    """
    Acquire images from camera and return PC timestamps.

    Arguments:
    - cam: PySpin camera object
    - writer: cv2.VideoWriter (already opened)
    - height, width: requested frame size (height, width)
    - num_frames: maximum frames to acquire
    - frame_rate_hz: requested FPS (used only to set camera)
    - stop_flag: threading.Event that, when set, causes acquisition to stop early
    - frame_queue: optional queue.Queue to which frames will be pushed for display by main thread
    Returns:
    - list of timestamp strings (pc timestamps) on success
    - False on error
    """
    try:
        nodemap_tldevice = cam.GetTLDeviceNodeMap()
        device_type = PySpin.CEnumerationPtr(nodemap_tldevice.GetNode('DeviceType')).GetIntValue()
        device_name = cam.DeviceModelName()
        nodemap = cam.GetNodeMap()

        # Disable automatic frame rate
        node_frame_rate_auto = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionFrameRateAuto"))
        if PySpin.IsAvailable(node_frame_rate_auto) and PySpin.IsWritable(node_frame_rate_auto):
            node_frame_rate_auto_off = node_frame_rate_auto.GetEntryByName("Off")
            if PySpin.IsAvailable(node_frame_rate_auto_off) and PySpin.IsReadable(node_frame_rate_auto_off):
                node_frame_rate_auto.SetIntValue(node_frame_rate_auto_off.GetValue())

        # Enable frame rate control
        node_frame_rate_enable = PySpin.CBooleanPtr(nodemap.GetNode("AcquisitionFrameRateEnabled"))
        if PySpin.IsAvailable(node_frame_rate_enable) and PySpin.IsWritable(node_frame_rate_enable):
            node_frame_rate_enable.SetValue(True)

        node_frame_rate = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
        if PySpin.IsAvailable(node_frame_rate) and PySpin.IsWritable(node_frame_rate):
            node_frame_rate.SetValue(float(frame_rate_hz))

        print('Device name:', device_name)
        if is_newer(device_name):
            calculate_offset = calculate_offset_newer
            print('This is a newer camera')
        elif device_type == PySpin.DeviceType_GEV:
            calculate_offset = calculate_offset_older_gev
            print('This is an older GEV camera')
        elif device_type == PySpin.DeviceType_U3V:
            calculate_offset = calculate_offset_older_usb
            print('This is an older U3V camera')
        else:
            calculate_offset = calculate_offset_newer

        # Compute offset once if possible
        try:
            cam_offset = calculate_offset(cam)
            print(f'Camera offset is {cam_offset}')
        except Exception:
            cam_offset = None
            print('Warning: failed to compute camera offset before acquisition; will compute per-frame if needed.')

        # Try to set width/height
        try:
            cam.Width.SetValue(width)
            cam.Height.SetValue(height)
        except Exception:
            print("Couldn't access camera width and height; continuing with camera defaults.")

        cam.BeginAcquisition()

        pc_timestamps = []
        for i in range(num_frames):
            # Check for external stop
            if stop_flag is not None and stop_flag.is_set():
                print("Stop flag detected in acquire_images; breaking acquisition loop.")
                break

            if i % 10000 == 0:
                print('Recording in progress. Acquired {} images...'.format(i))

            try:
                image = cam.GetNextImage(1000)
            except PySpin.SpinnakerException as ex:
                print('ERROR getting next image:', ex)
                continue

            if image.IsIncomplete():
                print('Warning: image {} incomplete'.format(image.GetFrameID()))
                try:
                    image.Release()
                except Exception:
                    pass
                continue

            # Get image data and write frame
            try:
                image_data = image.GetData().reshape(height, width, 1)  # monochrome
                # Squeeze to 2D for display
                frame_for_display = image_data.squeeze()
            except Exception:
                # fallback: attempt to get numpy array via GetNDArray()
                try:
                    image_data = image.GetNDArray()
                    if image_data.ndim == 3 and image_data.shape[2] == 3:
                        # convert to grayscale if needed
                        frame_for_display = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
                    else:
                        frame_for_display = image_data
                except Exception:
                    frame_for_display = None
                    image_data = None

            if image_data is not None:
                try:
                    writer.write(image_data)
                except Exception as e:
                    print(f"Warning: failed to write frame to writer: {e}")

            # Send frame to display queue if requested (non-blocking)
            if frame_queue is not None and frame_for_display is not None:
                try:
                    frame_queue.put_nowait(frame_for_display)
                except queue.Full:
                    # drop frame if queue is full (keeps worker from blocking)
                    pass

            # Process chunk timestamp
            try:
                chunk_data = image.GetChunkData()
                timestamp = chunk_data.GetTimestamp()
                if cam_offset is not None:
                    offset_value = cam_offset
                else:
                    try:
                        offset_value = calculate_offset(cam)
                    except Exception:
                        offset_value = 0
                converted_timestamp = timestamp / NS_PER_S + offset_value
                timestamp_full = datetime.datetime.fromtimestamp(converted_timestamp).strftime('%Y-%m-%d_%H:%M:%S.%f')
                pc_timestamps.append(timestamp_full)
            except Exception as e:
                print(f"Warning: failed to get chunk timestamp: {e}")

            try:
                image.Release()
            except Exception:
                pass

        # Cleanup acquisition
        try:
            cam.EndAcquisition()
        except Exception:
            print("Warning: cam.EndAcquisition() raised an exception during cleanup.")

        print("Okay, finished acquiring images. You can hit Stop and Save or close the GUI to save and exit. Do NOT Control-C or you will lose the log files and be sad.")
        return pc_timestamps

    except PySpin.SpinnakerException as ex:
        print('ERROR:', ex)
        try:
            cam.EndAcquisition()
        except Exception:
            pass
        return False


def setup_chunk_data(cam: PySpin.CameraPtr) -> bool:
    """
    Sets up chunk data to include the image timestamp for the given camera.
    Returns True on success, False on error.
    """
    try:
        cam.ChunkModeActive.SetValue(True)
        cam.ChunkSelector.SetValue(PySpin.ChunkSelector_Timestamp)
        cam.ChunkEnable.SetValue(True)
    except PySpin.SpinnakerException as ex:
        print('ERROR:', ex)
        return False

    return True