import streamlit as st
import requests
from collections import defaultdict
import plotly.express as px
from datetime import datetime
import time
from streamlit_option_menu import option_menu
from PIL import Image

st.set_page_config(layout="wide")    # 페이지를 항상 와이드 모드로 설정합니다.

# 생산정보 및 불량정보를 얻기 위한 POST 요청변수를 정의합니다.
def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

print(get_current_date())


def get_production_data():
    # 생산정보를 얻기 위한 POST 요청변수를 정의합니다.
    production_data = {
        "sUserID": "exgso",
        "sRgnCode": "ZZGSO",
        "sCheckSum": "dju@$i51!k",
        # "sAymd": get_current_date()
        "sAymd": "2023-06-20"
    }
    # 생산정보 API에 POST 요청을 보냅니다.
    response = requests.post("http://gsoptitech.iptime.org/cwebapi/exapi/exprd2", json=production_data)
    return response


def get_defect_data():
    # 불량정보를 얻기 위한 POST 요청변수를 정의합니다.
    defect_data = {
        "sUserID": "exgso",
        "sRgnCode": "ZZGSO",
        "sCheckSum": "dju@$i51!k",
        # "sAymd": get_current_date()
        "sAymd": "2023-06-23"
    }
    # 불량정보 API에 POST 요청을 보냅니다.
    response = requests.post("http://gsoptitech.iptime.org/cwebapi/exapi/exmor3", json=defect_data)
    return response


