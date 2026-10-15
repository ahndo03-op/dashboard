import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 1. 페이지 기본 설정 및 디자인 (따뜻한 톤 레이아웃)
st.set_page_config(
    page_title="우리 동네 인구 피라미드", page_icon="👨‍👩‍👧‍👦", layout="centered"
)

# 따뜻하고 정감 있는 스타일 적용
st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption("우리 동네의 최신 연도 연령별 남녀 인구 구성을 한눈에 확인해 보세요.")


# 2. 데이터 불러오기 함수 (캐싱을 적용해 매번 다시 다운로드하지 않도록 함)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/ahndo03-op/dashboard/main/population_ts_yearly_gender.zip"
    # zip 압축 파일이라도 pandas가 자동으로 해제하여 읽어옵니다.
    df = pd.read_csv(url)

    # 가장 최신 연도 데이터만 추출
    max_year = df["연도"].max()
    latest_df = df[df["연도"] == max_year].copy()

    return latest_df, max_year


# 데이터 로딩 표시
with st.spinner("데이터를 불러오는 중입니다..."):
    df, latest_year = load_data()

st.info(f"💡 현재 조회 대상 연도: **{latest_year}년**")


# 3. 시도 -> 시군구 -> 동 선택 드롭다운 (상단배치)
st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

with col1:
    # 시도 목록 추출 및 선택
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("시·도", sido_list)

with col2:
    # 선택된 시도에 해당하는 시군구 목록 추출 및 선택
    filtered_sigungu_df = df[df["시도"] == selected_sido]
    sigungu_list = sorted(filtered_sigungu_df["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("시·군·구", sigungu_list)

with col3:
    # 선택된 시군구에 해당하는 동 목록 추출 및 선택
    filtered_dong_df = filtered_sigungu_df[
        filtered_sigungu_df["시군구"] == selected_sigungu
    ]
    dong_list = sorted(filtered_dong_df["동"].dropna().unique())
    selected_dong = st.selectbox("읍·면·동", dong_list)


# 4. 선택한 지역의 1개 행 추출 및 데이터 정리
target_row = filtered_dong_df[filtered_dong_df["동"] == selected_dong].iloc[0]

# 나이 라벨 순서 정의 (0세부터 100세 이상까지)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_counts = []
female_counts = []

for age in age_labels:
    male_col = f"남_{age}"
    female_col = f"여_{age}"

    # 해당 열의 값을 가져와 추가 (데이터가 없거나 NaN일 경우 0 처리)
    male_counts.append(int(target_row.get(male_col, 0)))
    female_counts.append(int(target_row.get(female_col, 0)))


# 5. 주요 지표 계산 (총인구, 평균연령, 고령화율)
total_male = sum(male_counts)
total_female = sum(female_counts)
total_pop = total_male + total_female

# 나이별 전체 인구수 계산 (100세 이상은 100세로 계산)
pop_by_age = [m + f for m, f in zip(male_counts, female_counts)]

if total_pop > 0:
    # 평균연령 = sum(나이 * 인구수) / 총인구
    weighted_age_sum = sum(
        age * count for age, count in enumerate(pop_by_age[:100])
    ) + (100 * pop_by_age[100])
    avg_age = weighted_age_sum / total_pop

    # 고령화율 (65세 이상 비율, %) = 65세 이상 인구 / 총인구 * 100
    elderly_pop = sum(pop_by_age[65:])
    aging_rate = (elderly_pop / total_pop) * 100

    # 유소년 인구 (15세 미만 비율, %)
    child_pop = sum(pop_by_age[:15])
    child_rate = (child_pop / total_pop) * 100
else:
    avg_age = 0.0
    aging_rate = 0.0
    child_rate = 0.0


# 6. 그래프 상단 지표 카드 3개 배치
st.markdown("---")
m1, m2, m3 = st.columns(3)

m1.metric("총인구", f"{total_pop:,} 명")
m2.metric("평균 연령", f"{avg_age:.1f} 세")

# 고령화율 20% 이상 시 🚨 주의 표시 추가
if aging_rate >= 20.0:
    m3.metric(
        "고령화율 (65세+)", f"{aging_rate:.1f}%", delta="🚨 초고령사회 (20% 이상)"
    )
else:
    m3.metric("고령화율 (65세+)", f"{aging_rate:.1f}%")


# 7. Plotly 인구 피라미드 그래프 생성
# 남자는 왼쪽(음수 값), 여자는 오른쪽(양수 값)
male_negative_counts = [-val for val in male_counts]

fig = go.Figure()

# 남자 막대 그래프 (왼쪽, 포근한 파란색 계열)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_negative_counts,
        name="남자",
        orientation="h",
        marker=dict(color="#4c82c3"),
        customdata=male_counts,
        hovertemplate="%{y} 남자: %{customdata:,}명<extra></extra>",
    )
)

# 여자 막대 그래프 (오른쪽, 따뜻한 코랄/분홍색 계열)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_counts,
        name="여자",
        orientation="h",
        marker=dict(color="#e27085"),
        hovertemplate="%{y} 여자: %{x:,}명<extra></extra>",
    )
)


# 8. 레이아웃 설정 및 세로축 순서 고정
fig.update_layout(
    title=dict(
        text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}] 인구 피라미드</b>",
        x=0.5,
        xanchor="center",
        font=dict(size=18),
    ),
    barmode="overlay",
    bargap=0.1,
    xaxis=dict(
        title="인구수 (명)",
        tickmode="array",
        tickformat=",d",
        hoverformat=",d",
    ),
    yaxis=dict(
        title="연령",
        type="category",
        categoryorder="array",
        categoryarray=age_labels,
    ),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
    ),
    height=800,
    paper_bgcolor="#fffdf9",
    plot_bgcolor="#fffdf9",
)

# x축의 음수 값을 양수 형태의 눈금 라벨로 조정
max_val = max(max(male_counts), max(female_counts)) if total_pop > 0 else 1
ticks = list(range(0, max_val + 1, max(1, max_val // 4)))
tick_vals = [-t for t in reversed(ticks[1:])] + ticks
tick_texts = [f"{abs(t):,}" for t in tick_vals]

fig.update_xaxes(tickvals=tick_vals, ticktext=tick_texts)


# 9. 스트림릿 화면에 그래프 출력
st.plotly_chart(fig, use_container_width=True)


# 10. 피라미드 아래 한 줄 설명 자동 생성
st.subheader("💡 동네 인구 특성 한 줄 요약")

if aging_rate >= 20.0:
    st.warning(
        f"👴 **어르신들이 많은 동네입니다.** (65세 이상 고령인구 비율이 **{aging_rate:.1f}%**로 높습니다.)"
    )
elif child_rate > aging_rate:
    st.success(
        f"👶 **아이들이 상대적으로 많은 활기찬 동네입니다.** (15세 미만 유소년 비율 **{child_rate:.1f}%** > 고령인구 비율 **{aging_rate:.1f}%**)"
    )
else:
    st.info(
        f"⚖️ **아이와 어르신 비율이 균형을 이루거나 청장년층 중심의 동네입니다.** (고령화율 **{aging_rate:.1f}%**, 유소년 비율 **{child_rate:.1f}%**)"
    )
