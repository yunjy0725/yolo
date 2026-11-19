
import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
import os
import pandas as pd


# =====================================
# STEP 1. 웹페이지 기본 설정
# =====================================

st.set_page_config(
    page_title="YOLO Object Detection",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 YOLO Object Detection")
st.write("YOLO 모델을 활용한 실시간 객체 탐지 웹페이지입니다.")

st.divider()


# =====================================
# STEP 2. YOLO 모델 불러오기
# =====================================

MODEL_PATH = r"C:\workspace\06_AI\YOLO_trian\best.pt"


@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)


if not os.path.exists(MODEL_PATH):
    st.error(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    st.stop()

model = load_model()


# =====================================
# STEP 3. 이미지 입력
# =====================================

st.subheader("📷 이미지 입력")

input_mode = st.radio(
    "입력 방법을 선택하세요.",
    ["사진 촬영", "이미지 업로드"],
    horizontal=True
)

image = None

if input_mode == "사진 촬영":

    uploaded_file = st.camera_input("사진을 촬영하세요.")

else:

    uploaded_file = st.file_uploader(
        "이미지를 업로드하세요.",
        type=["jpg", "jpeg", "png", "bmp"]
    )

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")


# =====================================
# STEP 4. 원본 이미지 출력
# =====================================

if image is not None:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("원본 이미지")
        st.image(image, use_container_width=True)


    # =====================================
    # STEP 5. YOLO Object Detection
    # =====================================

    if st.button("🔍 Object Detection 실행", type="primary"):

        with st.spinner("객체를 탐지하고 있습니다..."):

            image_array = np.array(image)

            results = model.predict(
                source=image_array,
                conf=0.25,
                verbose=False
            )

            result = results[0]

            # 객체 탐지 결과 이미지
            result_image = result.plot()

            # BGR -> RGB 변환
            result_image = result_image[:, :, ::-1]

        # =====================================
        # STEP 6. 탐지 결과 출력
        # =====================================

        with col2:
            st.subheader("Object Detection 결과")
            st.image(
                result_image,
                use_container_width=True
            )

        # =====================================
        # STEP 7. 탐지 결과 통계
        # =====================================

        object_count = len(result.boxes)

        st.divider()
        st.subheader("📊 Detection Summary")

        metric1, metric2 = st.columns(2)

        metric1.metric(
            "Detected Objects",
            object_count
        )

        metric2.metric(
            "Model Classes",
            len(model.names)
        )

        # =====================================
        # STEP 8. 객체별 상세 정보
        # =====================================

        st.subheader("🔎 Detection Details")

        if object_count > 0:

            detection_data = []

            for index, box in enumerate(result.boxes, start=1):

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                class_name = model.names[class_id]

                # Bounding Box 좌표
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detection_data.append({
                    "No": index,
                    "Class": class_name,
                    "Confidence": round(confidence, 4),
                    "X1": round(x1, 2),
                    "Y1": round(y1, 2),
                    "X2": round(x2, 2),
                    "Y2": round(y2, 2)
                })

            df = pd.DataFrame(detection_data)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            # 결과 이미지 다운로드
            result_pil = Image.fromarray(result_image)

            from io import BytesIO

            image_buffer = BytesIO()
            result_pil.save(image_buffer, format="JPEG")

            st.download_button(
                label="📥 탐지 결과 이미지 다운로드",
                data=image_buffer.getvalue(),
                file_name="detection_result.jpg",
                mime="image/jpeg"
            )

        else:

            st.warning("탐지된 객체가 없습니다.")

else:

    st.info("사진을 촬영하거나 이미지를 업로드해 주세요.")
