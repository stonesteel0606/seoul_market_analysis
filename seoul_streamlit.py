#!/usr/bin/env python
# coding: utf-8
# %%

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
import streamlit as st
plt.rc('font', family='NanumGothic')
from urllib.request import urlopen
import json
import plotly.express as px
import seaborn as sns
seoul_geo_url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"

st.set_page_config(page_title="My Dashboard", page_icon=":bar_chart:", layout="wide")

with urlopen(seoul_geo_url) as response:
    seoul_geojson = json.load(response)

# %%
df_market = pd.read_csv('seoul_data/상권_추정매출.csv(2017_2021).csv')
df_lease = pd.read_csv('seoul_data/자치구_평당임대료.csv', encoding='cp949')


# %%

# 상권 매출정보와 평당 임대료 df를 넣으면 병합한 데이터 프레임을 준다
# 구별 평당 임대료, 월평균 매출, 객단가까지 함쳐서 준다
def get_dataframe(df_market, df_lease):
    temp_list = []
    
    df_market = df_market[df_market['기준_년_코드'] == 2021]
    df_lease = df_lease.set_index('Unnamed: 0')
    
#    구별 평당 임대료 데이터 넣기
    for gu in df_market['구'].unique():
        df_temp = df_market[df_market['구'] == gu].copy()
        df_temp['평당 임대료']= df_lease.loc[gu, '연평균임대료']
        temp_list.append(df_temp)
    df_temp = pd.concat(temp_list)
    
#     매장 월평균 매출 열 추가하기
    df_temp['매장 월평균 매출'] = df_temp['분기당_매출_금액'] / (df_temp['점포수'] * 3)
    
#     객단가 계산하기
    df_temp['객단가'] = df_temp['분기당_매출_금액'] / df_temp['분기당_매출_건수']
    
    return df_temp


# %%
df = get_dataframe(df_market, df_lease)


# %%
def get_sales_lease_top5(service_name, surface_area, df):
    
    df_temp = pd.DataFrame()
#     선택 업종의 데이터만 가져오기
    df_service = df[df['서비스_업종_코드_명'].str.contains(service_name)].copy()
    
#     구별 매출 평균, 평당 임대료 값 가져오기
    for gu in df['구'].unique():
        df_temp.loc[0, gu] = round(df_service[df_service['구'] == gu]['매장 월평균 매출'].mean(), 0)
        df_temp.loc[1, gu] = df_service[df_service['구'] == gu]['평당 임대료'].mean()
        df_temp.loc[2, gu] = round(df_service[df_service['구'] == gu]['객단가'].mean(), 0)
        df_temp.loc[3, gu] = df_service[df_service['구'] == gu]['lat'].mean()
        df_temp.loc[4, gu] = df_service[df_service['구'] == gu]['lot'].mean()
        
#   df_temp 형태 및 열 이름 바꿔주기      
    df_temp = df_temp.T
    df_temp.columns = ['월평균 매출', '평당 임대료', '평균 객단가', '위도', '경도']
    
#     월평균 매출 - 임대료 값, 임대료 비율 추가하기
    df_temp['매출-임대료'] = df_temp['월평균 매출'] - (df_temp['평당 임대료'] * surface_area)
    df_temp['임대료'] = df_temp['평당 임대료'] * surface_area
    df_temp['임대료 비율'] = (df_temp['평당 임대료'] * surface_area) / df_temp['월평균 매출'] * 100
    df_temp = df_temp.sort_values(by='평당 임대료', ascending = True) 
    
#     plt.figure(1)
#     plt.barh(df_temp['매출-임대료'].tail())
#     df_temp['매출-임대료'].tail().plot(kind='barh', 
#                                            title=f'{service_name} 업종 매출-임대료 상위 top5 구')
    return df_temp


