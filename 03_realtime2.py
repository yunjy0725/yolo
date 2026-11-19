
import time

import cv2
from ultralytics import YOLO

# Load a model
model = YOLO("yolo26n.pt")

# Open the default webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    raise RuntimeError("Could not open the webcam.")

previous_frame_time = time.perf_counter()

try:
    while True:
        success, frame = cap.read()

        if not success:
            raise RuntimeError("Could not read a frame from the webcam.")

        # 사람(Person)만 탐지 (class 0)
        result = model(
            frame,
            imgsz=320,
            classes=[0],
            verbose=False
        )[0]

        annotated_frame = result.plot()

        # FPS 계산
        current_frame_time = time.perf_counter()
        fps = 1 / (current_frame_time - previous_frame_time)
        previous_frame_time = current_frame_time

        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        cv2.imshow("YOLO Person Detection", annotated_frame)

        # Press q to stop the stream
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
