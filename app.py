import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from st_supabase_connection import SupabaseConnection

# 페이지 설정
st.set_page_config(page_title="팀 프로젝트 통합 관리 시스템", layout="wide")

# --- DB 연결 설정 ---
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
st.sidebar.divider()
team_code = st.sidebar.text_input("🔑 팀 코드를 입력하세요", placeholder="예: SSU_TEAM_01").strip()

if not team_code:
    st.sidebar.warning("팀 코드를 입력해야 데이터가 공유됩니다.")
    st.info("왼쪽 사이드바에 우리 팀만의 코드를 입력하고 시작하세요!")
    st.stop()

menu = st.sidebar.radio("화면 이동", ["📅 일정 관리", "🤖 AI 도우미", "📂 자료실"])

# --- [1. 일정 관리] ---
if menu == "📅 일정 관리":
    st.header(f"📅 {team_code} 팀 진행 현황")
    
    # DB에서 데이터 가져오기
    response = conn.table("schedules").select("*").eq("team_id", team_code).execute()
    data = response.data
    
    # 1. 일정 등록
    with st.expander("➕ 새 일정 등록", expanded=False):
        with st.form("schedule_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            task = col1.text_input("과제/항목 명칭")
            owner = col1.text_input("담당자")
            due = col2.date_input("마감 기한", value=datetime.now())
            status = col2.selectbox("진행 상태", ["대기", "진행 중", "완료"])
            
            if st.form_submit_button("일정 저장"):
                if task:
                    conn.table("schedules").insert({
                        "team_id": team_code,
                        "title": task,
                        "owner": owner,
                        "due_date": str(due),
                        "status": status
                    }).execute()
                    st.success("저장되었습니다!")
                    st.rerun()

    # 2. 보기 및 삭제 모드
    tab1, tab2 = st.tabs(["📊 리스트 및 삭제", "🗓️ 캘린더 뷰"])

    with tab1:
        if data:
            df = pd.DataFrame(data)
            display_df = df[["title", "owner", "due_date", "status"]].rename(
                columns={"title":"항목", "owner":"담당", "due_date":"마감", "status":"상태"}
            )
            st.table(display_df)
            
            # --- [여기서부터 삭제 기능] ---
            st.divider()
            st.subheader("🗑️ 일정 삭제")
            # 항목 리스트를 만들어서 선택하게 함
            titles = df['title'].tolist()
            delete_target = st.selectbox("삭제할 항목을 선택하세요", titles)
            
            if st.button("선택한 항목 삭제"):
                conn.table("schedules").delete().eq("team_id", team_code).eq("title", delete_target).execute()
                st.warning(f"'{delete_target}' 항목이 삭제되었습니다.")
                st.rerun()
        else:
            st.info("등록된 일정이 없습니다.")
            
    with tab2:
        st.subheader("🗓️ 이번 달 일정 확인")
        now = datetime.now()
        curr_year, curr_month = now.year, now.month
        cal = calendar.monthcalendar(curr_year, curr_month)
        
        cols = st.columns(7)
        for i, day in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
            cols[i].write(f"**{day}**")
            
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    target_date = f"{curr_year}-{curr_month:02d}-{day:02d}"
                    schedule_on_day = [d for d in data if d['due_date'] == target_date]
                    if schedule_on_day:
                        cols[i].markdown(f"**{day}** 🔴")
                        for item in schedule_on_day:
                            cols[i].caption(f"{item['title']}")
                    else:
                        cols[i].write(str(day))

# --- [2. AI 도우미 / 3. 자료실 생략 (기존과 동일)] ---
elif menu == "🤖 AI 도우미":
    st.header("🤖 Gemini AI 바로가기")
    st.link_button("🚀 Gemini 앱 실행", "https://gemini.google.com/app")

elif menu == "📂 자료실":
    st.header(f"📂 {team_code} 팀 공유 자료실")
    
    # 1. 파일 업로드 섹션
    st.subheader("📤 파일 올리기")
    uploaded_file = st.file_uploader("추가할 파일을 선택하세요", type=['pdf', 'xlsx', 'pptx', 'docx', 'zip', 'png', 'jpg'])
    
    if uploaded_file:
        # 파일 경로 설정 (팀코드 폴더 안에 저장)
        file_path = f"{team_code}/{uploaded_file.name}"
        
        if st.button("서버에 업로드"):
            with st.spinner("파일을 업로드 중입니다..."):
                try:
                    # Supabase Storage에 파일 업로드
                    conn.client.storage.from_("team_files").upload(
                        path=file_path,
                        file=uploaded_file.getvalue(),
                        file_options={"upsert": "true"} # 같은 이름 파일 덮어쓰기 허용
                    )
                    st.success(f"✅ '{uploaded_file.name}' 업로드 성공!")
                    st.rerun()
                except Exception as e:
                    st.error(f"업로드 실패: {e}")

    st.divider()

   # 2. 파일 목록 및 삭제/다운로드 섹션
    st.subheader("📋 우리 팀 자료 목록")
    
    try:
        # 해당 팀 코드 폴더 내의 파일 목록 가져오기
        files = conn.client.storage.from_("team_files").list(team_code)
        
        if files:
            for file in files:
                if file['name'] == '.empty_folder_placeholder':
                    continue
                    
                # 파일당 3개의 컬럼 (파일명, 다운로드 버튼, 삭제 버튼)
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"📄 {file['name']}")
                
                # 다운로드 버튼
                file_url = conn.client.storage.from_("team_files").get_public_url(f"{team_code}/{file['name']}")
                col2.link_button("다운로드", file_url)
                
                # 삭제 버튼 (빨간색 버튼)
                if col3.button("삭제", key=f"del_{file['name']}", type="secondary"):
                    try:
                        # 서버에서 파일 삭제 실행
                        conn.client.storage.from_("team_files").remove([f"{team_code}/{file['name']}"])
                        st.warning(f"🗑️ '{file['name']}' 파일이 삭제되었습니다.")
                        st.rerun() # 목록 갱신을 위해 새로고침
                    except Exception as e:
                        st.error(f"삭제 실패: {e}")
        else:
            st.info("아직 업로드된 파일이 없습니다.")
            
    except Exception as e:
        st.info("아직 생성된 폴더가 없습니다. 파일을 먼저 업로드해주세요.")
