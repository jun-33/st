
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="ESS 충전량과 방전량",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 ESS 날짜별 충전량과 방전량")
st.write("2024년부터 2025년까지의 ESS 일단위 충전 및 방전 실적을 확인합니다.")


# =========================================================
# CSV 파일 경로 설정
# =========================================================

file_2024 = "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2024.csv"
file_2025 = "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2025.csv"

base_dir = Path(__file__).resolve().parent

# main.py가 code 폴더 안에 있거나 저장소 최상위에 있는 경우 모두 지원
possible_dirs = [
    base_dir / "data",
    base_dir.parent / "data",
    base_dir
]

def find_file(filename):
    for folder in possible_dirs:
        path = folder / filename
        if path.exists():
            return path

    return None


path_2024 = find_file(file_2024)
path_2025 = find_file(file_2025)


# =========================================================
# 데이터 불러오기
# =========================================================

if path_2024 is None or path_2025 is None:
    st.error("CSV 파일을 찾을 수 없습니다. data 폴더와 파일 이름을 확인해 주세요.")
    st.stop()

try:
    df_2024 = pd.read_csv(path_2024, encoding="utf-8-sig")
    df_2025 = pd.read_csv(path_2025, encoding="utf-8-sig")

    # 두 연도 데이터 합치기
    df = pd.concat(
        [df_2024, df_2025],
        ignore_index=True
    )

except Exception as e:
    st.error(f"CSV 파일을 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# =========================================================
# 데이터 전처리
# =========================================================

required_columns = [
    "거래일",
    "충전량 합계(kWh)",
    "방전량 합계(kWh)"
]

for column in required_columns:
    if column not in df.columns:
        st.error(f"필요한 열을 찾을 수 없습니다: {column}")
        st.stop()

# 날짜와 숫자 자료형으로 변환
df["거래일"] = pd.to_datetime(
    df["거래일"],
    errors="coerce"
)

df["충전량 합계(kWh)"] = pd.to_numeric(
    df["충전량 합계(kWh)"],
    errors="coerce"
)

df["방전량 합계(kWh)"] = pd.to_numeric(
    df["방전량 합계(kWh)"],
    errors="coerce"
)


# =========================================================
# 데이터 개요
# =========================================================

st.subheader("📊 데이터 개요")

st.write(
    "2024년과 2025년의 CSV 데이터를 합친 원본 데이터의 "
    "행 수, 열 수, 자료형, 결측치 개수입니다."
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="전체 행 수",
        value=f"{df.shape[0]:,}개"
    )

with col2:
    st.metric(
        label="전체 열 수",
        value=f"{df.shape[1]:,}개"
    )

# 열별 자료형과 결측치 개수
overview = pd.DataFrame({
    "열 이름": df.columns,
    "자료형": [
        str(df[column].dtype)
        for column in df.columns
    ],
    "빈 값 개수": [
        int(df[column].isna().sum())
        for column in df.columns
    ]
})

st.dataframe(
    overview,
    use_container_width=True,
    hide_index=True
)

st.divider()


# =========================================================
# 날짜별 충전량과 방전량 계산
# =========================================================

# 날짜별로 지역 등의 데이터를 합산
daily_df = (
    df.dropna(subset=["거래일"])
    .groupby("거래일", as_index=False)[
        ["충전량 합계(kWh)", "방전량 합계(kWh)"]
    ]
    .sum(min_count=1)
)

daily_df = daily_df.sort_values("거래일")


# =========================================================
# 날짜별 충전량과 방전량 그래프
# =========================================================

st.subheader("📈 2024~2025년 ESS 날짜별 충전량과 방전량")

fig = go.Figure()

# 충전량
fig.add_trace(
    go.Scatter(
        x=daily_df["거래일"],
        y=daily_df["충전량 합계(kWh)"],
        mode="lines",
        name="충전량",
        line=dict(color="#636EFA", width=2),
        hovertemplate=
        "날짜: %{x|%Y-%m-%d}<br>" +
        "충전량: %{y:,.0f} kWh<extra></extra>"
    )
)

# 방전량
fig.add_trace(
    go.Scatter(
        x=daily_df["거래일"],
        y=daily_df["방전량 합계(kWh)"],
        mode="lines",
        name="방전량",
        line=dict(color="#FF4B4B", width=2),
        hovertemplate=
        "날짜: %{x|%Y-%m-%d}<br>" +
        "방전량: %{y:,.0f} kWh<extra></extra>"
    )
)

fig.update_layout(
    xaxis_title="거래일",
    yaxis_title="전력량(kWh)",
    hovermode="x unified",
    legend_title="구분",
    height=500,
    template="plotly_white"
)

fig.update_yaxes(
    tickformat=".2s"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================================================
# 데이터 확인
# =========================================================

with st.expander("📋 날짜별 충전량과 방전량 데이터 확인"):
    st.dataframe(
        daily_df,
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "자료 출처: 지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적"
)
