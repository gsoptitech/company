import streamlit as st
import requests
from collections import defaultdict
import plotly.express as px


# 생산정보를 얻기 위한 POST 요청변수를 정의합니다.
production_data = {
    "sUserID": "exgso",
    "sRgnCode": "ZZGSO",
    "sCheckSum": "dju@$i51!k",
    "sAymd": "2023-01-05"
}

def get_production_data():
    # 생산정보 API에 POST 요청을 보냅니다.
    response = requests.post("http://gsoptitech.iptime.org/cwebapi/exapi/exprd2", json=production_data)
    return response


# 불량정보를 얻기 위한 POST 요청변수를 정의합니다.
defect_data = {
    "sUserID": "exgso",
    "sRgnCode": "ZZGSO",
    "sCheckSum": "dju@$i51!k",
    "sAymd": "2023-01-05"
}


def get_defect_data():
    # 불량정보 API에 POST 요청을 보냅니다.
    response = requests.post("http://gsoptitech.iptime.org/cwebapi/exapi/exmor3", json=defect_data)
    return response

class ProductionInfo:
    def __init__(self, response, defect_response):
        self.response = response
        self.defect_response = defect_response
        self.all_plants = [f'사출{i}호기' for i in range(1, 15)]
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
        st.write('# 가동중')
        if self.response.status_code == 200:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.header('모델')
            col2.header('사출설비')
            col3.header('생산수량')
            col4.header('양품수량')
            col5.header('불량수량')
            col6.header('불량율')

            items = self.response.json()['ITEMS']
            
            for i, item in enumerate(items):
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                col1.text(item['ITEMNAME'])
                col2.text(item['PLANTNAME'])
                total_quantity = int(item['AQTY'])
                col3.text(str(total_quantity))
                defect_quantity = self.total_defects_by_plant[(item['ITEMNAME'], item['PLANTNAME'])]
                col5.text(str(defect_quantity))
                good_quantity = total_quantity - defect_quantity
                col4.text(str(good_quantity))
                defect_rate = defect_quantity / total_quantity if total_quantity > 0 else 0
                col6.text(f"{defect_rate * 100:.2f}%")
                with st.expander("More information"):
                    defect_col, chart_col = st.columns(2)
                    for defect_type in self.defect_types:
                        defect_col.text(f"{defect_type}: {self.quantities[(item['ITEMNAME'], item['PLANTNAME'], defect_type)]}")
                    fig = px.pie(values=[self.quantities[(item['ITEMNAME'], item['PLANTNAME'], defect_type)] for defect_type in self.defect_types], 
                                 names=self.defect_types,
                                 title='불량 유형 별 부적합 수량')
                    chart_col.plotly_chart(fig)
                self.received_plants.append(item['PLANTNAME'])
            not_received = sorted(list(set(self.all_plants) - set(self.received_plants)),
                                  key=lambda x: int(x.replace("사출", "").replace("호기", "")))

            st.write('# 비가동중')
            
            not_received_list = [not_received]

            st.data_editor(
                not_received_list,
                column_config={"sales": st.column_config.ListColumn("비가동중",width="medium")},
                hide_index=True,
            )



        else:
            st.write(f"Error: {self.response.status_code}")



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
                    col3.text(str(self.total_defects_by_plant[(item_name, plant)]) if i == len(self.defect_types) // 2 else "")
                    col4.caption(defect_type)
                    col5.text(str(self.quantities[(item_name, plant, defect_type)]))
                with st.expander("More information"):
                    fig = px.pie(values=[self.quantities[(item_name, plant, defect_type)] for defect_type in self.defect_types], 
                                 names=self.defect_types,
                                 title='불량 유형 별 부적합 수량')
                    st.plotly_chart(fig)
        else:
            st.write(f"Error: {self.response.status_code}")



production_response = get_production_data()
defect_response = get_defect_data()

page = st.sidebar.radio("페이지 선택", ["생산정보", "불량정보"])

if page == "생산정보":
    ProductionInfo(production_response, defect_response).display()
elif page == "불량정보":
    DefectInfo(defect_response).display()
