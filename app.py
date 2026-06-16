import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network


st.set_page_config(
    page_title="HW1Napob | SET50 Shareholder Network",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("set50_top5_shareholders.csv")
    df["percent_share"] = pd.to_numeric(df["percent_share"], errors="coerce")
    df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
    df["stakeholder_rank"] = pd.to_numeric(df["stakeholder_rank"], errors="coerce")
    return df


def build_network(df: pd.DataFrame) -> str:
    net = Network(height="720px", width="100%", bgcolor="#0f172a", font_color="#e5e7eb")
    net.barnes_hut(gravity=-25000, central_gravity=0.15, spring_length=160, spring_strength=0.04)

    for _, row in df.iterrows():
        company = row["company_symbol"]
        shareholder = row["stakeholder_name"]
        percent = row["percent_share"]
        rank = int(row["stakeholder_rank"])

        net.add_node(
            company,
            label=company,
            title=row["company_name_th"],
            color="#38bdf8",
            shape="dot",
            size=24,
        )
        net.add_node(
            shareholder,
            label=shareholder,
            title=f"ผู้ถือหุ้นอันดับ {rank}",
            color="#f59e0b" if not row["is_thai_nvdr"] else "#a78bfa",
            shape="dot",
            size=max(10, min(38, 10 + percent)),
        )
        net.add_edge(
            company,
            shareholder,
            value=max(1, percent),
            title=f"{company} -> {shareholder}: {percent:.2f}%",
            color="#94a3b8",
        )

    return net.generate_html(notebook=False)


df = load_data()

st.title("SET50 Top 5 Shareholders Network")
st.caption("HW1Napob | Data from SET major shareholder pages")

left, right = st.columns([1, 3])

with left:
    st.subheader("Filters")
    companies = sorted(df["company_symbol"].unique())
    selected_companies = st.multiselect(
        "เลือกบริษัท",
        companies,
        default=companies[:10],
        help="เลือกน้อยลงถ้าต้องการให้กราฟอ่านง่ายขึ้น",
    )
    max_rank = st.slider("อันดับผู้ถือหุ้น", 1, 5, 5)
    include_nvdr = st.checkbox("รวม Thai NVDR", value=True)

filtered = df[df["company_symbol"].isin(selected_companies)]
filtered = filtered[filtered["stakeholder_rank"] <= max_rank]
if not include_nvdr:
    filtered = filtered[~filtered["is_thai_nvdr"]]

with right:
    c1, c2, c3 = st.columns(3)
    c1.metric("Companies", filtered["company_symbol"].nunique())
    c2.metric("Stakeholders", filtered["stakeholder_name"].nunique())
    c3.metric("Relationships", len(filtered))

    if filtered.empty:
        st.warning("ไม่มีข้อมูลตาม filter ที่เลือก")
    else:
        components.html(build_network(filtered), height=760, scrolling=True)

st.subheader("Data")
st.dataframe(filtered, use_container_width=True, hide_index=True)
