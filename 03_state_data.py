import time

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="상태·캐시 예제", page_icon="📦", layout="wide")
st.title("📦 Streamlit이 '다시 실행'되는 원리")

# =================================================
# 0. 재실행 눈으로 확인하기
# =================================================
if "run_count" not in st.session_state:
    st.session_state.run_count = 0
st.session_state.run_count += 1

st.info(
    f"🔄 이 코드는 지금까지 **{st.session_state.run_count}번** 실행됐습니다.  \n"
    "👉 아래 아무 버튼이나 눌러 보세요. 누를 때마다 숫자가 올라갑니다 = 코드 전체가 다시 실행됨"
)

# =================================================
# 1. 세션 상태 (session_state)
# =================================================
st.header("1️⃣ 값을 기억하기 — st.session_state")
st.caption("👉 양쪽 +1 버튼을 여러 번 눌러서 결과를 비교해 보세요.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("❌ 일반 변수")
    count = 0                          # 재실행될 때마다 이 줄이 다시 실행 → 0
    if st.button("+1", key="normal"):
        count += 1
    st.metric("현재 값", count)
    st.caption("아무리 눌러도 1 이상 올라가지 않습니다. 매번 0부터 다시 시작하기 때문입니다.")

with col2:
    st.subheader("✅ session_state")
    if "count" not in st.session_state:  # 처음 접속했을 때 딱 한 번만 실행
        st.session_state.count = 0
    if st.button("+1", key="state"):
        st.session_state.count += 1
    st.metric("현재 값", st.session_state.count)
    st.caption("값이 계속 쌓입니다. 브라우저를 새로고침하면 0으로 돌아갑니다.")

st.divider()

# =================================================
# 2. 캐시 (cache_data)
# =================================================
st.header("2️⃣ 오래 걸리는 작업 한 번만 하기 — @st.cache_data")
st.caption("👉 같은 행 수로 양쪽 '불러오기'를 2~3번씩 눌러 보세요. 그다음 행 수를 바꿔서 다시 눌러 보세요.")


def make_data(n_rows):
    """가짜 생산 데이터 생성"""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "날짜": pd.date_range("2026-01-01", periods=n_rows),
        "생산량": rng.integers(80, 120, n_rows),
        "불량수": rng.integers(0, 10, n_rows),
        "라인": rng.choice(["A", "B", "C"], n_rows),
    })


def load_slow(n_rows):                 # 캐시 없음
    time.sleep(2)                      # 큰 파일 읽기·DB 조회처럼 2초 걸린다고 가정
    return make_data(n_rows)


@st.cache_data                         # ← 이 한 줄만 다름
def load_slow_cached(n_rows):
    time.sleep(2)
    return make_data(n_rows)


if "log" not in st.session_state:
    st.session_state.log = []

n = st.radio("불러올 행 수", [30, 60, 90], horizontal=True)

def run_and_log(func, label):
    start = time.time()
    with st.spinner("불러오는 중..."):
        func(n)
    sec = round(time.time() - start, 2)
    st.session_state.log.append({"방식": label, "행 수": n, "걸린 시간(초)": sec})
    return sec

cA, cB = st.columns(2)
with cA:
    st.subheader("🐢 캐시 없음")
    if st.button("불러오기", key="no_cache"):
        st.metric("걸린 시간", f"{run_and_log(load_slow, '🐢 캐시 없음')}초")
    st.caption("매번 2초가 걸립니다.")
with cB:
    st.subheader("⚡ 캐시 있음")
    if st.button("불러오기", key="cache"):
        st.metric("걸린 시간", f"{run_and_log(load_slow_cached, '⚡ 캐시 있음')}초")
    st.caption("처음 보는 행 수만 2초, 이미 불러온 행 수는 0초입니다.")

if st.session_state.log:
    st.write("**📋 실행 기록**")
    st.dataframe(pd.DataFrame(st.session_state.log), hide_index=True)
    b1, b2 = st.columns([1, 5])
    if b1.button("캐시 비우기"):
        load_slow_cached.clear()       # 저장된 결과 삭제 → 다시 2초 걸림
        st.toast("캐시를 비웠습니다.")
    if b2.button("기록 지우기"):
        st.session_state.log = []
        st.rerun()

st.success(
    "정리: 함수에 넣는 값(행 수)이 같으면 저장된 결과를 바로 돌려주고, 처음 보는 값일 때만 실제로 실행합니다.  \n"
    "AI 모델처럼 무거운 객체는 `@st.cache_resource`를 씁니다. (YOLO 앱의 `load_model`)"
)

st.divider()

# =================================================
# 3. 파일 주고받기 + 차트
# =================================================
st.header("3️⃣ 파일 내려받기 → 올리기 → 차트")

st.markdown("**STEP 1.** 샘플 CSV를 내려받으세요.")
st.download_button(
    "⬇ 샘플 CSV 다운로드",
    data=make_data(60).to_csv(index=False).encode("utf-8-sig"),  # utf-8-sig: 엑셀 한글 깨짐 방지
    file_name="sample_production.csv",
    mime="text/csv",
)

st.markdown("**STEP 2.** 내려받은 파일을 다시 올려 보세요.")
uploaded = st.file_uploader("CSV 업로드", type=["csv"])

if uploaded is None:
    st.info("파일을 올리면 표와 차트가 나타납니다.")
else:
    df = pd.read_csv(uploaded)
    st.success(f"✅ {uploaded.name} — {len(df)}행 × {len(df.columns)}열")

    st.markdown("**STEP 3.** 라인을 골라서 결과를 확인하세요.")
    lines = st.multiselect("라인 선택", sorted(df["라인"].unique()), default=sorted(df["라인"].unique()))
    filtered = df[df["라인"].isin(lines)]

    c1, c2 = st.columns([3, 2])
    with c1:
        st.write("📈 일별 생산량")
        st.line_chart(filtered, x="날짜", y="생산량")
    with c2:
        st.write("📊 라인별 불량수 합계")
        st.bar_chart(filtered.groupby("라인")["불량수"].sum())

    with st.expander("📋 원본 데이터 보기"):
        st.dataframe(filtered, hide_index=True)