# %%
def get_service_seoul_data(service_name, df):
    df_temp = pd.DataFrame()
    
    #     선택 업종의 데이터만 가져오기
    df_service = df[df['서비스_업종_코드_명'].str.contains(service_name)]
    
    #     해당 업종 2021년 전체 매출, 점포수 합
    df_temp.loc[0, '서울_전체_매출'] = df_service['분기당_매출_금액'].sum()
    df_temp.loc[0, '서울_전체_점포수'] = df_service[df_service['기준_분기_코드'] == 4]['점포수'].sum()
     
    #     2021년 분기별 매출합
    for no in range(1, 5):
        df_temp.loc[0, f'서울_전체_매출_{no}분기'] = df_service[df_service['기준_분기_코드'] == no]['분기당_매출_금액'].sum()
        
    #     주중, 주말 매출합
    df_temp.loc[0, '주중_매출합'] = df_service['주중_매출_금액'].sum()
    df_temp.loc[0, '주말_매출합'] = df_service['주말_매출_금액'].sum()
    
    #     남성, 여성 매출합
    df_temp.loc[0, '남성_매출합'] = df_service['남성_매출_금액'].sum()
    df_temp.loc[0, '여성_매출합'] = df_service['여성_매출_금액'].sum()
    df_temp.loc[0, '남성_객단가'] = df_service['남성_매출_금액'].sum() / df_service['남성_매출_건수'].sum()
    df_temp.loc[0, '여성_객단가'] = df_service['여성_매출_금액'].sum() / df_service['여성_매출_건수'].sum()

    #     요일별 매출 금액
    for day_name in list('월화수목금토일'):
        df_temp.loc[0, f'{day_name}_매출합'] = df_service[f'{day_name}요일_매출_금액'].sum()
    
    #     연령대별 매출 추이
    for no in range(1, 7):
        if no != 6:
            df_temp.loc[0, f'{no}0대_매출합'] = df_service[f'연령대_{no}0_매출_금액'].sum()
        else:
            df_temp.loc[0, f'{no}0대 이상_매출합'] = df_service[f'연령대_{no}0_이상_매출_금액'].sum()
    
    #     연령별 객단가
    for no in range(1, 7):
        if no != 6:
            df_temp.loc[0, f'{no}0대_객단가'] = df_service[f'연령대_{no}0_매출_금액'].sum() / df_service[f'연령대_{no}0_매출_건수'].sum()
        else:
            df_temp.loc[0, f'{no}0대 이상_객단가'] = df_service[f'연령대_{no}0_이상_매출_금액'].sum() / df_service[f'연령대_{no}0_이상_매출_건수'].sum()
    
     #     시간대 매출금액  '시간대_00~06_매출_금액'
    df_temp.loc[0, '00~06_매출합'] = df_service['시간대_00~06_매출_금액'].sum()
    df_temp.loc[0, '06~11_매출합'] = df_service['시간대_06~11_매출_금액'].sum()
    i = 11
    while True:
        
        if i != 17:
            df_temp.loc[0, f'{i}~{i+3}_매출합'] = df_service[f'시간대_{i}~{i+3}_매출_금액'].sum()
            i += 3
            if i >= 24:
                break
        else:
            df_temp.loc[0, f'{i}~{i+4}_매출합'] = df_service[f'시간대_{i}~{i+4}_매출_금액'].sum()
            i += 4
    
    
    return df_temp

# %%
with st.expander("==== 업종 참고(펼쳐보기) ===="):
    # 펼쳐진 내용 작성
    st.write(df['서비스_업종_코드_명'].unique())
    
service_name = st.text_input(label="업종을 입력해 주세요", value="커피")
surface_area = st.number_input(label="평수를 입력해 주세요", value=20)
service_search = st.button("Confirm")

gu_name = st.text_input(label="구 이름을 입력해 주세요")
gu_search = st.button("검색")

row1_1, row1_2= st.columns([1, 1])
row2_1, row2_2, row2_3 = st.columns([1, 1,1])
row3_1, row3_2 = st.columns([1, 1])
row4_1, row4_2 = st.columns([1, 1])


            
if service_search:
    df_sales = get_sales_lease_top5(service_name, surface_area, df)
    df_several = get_service_seoul_data(service_name, df)
    df_sales['시군구'] = df_sales.index
    
    with row1_1:
        st.subheader(f'{service_name} 업종 매출 분석')
        fig = px.choropleth(df_sales, geojson=seoul_geojson, color="매출-임대료",
                        locations=df_sales.index, featureidkey="properties.name", labels="시군구명",
                        projection="mercator", color_continuous_scale='Blues')
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(title_text = f'{service_name} 업종 (매출-임대료) 비교_{surface_area}평 기준', 
                          title_font_size = 20,  width=800, height=600, template='plotly_dark')
    
        st.plotly_chart(fig)
    
    with row1_2:
        row1_2_1, row1_2_2= st.columns([1, 1])

        
        with row1_2_1:
            df_seoul_sales = df_several[['서울_전체_매출', '서울_전체_점포수']]
            df_gender = round(df_several[['남성_객단가', '여성_객단가']], -1)
            df_seoul_sales.columns = ['전체 매출합(원)', '점포수(개)']
            df_seoul_sales = df_seoul_sales.T
            df_seoul_sales.columns = ['내용']
            df_gender.index = ['객단가(원/인)']
            df_gender.columns = ['남성', '여성']
            
            st.dataframe(df_seoul_sales)
            st.dataframe(df_gender)
            
            df_gender_sales = df_several[['남성_매출합', '여성_매출합']]
            df_gender_sales.columns = ['남성', '여성']
            df_gender_sales = df_gender_sales.T
            
            fig, ax = plt.subplots()

            labels = df_gender_sales.index
            colors = sns.color_palette('Blues_r', 2)
            wedgeprops={'width': 0.7, 'edgecolor': 'w', 'linewidth': 5}
            ax.pie(df_gender_sales[0], labels=labels, autopct='%.1f%%', startangle=260, 
                   counterclock=False, colors=colors, wedgeprops=wedgeprops)
            plt.title('성별 매출 분포')
            st.pyplot(fig)  
        
        with row1_2_2:
            st.write('hello')
               
    with row2_1:
        tab1, tab2= st.tabs(['수익 top5 구' , '수익 하위 top 5 구'])
        
        with tab1:
