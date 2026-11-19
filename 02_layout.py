import streamlit as st

st.set_page_config(page_title="레이아웃 예제", page_icon="🧱", layout="wide")  # 반드시 맨 위
st.title("🧱 화면 구성 예제")

# ---------------------------------
# 1. 사이드바
# ---------------------------------
st.sidebar.header("⚙️ 설정⚙️")
theme_color = st.sidebar.selectbox("강조 색상", ["blue", "green", "orange", "red"])
show_detail = st.sidebar.toggle("상세 정보 보기", value=True)
st.sidebar.caption("사이드바는 설정·필터를 두는 곳으로 많이 씁니다.")

# ---------------------------------
# 2. 화면 분할 (columns)
# ---------------------------------
st.header("1. 화면 분할 - st.columns")

st.write("**같은 비율로 3분할**")
col1, col2, col3 = st.columns(3)
col1.metric("라인 A", "98%", "+1%")
col2.metric("라인 B", "92%", "-3%")
col3.metric("라인 C", "95%", "0%")

st.write("**비율 지정 (2 : 1)** — with 문 사용")
left, right = st.columns([2, 1])
with left:
    st.markdown(f"### :{theme_color}[왼쪽 넓은 영역]")
    st.write("본문, 이미지, 차트 등 메인 내용을 배치합니다.")
    st.image("https://picsum.photos/600/300", caption="샘플 이미지")
with right:
    st.markdown("### 오른쪽 좁은 영역")
    st.write("요약 정보, 버튼 등을 배치합니다.")
    if st.button("새로고침", key="refresh"):
        st.toast("새로고침했습니다!")

st.divider()

# ---------------------------------
# 3. 탭 (tabs)
# ---------------------------------
st.header("2. 탭 - st.tabs")
tab1, tab2, tab3 = st.tabs(["📈 차트", "📋 데이터", "ℹ️ 설명"])
with tab1:
    st.line_chart({"생산량": [10, 25, 18, 30, 42, 38]})
with tab2:
    st.table({"라인": ["A", "B", "C"], "불량률(%)": [1.2, 3.4, 2.1]})
with tab3:
    st.write("탭은 공간을 아끼면서 여러 화면을 전환할 때 유용합니다.")

st.divider()

# ---------------------------------
# 4. 접기/펼치기 (expander) + 조건부 표시
# ---------------------------------
st.header("3. 접기 - st.expander")
with st.expander("👉 클릭해서 펼치기"):
    st.write("자주 보지 않는 상세 설명, 원본 데이터 등을 넣어 둡니다.")

if show_detail:  # 사이드바 토글 값에 따라 보이기/숨기기
    st.info("사이드바의 '상세 정보 보기'가 켜져 있어서 이 메시지가 보입니다.")

st.divider()

# ---------------------------------
# 5. 폼 (form)
# ---------------------------------
st.header("4. 입력 폼 - st.form")
st.caption("폼 밖의 위젯은 값이 바뀔 때마다 재실행되지만, 폼 안의 위젯은 '제출' 버튼을 눌러야 한 번에 반영됩니다.")

with st.form("survey_form"):
    c1, c2 = st.columns(2)               # 폼 안에서도 분할 가능
    name = c1.text_input("이름")
    team = c2.selectbox("소속", ["생산팀", "품질팀", "설비팀"])
    rating = st.slider("교육 만족도", 1, 5, 4)
    submitted = st.form_submit_button("제출")

if submitted:
    if name:
        st.success(f"{team} {name}님, 만족도 {rating}점 제출 완료!")
    else:
        st.error("이름을 입력해 주세요.")

st.divider()

# ---------------------------------
# 6. 빈 자리 (empty) — 같은 위치의 내용을 계속 바꿀 때
# ---------------------------------
st.header("5. 자리 예약 - st.empty")
st.caption("실시간 영상·진행률처럼 같은 자리를 계속 갱신할 때 씁니다. (YOLO 웹캠 예제에서 사용)")
placeholder = st.empty()
if st.button("카운트다운 시작"):
    import time
    for i in range(5, 0, -1):
        placeholder.markdown(f"## ⏳ {i}")
        time.sleep(1)
    placeholder.markdown("## 🚀 시작!")
