import os
import sys
import subprocess

# OpenCV 패키지 충돌 임시 해결
if os.environ.get("OPENCV_FIXED") != "1":

    # 일반 OpenCV 제거
    subprocess.run(
        [
            sys.executable, "-m", "pip",
            "uninstall", "-y", "opencv-python"
        ],
        check=False
    )

    # 얼굴 인식 기능이 포함된 OpenCV 재설치
    subprocess.run(
        [
            sys.executable, "-m", "pip",
            "install", "--no-deps", "--force-reinstall",
            "opencv-contrib-python-headless==4.11.0.86"
        ],
        check=True
    )

    os.environ["OPENCV_FIXED"] = "1"


import streamlit as st
import cv2
import numpy as np
import pandas as pd
import csv
import math
import time
import threading

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from av import VideoFrame

# ==========================================
# STEP 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="AI 얼굴 출석체크",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI 얼굴 출석체크 프로그램")
st.write("얼굴을 등록하고 웹캠으로 자동 출석을 확인합니다.")
st.divider()


# ==========================================
# STEP 2. 파일 경로 설정
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "yolo26n.pt")
FACE_DATA_DIR = os.path.join(BASE_DIR, "face_data")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance.csv")

os.makedirs(FACE_DATA_DIR, exist_ok=True)


# ==========================================
# STEP 3. YOLO 모델 불러오기
# ==========================================

@st.cache_resource
def load_yolo_model(model_path):
    return YOLO(model_path)


if not os.path.exists(MODEL_PATH):
    st.error(f"YOLO 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    st.stop()

try:
    yolo_model = load_yolo_model(MODEL_PATH)
except Exception as e:
    st.error(f"YOLO 모델 로딩 실패: {e}")
    st.stop()


# ==========================================
# STEP 4. 얼굴 인식용 함수
# ==========================================
st.write("OpenCV 버전:", cv2.__version__)
st.write("OpenCV 경로:", cv2.__file__)
st.write("CascadeClassifier 존재 여부:", hasattr(cv2, "CascadeClassifier"))
st.write("cv2.face 존재 여부:", hasattr(cv2, "face"))


face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

if face_cascade.empty():
    st.error("얼굴 탐지 모델을 불러오지 못했습니다.")
    st.stop()


def prepare_face(face):
    """얼굴 이미지를 인식하기 좋은 크기와 형태로 변환"""

    face = cv2.resize(face, (200, 200))
    face = cv2.equalizeHist(face)

    return face


# ==========================================
# STEP 5. 한글 화면 출력 함수
# ==========================================

@lru_cache(maxsize=4)
def get_korean_font(size):
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
    ]

    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def draw_korean_text(frame, text, position, size=28, color=(0, 255, 0)):
    """OpenCV 화면에 한글 출력"""

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)

    draw = ImageDraw.Draw(pil_image)
    font = get_korean_font(size)

    draw.text(
        position,
        text,
        font=font,
        fill=(color[2], color[1], color[0])
    )

    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)



