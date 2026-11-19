import streamlit as st
from datetime import date

# 텍스트 출력
st.write("Hello")
st.header('1. 텍스트 출력')
st.subheader('2. 작은 제목')
st.text('꾸밈없는 고정폭 텍스트')
st.markdown("**굵게** *기울임* `코드` [링크](https://www.naver.com/)")
st.caption('회색 작은 글씨 설명')
st.code('print("hello python")', language='python')

st.info("안내 메시지")
st.success('성공 메시지')
st.error('오류 메시지')
st.warning("경고 메시지")

st.divider()

# 버튼
st.header('2. 버튼')
if st.button("눌러보세요"):
    st.write('버튼이 눌렸습니다!')
    st.balloons()
else :
    st.write('아직 안눌렸습니다!')

# 위젯 입력
st.header('3. 위젯')

name = st.text_input("이름을 입력하세요: ", placeholder='홍길동')
age = st.number_input('나이: ', min_value=0, max_value=120, value=20)
score = st.slider('만족도 점수:', 0, 100, 70)
job = st.selectbox('직무', ['개발자', '데이터 분석가', '기획자', '기타'])
level = st.radio('AI 경험', ['처음','조금 해봄', '실무 경험'], horizontal=True)
langs = st.multiselect('사용 언어',['python', 'java', 'c', 'JavaScrip'], default=['python'])
agree = st.checkbox('개인정보 수집에 동의합니다.')
memo = st.text_area('하고 싶은 말')
birthday = st.date_input('생일',
    min_value=date(1900, 1, 1),
    max_value=date.today())

st.subheader("입력 결과: ")
if name:
    st.write(f"안녕하세요 **{name}**님 ({age}세, {job})")
    st.write(f"AI 경험 : {level} / 사용언어: {', '.join(langs) if langs else '없음'}")
    st.write(f"만족도 : {score}점, 생일: {birthday}")

    if memo:
        st.write(f"남긴 말 : {memo}")
    if agree:
        st.success('동의 완료!')
    else:
        st.warning('동의가 필요합니다.')
else:
    st.info('이름을 입력하면 결과가 표시됩니다.')

st.divider()

# 지표 표시
st.header('4. 지표 표시')
st.metric(label='오늘 탐지 건수', value='128건', delta='+12건')
st.metric(label='평균 신뢰도', value='0.87', delta='-0.2건')