class ProductionInfo:
    def __init__(self, response, defect_response):
        self.response = response
        self.defect_response = defect_response
        self.all_plants = [f'사출{i}호기' for i in range(1, 15)]  # 사출기 댓수가 늘어나면 range를 수정하면 됨
        self.received_plants = []
        self.defect_types = ["게이트불량", "오염불량", "외경불량", "이물불량", "인식불량", "Cavity무시"]
        self.quantities = defaultdict(int)
        self.total_defects_by_plant = defaultdict(int)
        self.process_defects()

    def process_defects(self):
        if self.defect_response.status_code == 200:
            items = self.defect_response.json()['ITEMS']
            for item in items:
                if item['BTYPE'] in self.defect_types:
                    self.quantities[(item['ITEMNAME'], item['PLANTNAME'], item['BTYPE'])] += int(item['AQTY'])
                    self.total_defects_by_plant[(item['ITEMNAME'], item['PLANTNAME'])] += int(item['AQTY'])

    def display(self):
        total_good_quantity = 0  # 전체 양품 수량
        total_defect_quantity = 0  # 전체 불량 수량
        target_quantity = 20000  # 목표 수량 설정

        if self.response.status_code == 200:
            items = self.response.json()['ITEMS']
            num_models = len(items)  # 모델의 개수 계산
            st.success(f'## 가동중 ({num_models})')  # 모델의 개수 표시
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            col1.markdown("<div style='text-align: center; font-weight: bold;'><h2>모델</H2></div>", unsafe_allow_html=True)
            col2.markdown("<div style='text-align: center; font-weight: bold;'><h2>사출설비</H2></div>", unsafe_allow_html=True)
            col3.markdown("<div style='text-align: center; font-weight: bold;'><h2>양품수량</H2></div>", unsafe_allow_html=True)
            col4.markdown("<div style='text-align: center; font-weight: bold;'><h2>불량수량</H2></div>", unsafe_allow_html=True)
            col5.markdown("<div style='text-align: center; font-weight: bold;'><h2>불량율</H2></div>", unsafe_allow_html=True)
            col6.markdown("<div style='text-align: center; font-weight: bold;'><h2>진행율</H2></div>", unsafe_allow_html=True)

            st.divider()

            for i, item in enumerate(items):
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                col1.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 20px'>{item['ITEMNAME']}</div>", unsafe_allow_html=True)
                col2.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 20px'>{item['PLANTNAME']}</div>", unsafe_allow_html=True)
                total_quantity = int(item['AQTY'])
                defect_quantity = self.total_defects_by_plant[(item['ITEMNAME'], item['PLANTNAME'])]
                col4.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 20px'>{defect_quantity:,}</div>", unsafe_allow_html=True)  # 천 단위 쉼표 구분, 굵게
                good_quantity = total_quantity - defect_quantity
                col3.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 20px'>{good_quantity:,}</div>", unsafe_allow_html=True)  # 천 단위 쉼표 구분, 굵게
                defect_rate = defect_quantity / total_quantity if total_quantity > 0 else 0
                total_good_quantity += good_quantity  # 양품 수량 누적
                total_defect_quantity += defect_quantity  # 불량 수량 누적

                # 진행율 계산
                progress_rate = good_quantity / target_quantity * 100

                col6.markdown(f"<div style='text-align: center; font-size: 15px'>{progress_rate:.2f}%</div>", unsafe_allow_html=True)

                # CSS 적용
                if progress_rate < 100:  # progress_rate가 100 미만인 경우
                    col6.markdown(
                        f"""
                        <style>
                            .stProgress > div:nth-child({i + 1}) > div > div > div {{
                                background-color: red;
                            }}
                        </style>""",
                        unsafe_allow_html=True,
                    )
                    col6.progress(progress_rate / 100)

                elif progress_rate >= 100:  # progress_rate가 100 이상인 경우
                    col6.markdown(
                        f"""
                        <style>
                            .stProgress > div:nth-child({i + 1}) > div > div > div {{
                                background-color: red;
                            }}
                            .stProgress > div:nth-child({i + 1}) > div > div > div::before {{
                                background-color: red;
                            }}
                        </style>""",
                        unsafe_allow_html=True,
                    )
                    col6.progress(1.0)  # progress_rate가 100 이상일 경우, 프로그레스바를 가득 채움

                # 불량율이 1% 이상일 때 빨간색으로, 1% 미만이면 파란색으로 표시, 굵게
                if defect_rate >= 0.01:
                    col5.markdown(
                        f"<div style='text-align: center; color: red; font-weight: bold; font-size: 20px'>{defect_rate * 100:.2f}%</div>",
                        unsafe_allow_html=True)
                else:
                    col5.markdown(
                        f"<div style='text-align: center; color: blue; font-weight: bold;font-size: 20px'>{defect_rate * 100:.2f}%</div>",
                        unsafe_allow_html=True)

                self.received_plants.append(item['PLANTNAME'])  # 받은 사출설비 추가

                st.divider()

            not_received = sorted(list(set(self.all_plants) - set(self.received_plants)),
                                  key=lambda x: int(x.replace("사출", "").replace("호기", "")))

            num_not_received = len(not_received)  # 비가동중인 설비의 개수 계산
            st.error(f'## M/T ({num_not_received})')  # 비가동중인 설비의 개수 표시

            not_received_list = [not_received]

            st.data_editor(
                not_received_list,
                column_config={"sales": st.column_config.ListColumn("비가동중", width="medium")},
                hide_index=True,
            )

        else:
            st.write(f"Error: {self.response.status_code}")

        # 사이드바 하단에 전체 양품 수량과 전체 불량 수량 추가
        total_progress = total_good_quantity / (num_models * target_quantity) * 100



        st.sidebar.markdown(f'## 총 양품 수량: {total_good_quantity:,}')
        st.sidebar.markdown(f'## 총 불량 수량: {total_defect_quantity:,}')
        st.sidebar.markdown(f'## 총 진행율: {total_progress:.2f}%')

        if total_progress >= 100:
            st.sidebar.progress(1.0)
        else:
            st.sidebar.progress(total_progress / 100)