#    매출-임대료 top5 구
            df_plt1 = df_sales.sort_values(by='매출-임대료', ascending=False).head()
            plt.style.use('default')
            plt.rcParams['figure.figsize'] = (7, 4)
            plt.rc('font', family='NanumGothic')
            plt.rcParams['font.size'] = 12
            plt.style.use('dark_background')
            colors = sns.color_palette('Blues_r', len(df_plt1['시군구']))
            
            fig, ax1 = plt.subplots()

            ax1.bar(df_plt1['시군구'], df_plt1['매출-임대료'], color=colors, alpha=0.7, width=0.2, label='매출-임대료')
            ax1.axhline(df_sales['매출-임대료'].mean(),label='Mean', c='r', ls=':')

            ax1.set_xlabel('시군구')
            ax1.set_ylabel('매출-임대료 (원)')
            ax1.tick_params(axis='both', direction='in')

            ax2 = ax1.twinx()
            ax2.plot(df_plt1['시군구'], df_plt1['평균 객단가'], '-s', color='white', markersize=4, linewidth=2, alpha=0.7, label='객단가')
                # ax2.set_ylim(7000, 11000)
            ax2.set_ylabel('객단가 (원/인)')
            ax2.tick_params(axis='y', direction='in')

            ax1.set_zorder(ax2.get_zorder() - 10)
            ax1.patch.set_visible(False)

            ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2))
            ax2.legend(loc='upper center', bbox_to_anchor=(0.85, -0.2))

            st.pyplot(fig)

        with tab2:
            df_plt2 = df_sales.sort_values(by='매출-임대료', ascending=False).tail()
            plt.style.use('default')
            plt.rcParams['figure.figsize'] = (7, 4)
            plt.rc('font', family='NanumGothic')
            plt.style.use('dark_background')
            plt.rcParams['font.size'] = 12
            colors = sns.color_palette('Blues_r', len(df_plt2['시군구']))
            fig, ax1 = plt.subplots()

            ax1.bar(df_plt2['시군구'], df_plt2['매출-임대료'], color=colors, alpha=0.7, width=0.2, label='매출-임대료')
            ax1.axhline(df_sales['매출-임대료'].mean(),label='Mean', c='r', ls=':')

            ax1.set_xlabel('시군구')
            ax1.set_ylabel('매출-임대료 (원)')
            ax1.tick_params(axis='both', direction='in')

            ax2 = ax1.twinx()
            ax2.plot(df_plt2['시군구'], df_plt2['평균 객단가'], '-s', color='white', markersize=4, linewidth=2, alpha=0.7, label='객단가')
                # ax2.set_ylim(7000, 11000)
            ax2.set_ylabel('객단가 (원/인)')
            ax2.tick_params(axis='y', direction='in')

            ax1.set_zorder(ax2.get_zorder() - 10)
            ax1.patch.set_visible(False)

            ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2))
            ax2.legend(loc='upper center', bbox_to_anchor=(0.85, -0.2))

            st.pyplot(fig)
                
    with row2_2:
        tab1, tab2, tab3 = st.tabs(['분기별 매출', '요일별 매출' , '시간대별 매출'])
        
        with tab1:
            df_quarter = df_several[['서울_전체_매출_1분기', '서울_전체_매출_2분기', '서울_전체_매출_3분기', '서울_전체_매출_4분기']]
            df_quarter.columns = ['1분기', '2분기', '3분기','4분기']
            df_quarter = df_quarter.T
            df_quarter.columns = ['서울 전체 분기별 매출']
