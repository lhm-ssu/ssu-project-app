import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from st_supabase_connection import SupabaseConnection # [추가] 설치 필수

# 페이지 설정
st.set_page_config(page_title="팀 프로젝트 통합 관리 시스템", layout="wide")

# --- [추가] DB 연결 설정 ---
# 아까 찾으신 정보를 여기에 넣으세요!
SUPABASE_URL = "https://anupizxgesymviooilky.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFudXBpenhnZXN5bXZpb29pbGt5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUzMTU3NjYsImV4cCI6MjA5MDg5MTc2Nn0.MJkk1XH8ZHb1nl7sq2W2JkgeYQcVgkMkFyH_t4n4XXA"

conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=SUPABASE_URL,
    key=SUPABASE_KEY
)

# 사이드바 메뉴
st.sidebar.title("📌 Project Menu")

# --- [추가] 팀 코드 입력창 ---
# 이 코드가 있어야 팀원끼리 공유되고 다른 팀과 분리됩니다.
st.sidebar.divider()
team_code = st.sidebar.text_input("🔑 팀 코드를 입력하세요", placeholder="예: SSU_TEAM_01").strip()

if not team_code:
    st.sidebar.warning("팀 코드를 입력해야 데이터가 공유됩니다.")
    st.info("왼쪽 사이드바에 우리 팀만의 코드를 입력하고 시작하세요!")
    st.stop()

menu = st.sidebar.radio("화면 이동", ["📅 일정 관리", "🤖 AI 도우미", "📂 자료실"])

# --- [1. 일정 관리: DB 실시간 연동] ---
if menu == "📅 일정 관리":
    st.header(f"📅 {team_code} 팀 진행 현황")
    
    # [수정] 이제 session_state 대신 DB에서 데이터를 가져옵니다.
    response = conn.table("schedules").select("*").eq("team_id", team_code).execute()
    data = response.data
    
    # 1. 일정 등록 (DB에 저장)
    with st.expander("➕ 새 일정 등록", expanded=True):
        with st.form("schedule_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            task = col1.text_input("과제/항목 명칭")
            owner = col1.text_input("담당자")
            due = col2.date_input("마감 기한", value=datetime.now())
            status = col2.selectbox("진행 상태", ["대기", "진행 중", "완료"])
            
            if st.form_submit_button("일정 저장"):
                if task:
                    # [수정] DB에 insert 할 때 team_id를 꼭 넣어줘야 합니다.
                    conn.table("schedules").insert({
                        "team_id": team_code,
                        "title": task,
                        "owner": owner,
                        "due_date": str(due),
                        "status": status
                    }).execute()
                    st.success("데이터가 서버에 실시간 저장되었습니다!")
                    st.rerun()

    # 2. 보기 모드
    tab1, tab2 = st.tabs(["📊 리스트 뷰", "🗓️ 캘린더 뷰"])

    with tab1:
        if data:
            df = pd.DataFrame(data)
            # 깔끔하게 보여주기 위해 컬럼명 변경 및 선택
            display_df = df[["title", "owner", "due_date", "status"]].rename(
                columns={"title":"항목", "owner":"담당", "due_date":"마감", "status":"상태"}
            )
            st.table(display_df)
        else:
            st.info("등록된 일정이 없습니다.")
            
    with tab2:
        st.subheader("🗓️ 이번 달 일정 확인")
        now = datetime.now()
        curr_year, curr_month = now.year, now.month
        cal = calendar.monthcalendar(curr_year, curr_month)
        
        cols = st.columns(7)
        days = ["월", "화", "수", "목", "금", "토", "일"]
        for i, day in enumerate(days):
            cols[i].write(f"**{day}**")
            
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write(" ")
                else:
                    target_date = f"{curr_year}-{curr_month:02d}-{day:02d}"
                    # [수정] DB에서 가져온 데이터로 날짜 체크
                    schedule_on_day = [d for d in data if d['due_date'] == target_date]
                    
                    if schedule_on_day:
                        cols[i].markdown(f"**{day}** 🔴")
                        for item in schedule_on_day:
                            cols[i].caption(f"{item['title']}")
                    else:
                        cols[i].write(str(day))

# --- [2. AI 도우미: 원클릭 이동 버튼] ---
elif menu == "🤖 AI 도우미":
    st.header("🤖 Gemini AI 바로가기")
    st.divider()
    st.link_button("🚀 Gemini(제미나이) 앱 실행", "https://gemini.google.com/app")
    st.caption("※ 로그인이 되어있다면 바로 대화를 시작하실 수 있습니다.")

# --- [3. 자료실] ---
elif menu == "📂 자료실":
    st.header("📂 팀 공유 자료실")
    # 실전 배포 시에는 Storage 기능을 써야 하지만, 우선 UI만 유지합니다.
    st.info("현재 팀 코드로 구분된 환경입니다. 파일 업로드 기능을 시연하세요.")
    uploaded_file = st.file_uploader("문서 선택", type=['pdf', 'xlsx', 'pptx', 'docx', 'zip'])
    if uploaded_file:
        st.success(f"'{uploaded_file.name}' 업로드 완료! (서버 저장 로직 연결 대기 중)")