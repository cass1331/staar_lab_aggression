# test_write.py
import cv2, numpy as np, sys
w, h = 640, 480
fps = 20.0
out_file = "test_out.mp4"
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # try "XVID" or "MJPG" if mp4v fails

writer = cv2.VideoWriter(out_file, fourcc, fps, (w, h))
print("VideoWriter isOpened:", writer.isOpened())
if not writer.isOpened():
    print("VideoWriter failed to open. Try a different FOURCC or container.")
    sys.exit(1)

for i in range(100):
    # generate a test frame (color gradient + frame index)
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:] = (i % 256, (i*2) % 256, (i*3) % 256)
    cv2.putText(frame, f"frame {i}", (20,50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
    try:
        writer.write(frame)
    except Exception as e:
        print("Exception writing frame", i, e)
        break
writer.release()
print("Done. File:", out_file)