#             plt.rcParams['figure.figsize'] = (10, 4)
            plt.style.use('dark_background')
            colors = sns.color_palette('Blues_r', len(df_plt1.index))
            fig, ax = plt.subplots() ## Figure 생성 
            # fig.set_facecolor('white') ## Figure 배경색 지정
            
#             colors = sns.color_palette('Blues_r', len(df_quarter['서울 전체 분기별 매출'])) ## 바 차트 색상
 
            ax.bar(df_quarter.index, df_quarter['서울 전체 분기별 매출'], color=colors,  width=0.2) ## 바차트 출력
            ax.plot(df_quarter.index, df_quarter['서울 전체 분기별 매출'], color='white', linestyle='--', marker='o') ## 선 그래프 출력
                        
            st.pyplot(fig)
            
        with tab2:
            df_day = df_several[['월_매출합', '화_매출합', '수_매출합', '목_매출합', '금_매출합', '토_매출합', '일_매출합']]
            df_day.columns = list('월화수목금토일')
            df_day.index = ['매출']
            df_day = df_day.T
            
            plt.style.use('dark_background')
            colors = sns.color_palette('Blues_r', len(df_day.index))
            
            fig, ax = plt.subplots()
            ax.bar(df_day.index, df_day['매출'], color=colors,  width=0.3) ## 바차트 출력
            ax.plot(df_day.index,  df_day['매출'], color='white', linestyle='--', marker='o') ## 선 그래프 출력

            st.pyplot(fig)
        
        with tab3:
            df_hour = df_several[['00~06_매출합', '06~11_매출합', '11~14_매출합', '14~17_매출합', '17~21_매출합', '21~24_매출합']]
            df_hour.columns = ['00~06', '06~11', '11~14', '14~17', '17~21', '21~24']
            df_hour.index = ['매출']
            df_hour = df_hour.T
            
            plt.style.use('dark_background')
            colors = sns.color_palette('Blues_r', len(df_hour.index)) 
            
            fig, ax = plt.subplots()
            ax.bar(df_hour.index, df_hour['매출'], color=colors,  width=0.3) ## 바차트 출력
            ax.plot(df_hour.index,  df_hour['매출'], color='white', linestyle='--', marker='o') ## 선 그래프 출력

            st.pyplot(fig)
    
    with row2_3:
        
        df_age = df_several[['10대_매출합', '20대_매출합', '30대_매출합', '40대_매출합', '50대_매출합', '60대 이상_매출합']]
        df_age_unit_price = df_several[['10대_객단가', '20대_객단가', '30대_객단가', '40대_객단가', '50대_객단가', '60대 이상_객단가']] 
        cols = ['10대', '20대', '30대', '40대', '50대', '60대 이상']
        df_age.columns =cols
        df_age_unit_price.columns = cols
        df_age.index = ['연령대별 매출']
        df_age_unit_price.index = ['연령대별 객단가']
        df_age = df_age.T
        # df_age['연령대별 객단가'] = df_age_unit_price.T['연령대별 객단가']
        df_age['연령대별 객단가'] = df_age_unit_price.T['연령대별 객단가']

        plt.style.use('default')
        colors = sns.color_palette('Blues_r', len(df_age.index))
#         plt.rcParams['figure.figsize'] = (5, 3)
        plt.rc('font', family='NanumGothic')
        plt.style.use('dark_background')
        plt.rcParams['font.size'] = 12
        fig, ax1 = plt.subplots()

        ax1.bar(df_age.index, df_age['연령대별 매출'], color=colors, alpha=0.7, width=0.2, label='매출')

        ax1.set_xlabel('연령대')
        ax1.set_ylabel('매출 (원)')
        ax1.tick_params(axis='both', direction='in')

        ax2 = ax1.twinx()
        ax2.plot(df_age.index, df_age['연령대별 객단가'], '-s', color='white', markersize=4, linewidth=2, alpha=0.7, label='객단가')
        ax2.set_ylabel('객단가 (원/인)')
        ax2.tick_params(axis='y', direction='in')

        ax1.set_zorder(ax2.get_zorder() - 10)
        ax1.patch.set_visible(False)

        ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2))
        ax2.legend(loc='upper center', bbox_to_anchor=(0.85, -0.2))

        plt.title('연령대별 매출 추이')
        st.pyplot(fig)


# %%

# %%