class AttendanceProcessor:

    def __init__(self, yolo, recognizer=None, names=None):

        self.yolo = yolo
        self.recognizer = recognizer
        self.names = names or {}

        self.lock = threading.Lock()

        self.countdown_name = None
        self.start_time = None

        self.attended = set()

        # 출석 완료 메시지 표시용
        self.completed_name = None
        self.completed_at = None

        # 기존 출석 기록 불러오기
        if os.path.exists(ATTENDANCE_FILE):
            try:
                df = pd.read_csv(
                    ATTENDANCE_FILE,
                    encoding="utf-8-sig"
                )

                today = datetime.now().strftime("%Y-%m-%d")

                if "날짜" in df.columns and "이름" in df.columns:
                    today_df = df[df["날짜"] == today]

                    self.attended = set(
                        today_df["이름"].astype(str).tolist()
                    )

            except Exception:
                pass


    def update_recognizer(self, recognizer, names):

        with self.lock:
            self.recognizer = recognizer
            self.names = names

            self.countdown_name = None
            self.start_time = None

            self.completed_name = None
            self.completed_at = None


    def save_attendance(self, name):

        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%H:%M:%S")

        file_exists = os.path.exists(ATTENDANCE_FILE)

        with open(
            ATTENDANCE_FILE,
            "a",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            if not file_exists:
                writer.writerow(["날짜", "이름", "출석시간"])

            writer.writerow([today, name, now])

        self.attended.add(name)


    # 민트 네온 카운트다운 디자인
    def draw_countdown(self, frame, remaining, progress):

        height, width = frame.shape[:2]

        center_x = width // 2
        center_y = height // 2

        # 반투명 원형 배경
        overlay = frame.copy()

        cv2.circle(
            overlay,
            (center_x, center_y),
            85,
            (35, 45, 40),
            -1
        )

        cv2.addWeighted(
            overlay,
            0.65,
            frame,
            0.35,
            0,
            frame
        )

        # 원형 테두리
        cv2.circle(
            frame,
            (center_x, center_y),
            75,
            (90, 120, 100),
            5
        )

        # 진행 상태를 보여주는 민트색 원형 게이지
        end_angle = int(360 * progress)

        cv2.ellipse(
            frame,
            (center_x, center_y),
            (75, 75),
            -90,
            0,
            end_angle,
            (180, 255, 190),
            6
        )

        # 카운트다운 숫자
        number = str(remaining)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 3
        thickness = 6

        text_size = cv2.getTextSize(
            number,
            font,
            font_scale,
            thickness
        )[0]

        text_x = center_x - text_size[0] // 2
        text_y = center_y + text_size[1] // 2

        cv2.putText(
            frame,
            number,
            (text_x, text_y),
            font,
            font_scale,
            (180, 255, 190),
            thickness,
            cv2.LINE_AA
        )

        return frame


    def process_frame(self, frame):

        # YOLO로 사람 탐지
        results = self.yolo.predict(
            source=frame,
            imgsz=320,
            classes=[0],
            conf=0.35,
            verbose=False
        )

        result = results[0]

        # YOLO 사람 탐지 박스 표시
        if result.boxes is not None:

            for box in result.boxes:

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (180, 200, 120),
                    2
                )

        # 얼굴 탐지
        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80)
        )

        with self.lock:

            if self.recognizer is None:

                return draw_korean_text(
                    frame,
                    "먼저 얼굴을 등록하고 모델을 학습하세요.",
                    (20, 30),
                    24,
                    (0, 0, 255)
                )

            if len(faces) == 0:

                self.countdown_name = None
                self.start_time = None

                return draw_korean_text(
                    frame,
                    "얼굴을 카메라에 비춰주세요.",
                    (20, 30),
                    28,
                    (180, 255, 190)
                )

            # 가장 큰 얼굴 하나 선택
            x, y, w, h = max(
                faces,
                key=lambda face: face[2] * face[3]
            )

            face_image = gray[y:y+h, x:x+w]
            face_image = prepare_face(face_image)

            # 등록된 얼굴과 비교
            label, confidence = self.recognizer.predict(
                face_image
            )

            threshold = 70

            # 등록되지 않은 얼굴
            if confidence > threshold:

                self.countdown_name = None
                self.start_time = None

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 0, 255),
                    3
                )

                frame = draw_korean_text(
                    frame,
                    "등록되지 않은 얼굴입니다.",
                    (20, 30),
                    26,
                    (0, 0, 255)
                )

                return frame

            name = self.names.get(label, "알 수 없음")

            # 민트 네온 얼굴 인식 박스
            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (180, 255, 190),
                3
            )

            # 출석 완료 메시지를 3초 동안 유지
            if (
                name == self.completed_name
                and self.completed_at is not None
                and time.time() - self.completed_at < 3
            ):

                frame = draw_korean_text(
                    frame,
                    "출석체크가 완료되었습니다!",
                    (20, 30),
                    30,
                    (180, 255, 190)
                )

                frame = draw_korean_text(
                    frame,
                    f"{name}님 출석 완료!",
                    (20, 75),
                    28,
                    (180, 255, 190)
                )

                return frame

            # 이미 오늘 출석한 사람인지 확인
            if name in self.attended:

                frame = draw_korean_text(
                    frame,
                    f"{name}님은 이미 출석했습니다.",
                    (20, 30),
                    26,
                    (180, 255, 190)
                )

                return frame

            # 새로운 사람이 인식되었거나 사람이 바뀐 경우
            if self.countdown_name != name:

                self.countdown_name = name
                self.start_time = time.time()

            elapsed = time.time() - self.start_time

            remaining = max(
                0,
                math.ceil(5 - elapsed)
            )

            # 5초가 지나면 출석 완료
            if elapsed >= 5:

                self.save_attendance(name)

                self.completed_name = name
                self.completed_at = time.time()

                frame = draw_korean_text(
                    frame,
                    "출석체크가 완료되었습니다!",
                    (20, 30),
                    30,
                    (180, 255, 190)
                )

                frame = draw_korean_text(
                    frame,
                    f"{name}님 출석 완료!",
                    (20, 75),
                    28,
                    (180, 255, 190)
                )

            else:

                frame = draw_korean_text(
                    frame,
                    f"{name}님 얼굴 인식 완료!",
                    (20, 30),
                    26,
                    (180, 255, 190)
                )

                # 민트 네온 카운트다운
                progress = min(elapsed / 5, 1.0)

                frame = self.draw_countdown(
                    frame,
                    remaining,
                    progress
                )

                frame = draw_korean_text(
                    frame,
                    "잠시만 기다려 주세요.",
                    (20, 75),
                    24,
                    (180, 255, 190)
                )

        return frame


    def video_frame_callback(self, video_frame):

        frame = video_frame.to_ndarray(
            format="bgr24"
        )

        result_frame = self.process_frame(frame)

        return VideoFrame.from_ndarray(
            result_frame,
            format="bgr24"
        )