# 불량 데이터 함수
class DefectInfo:
    def __init__(self, response):
        self.response = response
        self.defect_types = ["게이트불량", "오염불량", "외경불량", "이물불량", "인식불량", "Cavity무시"]
        self.quantities = defaultdict(int)
        self.total_defects_by_plant = defaultdict(int)

    def display(self):
        if self.response.status_code == 200:
            items = self.response.json()['ITEMS']
            for item in items:
                if item['BTYPE'] in self.defect_types:
                    self.quantities[(item['ITEMNAME'], item['PLANTNAME'], item['BTYPE'])] += int(item['AQTY'])
                    self.total_defects_by_plant[(item['ITEMNAME'], item['PLANTNAME'])] += int(item['AQTY'])
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.header('모델')
            col2.header('사출설비')
            col3.header('불량수량')
            col4.header('불량유형')
            col5.header('부적합 수량')

            for item_name, plant in sorted(set((key[0], key[1]) for key in self.quantities.keys()),
                                           key=lambda x: (x[0], int(x[1].replace('사출', '').replace('호기', '')))):
                for i, defect_type in enumerate(self.defect_types):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.text(item_name if i == len(self.defect_types) // 2 else "")
                    col2.text(plant if i == len(self.defect_types) // 2 else "")
                    col3.text(str(self.total_defects_by_plant[(item_name, plant)]) if i == len(
                        self.defect_types) // 2 else "")
                    col4.caption(defect_type)
                    col5.text(str(self.quantities[(item_name, plant, defect_type)]))
                with st.expander("More information"):
                    fig = px.pie(
                        values=[self.quantities[(item_name, plant, defect_type)] for defect_type in self.defect_types],
                        names=self.defect_types,
                        title='불량 유형 별 부적합 수량')
                    st.plotly_chart(fig)
        else:
            st.write(f"Error: {self.response.status_code}")


# 생산 정보 및 불량 정보 데이터를 매 10초마다 업데이트합니다.
def update_data(state):
    state.production_response = get_production_data()
    state.defect_response = get_defect_data()
    print("데이터 업데이트:", datetime.now())  # 업데이트된 시간 출력


# Streamlit의 SessionState를 이용하여 캐싱할 데이터를 저장하는 클래스
class _SessionState:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


def get_session_state(**kwargs):
    if 'session_state' not in st.session_state:
        st.session_state['session_state'] = _SessionState(**kwargs)
    return st.session_state['session_state']


# Session 상태를 관리하는 객체를 가져옵니다.
state = get_session_state(production_response=None, defect_response=None)

# 처음 실행시 데이터를 불러옵니다.
if state.production_response is None or state.defect_response is None:
    update_data(state)


# 이미지 로드
image = Image.open('C:\streamit\logo.png')

st.sidebar.image(image, use_column_width=True)

for _ in range(1):  # 5줄의 공백을 추가합니다.
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

# 페이지 설정 부분을 함수화 합니다.
with st.sidebar:
    choose = option_menu("", ["생산정보", "불량정보"],
                         icons=['house', 'camera fill'],
                         menu_icon="None", default_index=0,
                         styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": {"font-size": "25px"},
        "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
        # "nav-link-selected": {"background-color": "#02ab21"},
    }
                         )

if choose == "생산정보":
    # 초기 상태로 재설정
    state.production_response = None
    state.defect_response = None

    if state.production_response is None or state.production_response.status_code != 200:
        state.production_response = get_production_data()
    if state.defect_response is None or state.defect_response.status_code != 200:
        state.defect_response = get_defect_data()

    ProductionInfo(state.production_response, state.defect_response).display()

elif choose == "불량정보":
    # 초기 상태로 재설정
    state.production_response = None
    state.defect_response = None

    if state.defect_response is None or state.defect_response.status_code != 200:
        state.defect_response = get_defect_data()

    DefectInfo(state.defect_response).display()


# 10초 마다 데이터를 업데이트하고 페이지를 새로 고침합니다.
while True:
    time.sleep(10)
    # Add these lines before rerun
    state.production_response = None
    state.defect_response = None
    update_data(state)

