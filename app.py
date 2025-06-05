import streamlit as st
import os
import tempfile
import shutil
from judge import get_strategies, play_full_league, make_report, payoff
import pandas as pd
from openai import OpenAI

def generate_strategy_code(description, strategy_name):
    """OpenAI를 사용하여 자연어 설명을 바탕으로 전략 코드를 생성"""
    
    # 환경변수에서 OpenAI API 키 가져오기
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    
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
    
    # 사이드바: 도움말
    with st.sidebar:
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
    
    # 메인 화면
    st.markdown("#### 1️⃣ 전략 설명을 자연어로 입력하세요")
    strategy_description = st.text_area(
        "어떤 전략을 만들고 싶나요?",
        placeholder="예: 상대방이 협력하면 협력하고, 배신하면 배신하는 전략",
        height=100
    )
    
    strategy_name = st.text_input(
        "전략 이름을 입력하세요",
        placeholder="예: 나는가끔과거를잊는다",
        max_chars=30
    )
    
    if st.button("🔄 전략 코드 생성"):
        if strategy_description and strategy_name:
            # 전략 코드 생성
            strategy_code = generate_strategy_code(strategy_description, strategy_name)
            
            st.markdown("#### 2️⃣ 생성된 전략 코드")
            st.code(strategy_code, language='python')
            
            # 세션 상태에 저장
            st.session_state.strategy_code = strategy_code
            st.session_state.strategy_name = strategy_name
            st.session_state.strategy_description = strategy_description
            
            # 파일 다운로드
            st.download_button(
                label="📁 전략 파일 다운로드",
                data=strategy_code,
                file_name=f"{strategy_name.lower()}.py",
                mime="text/plain"
            )
            
        else:
            st.warning("전략 설명과 이름을 모두 입력해주세요!")
    
    # 미니 리그전 실행
    if hasattr(st.session_state, 'strategy_code'):
        st.markdown("#### 3️⃣ 미니 리그전 테스트")
        st.markdown("새로 만든 전략을 **팃포탯, 올디, 다우닝**과 리그전을 치러보세요!")
        
        if st.button("⚔️ 미니 리그전 시작!"):
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