# ==========================================
# STEP 7. 출석체크 처리 객체 생성
# ==========================================

if "processor" not in st.session_state:

    st.session_state.processor = AttendanceProcessor(
        yolo_model
    )

if "camera_key" not in st.session_state:
    st.session_state.camera_key = 0


processor = st.session_state.processor


# ==========================================
# STEP 8. 얼굴 등록 화면
# ==========================================

st.header("1️⃣ 얼굴 등록")

st.write("출석체크할 사람의 이름을 입력하고 얼굴 사진을 촬영하세요.")

person_name = st.text_input(
    "이름 입력",
    placeholder="예: 홍길동"
)

captured_image = st.camera_input(
    "얼굴 사진 촬영",
    key=f"register_camera_{st.session_state.camera_key}"
)

if captured_image is not None:

    if st.button("📸 촬영한 얼굴 등록하기"):

        if not person_name.strip():

            st.warning("이름을 먼저 입력해 주세요.")

        else:

            name = person_name.strip()

            # 폴더명으로 사용하기 어려운 문자 제거
            safe_name = "".join(
                c for c in name
                if c not in '\\/:*?"<>|'
            ).strip()

            if not safe_name:

                st.warning("올바른 이름을 입력해 주세요.")

            else:

                image = Image.open(captured_image).convert("RGB")
                image_array = np.array(image)

                gray = cv2.cvtColor(
                    image_array,
                    cv2.COLOR_RGB2GRAY
                )

                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.2,
                    minNeighbors=5,
                    minSize=(80, 80)
                )

                if len(faces) == 0:

                    st.error(
                        "얼굴을 찾을 수 없습니다. "
                        "얼굴이 잘 보이도록 다시 촬영해 주세요."
                    )

                else:

                    x, y, w, h = max(
                        faces,
                        key=lambda face: face[2] * face[3]
                    )

                    face = gray[y:y+h, x:x+w]
                    face = prepare_face(face)

                    person_folder = os.path.join(
                        FACE_DATA_DIR,
                        safe_name
                    )

                    os.makedirs(
                        person_folder,
                        exist_ok=True
                    )

                    existing_files = [
                        f for f in os.listdir(person_folder)
                        if f.lower().endswith((".jpg", ".png"))
                    ]

                    image_number = len(existing_files) + 1

                    save_path = os.path.join(
                        person_folder,
                        f"{image_number}.jpg"
                    )

                    cv2.imwrite(save_path, face)

                    st.success(
                        f"{name}님의 얼굴 사진을 등록했습니다!"
                    )

                    st.session_state.camera_key += 1
                    st.rerun()


