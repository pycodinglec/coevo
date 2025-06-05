import streamlit as st
import os
import tempfile
import shutil
from judge import get_strategies, play_full_league, make_report, payoff
import pandas as pd
from openai import OpenAI

def check_password():
    """비밀번호 확인 함수"""
    def password_entered():
        """비밀번호가 입력되었을 때 호출되는 함수"""
        if st.session_state["password"] == st.secrets["passwords"]["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 비밀번호는 메모리에서 삭제
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 첫 실행시
        st.text_input(
            "🔐 비밀번호를 입력하세요", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # 비밀번호가 틀린 경우
        st.text_input(
            "🔐 비밀번호를 입력하세요", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😞 비밀번호가 올바르지 않습니다.")
        return False
    else:
        # 비밀번호가 맞는 경우
        return True

def generate_strategy_code(description, strategy_name):
    """OpenAI를 사용하여 자연어 설명을 바탕으로 전략 코드를 생성"""
    
    # Streamlit secrets에서 OpenAI API 키 가져오기
    try:
        api_key = st.secrets["api_keys"]["openai_api_key"]
    except KeyError:
        # secrets.toml에 없으면 환경변수에서 가져오기 (백업)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. secrets.toml 파일을 확인하세요.")
    
    client = OpenAI(api_key=api_key)
    
    # 프롬프트 작성
    prompt = f"""
다음은 죄수의 딜레마 게임을 위한 파이썬 전략 함수를 작성하는 작업입니다.

전략 설명: {description}
함수 이름: {strategy_name}

규칙:
1. 함수는 두 개의 매개변수를 통해 각각 리스트를 전달 받습니다. 이름은 다음과 같습니다: mine(내 행동 기록), yours(상대방 행동 기록)
2. 각 리스트는 'C'(협력) 또는 'D'(배신)로 구성됩니다
3. 함수는 반드시 'C' 또는 'D' 둘 중 하나를 반환해야 합니다
4. 첫 게임일 때는 len(mine) == 0 또는 len(yours) == 0 입니다
5. 필요시 random 모듈을 import할 수 있습니다
6. 주석으로 전략의 동작을 설명해주세요

기존 전략 예시:
- 팃포탯: 첫 게임은 협력, 이후 상대방의 직전 행동을 따라함
- 올디: 항상 배신
- 랜덤: 50% 확률로 협력/배신
- 팃포투탯: 상대방이 연속 2번 배신할 때만 보복

위 설명을 바탕으로 완전한 파이썬 함수를 작성해주세요. 함수 정의부터 시작하여 완전한 코드만 출력하고, 다른 설명은 하지 마세요.
"""

    try:
        response = client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        
        generated_code = response.choices[0].message.content.strip()
        
        # 코드 블록 마크다운 제거 (만약 있다면)
        if generated_code.startswith('```python'):
            generated_code = generated_code[9:]
        if generated_code.startswith('```'):
            generated_code = generated_code[3:]
        if generated_code.endswith('```'):
            generated_code = generated_code[:-3]
        
        return generated_code.strip()
        
    except Exception as e:
        # OpenAI API 오류시 기본 팃포탯 전략으로 폴백
        fallback_code = f"""def {strategy_name}(mine, yours):
    # {description}
    # OpenAI API 오류로 인해 기본 팃포탯 전략을 적용합니다
    n = len(mine)
    if n == 0:
        return 'C'  # 첫 게임은 협력
    
    if yours[-1] == 'C':
        return 'C'
    else:
        return 'D'"""
        
        st.warning(f"OpenAI API 오류가 발생했습니다: {str(e)}")
        st.info("기본 팃포탯 전략으로 대체합니다.")
        return fallback_code

def run_mini_league(new_strategy_code, strategy_name):
    """새 전략과 기존 3개 전략(팃포탯, 올디, 다우닝)으로 미니 리그전 실행"""
    
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp()
    temp_strategies_dir = os.path.join(temp_dir, 'strategies')
    os.makedirs(temp_strategies_dir)
    
    try:
        # 기존 전략들 복사 (팃포탯, 올디, 다우닝)
        base_strategies = ['a.py', 'b.py', 'e.py']  # 팃포탯, 올디, 다우닝
        for strategy_file in base_strategies:
            shutil.copy(f'strategies/{strategy_file}', temp_strategies_dir)
        
        # 새 전략 파일 생성
        new_strategy_file = os.path.join(temp_strategies_dir, f'{strategy_name.lower()}.py')
        with open(new_strategy_file, 'w', encoding='utf-8') as f:
            f.write(new_strategy_code)
        
        # 임시로 작업 디렉토리 변경
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # 리그전 실행
        strategies = get_strategies('strategies')
        total_records = play_full_league('strategies', strategies)
        report_file = make_report(strategies, total_records)
        
        # 결과 읽기
        with open(report_file, 'r', encoding='utf-8') as f:
            result_content = f.read()
        
        # 원래 디렉토리로 복귀
        os.chdir(original_cwd)
        
        return result_content, strategies
        
    finally:
        # 임시 디렉토리 정리
        shutil.rmtree(temp_dir)

def main():
    st.title("🎮 죄수의 딜레마 전략 생성기")
    st.markdown("### 협력의 진화 - 나만의 전략을 만들어보세요!")
    
    # 사이드바: 비밀번호 입력 및 도움말
    with st.sidebar:
        st.markdown("### 🔑 접근 권한")
        
        # 비밀번호 확인
        if not check_password():
            st.stop()  # 비밀번호가 틀리면 여기서 앱 실행 중단
        
        # 로그인 성공 메시지
        st.success("✅ 로그인 성공!")
        
        # 로그아웃 버튼
        if st.button("🚪 로그아웃"):
            st.session_state["password_correct"] = False
            st.rerun()
        
        # 새로고침 버튼
        if st.button("🔄 새로고침 (새 전략 생성)"):
            # 전체 세션 상태 초기화
            for key in list(st.session_state.keys()):
                if key != "password_correct":  # 로그인 상태는 유지
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### 📚 전략 설명 예시")
        st.markdown("""
        - "항상 협력하는 전략"
        - "항상 배신하는 전략"  
        - "상대방의 행동을 따라하는 팃포탯"
        - "연속 2번 배신당하면 보복하는 전략"
        - "70% 확률로 협력하는 전략"
        - "한번 배신당하면 계속 보복하는 전략"
        - "랜덤하게 행동하는 전략"
        """)
        
        st.markdown("### 📝 전략 이름 가이드")
        st.markdown("""
        **좋은 예시:**
        - `나만의전략`
        - `똑똑한팃포탯`
        - `복수전략`
        - `확률적전략`
        
        **피해야 할 것:**
        - `나만의 전략` ❌ (띄어쓰기)
        - `전략 이름` ❌ (띄어쓰기)
        """)
        
        st.info("💡 띄어쓰기는 자동으로 언더스코어(_)로 변경됩니다!")
        
        st.markdown("### 🔄 새 전략 만들기")
        st.markdown("""
        **새로운 전략을 만들고 싶다면:**
        
        상단의 **🔄 새로고침** 버튼을 클릭하세요!
        
        - 입력창 초기화
        - 생성된 코드 삭제
        - 세션 상태 완전 리셋
        """)
        st.warning("⚠️ 현재 작업 중인 전략이 모두 삭제됩니다.")
        
        st.markdown("### ⚠️ 서버 안정성 안내")
        st.markdown("""
        **미니 리그전 기능 비활성화**
        
        웹 서버의 안정성을 위해 CPU 집약적인 
        리그전 시뮬레이션을 비활성화했습니다.
        
        **대안:**
        1. 전략 파일 다운로드
        2. 로컬에서 `python judge.py` 실행
        3. 전체 리그전 결과 확인
        """)
        st.info("💻 로컬 환경에서는 모든 기능이 정상 작동합니다!")
    
    # 메인 화면
    st.markdown("#### 1️⃣ 전략 설명을 자연어로 입력하세요")
    strategy_description = st.text_area(
        "어떤 전략을 만들고 싶나요?",
        placeholder="예: 상대방이 협력하면 협력하고, 배신하면 배신하는 전략",
        height=100
    )
    
    strategy_name_input = st.text_input(
        "전략 이름을 입력하세요",
        placeholder="예: 나는가끔과거를잊는다, 똑똑한팃포탯, 복수전략",
        max_chars=30,
        help="⚠️ 전략 이름에는 띄어쓰기를 사용할 수 없습니다. 띄어쓰기는 자동으로 언더스코어(_)로 변경됩니다."
    )
    
    # 띄어쓰기를 언더스코어로 자동 변환
    strategy_name = strategy_name_input.replace(" ", "_") if strategy_name_input else ""
    
    # 변환된 이름 표시 (원래 입력과 다른 경우)
    if strategy_name_input and strategy_name != strategy_name_input:
        st.info(f"📝 전략 이름이 자동 변환되었습니다: **{strategy_name}**")
    elif strategy_name and not " " in strategy_name_input:
        st.success(f"✅ 전략 이름: **{strategy_name}**")
    
    # 처리 시간 안내 (항상 표시)
    st.info("⏱️ **처리 시간 안내**: o4-mini 추론 모델은 고품질 코드 생성을 위해 **10-30초** 정도 소요됩니다.")
    
    if st.button("🔄 전략 코드 생성"):
        if strategy_description and strategy_name:
            # 로딩 표시와 함께 전략 코드 생성
            with st.spinner("🤖 o4-mini가 전략을 분석하고 있습니다... (약 10-30초 소요)"):
                try:
                    # 진행 상황 표시
                    progress_text = st.empty()
                    progress_text.text("🧠 전략 로직 분석 중...")
                    
                    strategy_code = generate_strategy_code(strategy_description, strategy_name)
                    
                    progress_text.text("✅ 코드 생성 완료!")
                    progress_text.empty()  # 진행 상황 텍스트 제거
                    
                    # 세션 상태에 저장
                    st.session_state.strategy_code = strategy_code
                    st.session_state.strategy_name = strategy_name
                    st.session_state.strategy_description = strategy_description
                    
                except Exception as e:
                    st.error(f"❌ 코드 생성 중 오류가 발생했습니다: {str(e)}")
                    st.stop()
            
        else:
            st.warning("전략 설명과 이름을 모두 입력해주세요!")
    
    # 생성된 코드가 있으면 항상 표시 (다운로드 후에도 유지)
    if hasattr(st.session_state, 'strategy_code') and st.session_state.strategy_code:
        st.markdown("#### 2️⃣ 생성된 전략 코드")
        st.code(st.session_state.strategy_code, language='python')
        
        # 파일 다운로드 버튼 (항상 표시)
        st.download_button(
            label="📁 전략 파일 다운로드",
            data=st.session_state.strategy_code,
            file_name=f"{st.session_state.strategy_name.lower()}.py",
            mime="text/plain",
            key="download_strategy"  # 고유 키 추가
        )
    
    # 미니 리그전 실행 (현재 비활성화)
    if hasattr(st.session_state, 'strategy_code'):
        st.markdown("#### 3️⃣ 미니 리그전 테스트")
        st.markdown("새로 만든 전략을 **팃포탯, 올디, 다우닝**과 리그전을 치러보세요!")
        
        # 리그전 버튼 비활성화
        st.warning("⚠️ **미니 리그전 기능이 일시적으로 비활성화되었습니다.**")
        st.info("💡 웹 서버 안정성을 위해 CPU 집약적인 리그전 시뮬레이션을 비활성화했습니다. 생성된 전략 파일을 다운로드하여 로컬에서 `python judge.py`로 테스트해보세요!")
        
        # 비활성화된 버튼 표시
        st.button("⚔️ 미니 리그전 시작!", disabled=True, help="현재 비활성화됨 - 서버 안정성을 위해")
        
        if False:  # 실행되지 않도록 False로 설정
            with st.spinner("미니 리그전 진행 중..."):
                try:
                    result_content, strategies = run_mini_league(
                        st.session_state.strategy_code, 
                        st.session_state.strategy_name
                    )
                    
                    st.success("미니 리그전 완료!")
                    
                    # 결과 파싱 및 표시
                    lines = result_content.split('\n')
                    
                    # 전략-파일 매핑 찾기
                    strategy_mapping = {}
                    for i, line in enumerate(lines):
                        if line.startswith('file,strategy'):
                            for j in range(i+1, len(lines)):
                                if lines[j].strip() == '':
                                    break
                                parts = lines[j].split(',')
                                if len(parts) == 2:
                                    strategy_mapping[parts[1]] = parts[0]
                    
                    # 순위표 찾기
                    for i, line in enumerate(lines):
                        if line.startswith('ranking,strategy,obtained'):
                            st.markdown("### 🏆 미니 리그전 결과")
                            rank_data = []
                            for j in range(i+1, len(lines)):
                                if lines[j].strip() == '':
                                    break
                                parts = lines[j].split(',')
                                if len(parts) == 3:
                                    rank_data.append({
                                        '순위': parts[0],
                                        '전략': parts[1],
                                        '점수': parts[2]
                                    })
                            
                            df = pd.DataFrame(rank_data)
                            st.dataframe(df, use_container_width=True)
                            
                            # 내 전략 결과 하이라이트
                            my_rank = None
                            for rank in rank_data:
                                if rank['전략'] == st.session_state.strategy_name:
                                    my_rank = rank['순위']
                                    break
                            
                            if my_rank:
                                if my_rank == '1':
                                    st.balloons()
                                    st.success(f"🎉 축하합니다! '{st.session_state.strategy_name}' 전략이 1위를 차지했습니다!")
                                else:
                                    st.info(f"'{st.session_state.strategy_name}' 전략이 {my_rank}위를 기록했습니다.")
                            
                            break
                    
                except Exception as e:
                    st.error(f"리그전 실행 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main() 