# ==========================================
# STEP 9. 등록된 얼굴 확인
# ==========================================

st.divider()
st.subheader("📋 등록된 사람")

registered_people = []

if os.path.exists(FACE_DATA_DIR):

    for name in os.listdir(FACE_DATA_DIR):

        folder = os.path.join(FACE_DATA_DIR, name)

        if os.path.isdir(folder):

            photo_count = len([
                f for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".png"))
            ])

            registered_people.append({
                "이름": name,
                "등록 사진 수": photo_count
            })

if registered_people:

    st.dataframe(
        pd.DataFrame(registered_people),
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("아직 등록된 얼굴이 없습니다.")


# ==========================================
# STEP 10. 얼굴 인식 모델 학습
# ==========================================

st.divider()
st.header("2️⃣ 얼굴 인식 모델 학습")

st.write(
    "등록한 얼굴 사진을 학습합니다. "
    "한 사람당 여러 장의 사진을 등록하면 인식에 도움이 됩니다."
)

if st.button("🧠 얼굴 인식 모델 학습하기"):

    if not hasattr(cv2, "face"):

        st.error(
            "OpenCV 얼굴 인식 기능을 찾을 수 없습니다. "
            "opencv-contrib-python을 설치해 주세요."
        )

    else:

        training_images = []
        training_labels = []
        names = {}

        label_number = 0

        for name in sorted(os.listdir(FACE_DATA_DIR)):

            person_folder = os.path.join(
                FACE_DATA_DIR,
                name
            )

            if not os.path.isdir(person_folder):
                continue

            person_images = []

            for filename in os.listdir(person_folder):

                if not filename.lower().endswith((".jpg", ".png")):
                    continue

                image_path = os.path.join(
                    person_folder,
                    filename
                )

                face = cv2.imread(
                    image_path,
                    cv2.IMREAD_GRAYSCALE
                )

                if face is not None:

                    face = prepare_face(face)

                    person_images.append(face)

            if person_images:

                names[label_number] = name

                for face in person_images:

                    training_images.append(face)
                    training_labels.append(label_number)

                label_number += 1

        if len(training_images) == 0:

            st.warning("학습할 얼굴 사진이 없습니다.")

        else:

            recognizer = cv2.face.LBPHFaceRecognizer_create()

            recognizer.train(
                training_images,
                np.array(training_labels, dtype=np.int32)
            )

            processor.update_recognizer(
                recognizer,
                names
            )

            st.success(
                f"얼굴 인식 모델 학습 완료! "
                f"등록 인원: {len(names)}명 / "
                f"사진 수: {len(training_images)}장"
            )


# ==========================================
# STEP 11. 실시간 출석체크
# ==========================================

st.divider()
st.header("3️⃣ 실시간 출석체크")

st.write(
    "웹캠을 시작하면 등록된 얼굴을 인식합니다. "
    "같은 얼굴이 5초 동안 계속 인식되면 출석 처리됩니다."
)

if processor.recognizer is None:

    st.info(
        "먼저 얼굴을 등록하고 "
        "'얼굴 인식 모델 학습하기' 버튼을 눌러 주세요."
    )

else:

    webrtc_streamer(
        key="face-attendance",
        video_frame_callback=processor.video_frame_callback,
        media_stream_constraints={
            "video": True,
            "audio": False
        },
        async_processing=True,
        rtc_configuration=RTCConfiguration({
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]}
            ]
        })
    )


# ==========================================
# STEP 12. 출석 현황
# ==========================================

st.divider()
st.header("4️⃣ 출석 현황")

if st.button("🔄 출석 현황 새로고침"):

    st.rerun()

if os.path.exists(ATTENDANCE_FILE):

    try:

        attendance_df = pd.read_csv(
            ATTENDANCE_FILE,
            encoding="utf-8-sig"
        )

        st.dataframe(
            attendance_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            label="📥 출석 기록 CSV 다운로드",
            data=attendance_df.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="attendance.csv",
            mime="text/csv"
        )

    except Exception as e:

        st.error(f"출석 기록을 읽을 수 없습니다: {e}")

else:

    st.info("아직 출석 기록이 없습니다.")
