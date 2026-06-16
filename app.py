import csv
import html
import math
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="HW1Napob | SET50 Shareholder Network",
    layout="wide",
)


@st.cache_data
def load_rows():
    rows = []
    with Path("set50_top5_shareholders.csv").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            row["stakeholder_rank"] = int(row["stakeholder_rank"])
            row["percent_share"] = float(row["percent_share"])
            row["shares"] = int(float(row["shares"]))
            row["is_thai_nvdr"] = row["is_thai_nvdr"].lower() == "true"
            rows.append(row)
    return rows


def make_svg(rows):
    width = 1100
    height = 760
    cx = width / 2
    cy = height / 2

    companies = sorted({row["company_symbol"] for row in rows})
    stakeholders = sorted({row["stakeholder_name"] for row in rows})
    company_positions = {}
    stakeholder_positions = {}

    for i, company in enumerate(companies):
        angle = 2 * math.pi * i / max(1, len(companies))
        company_positions[company] = (cx + 260 * math.cos(angle), cy + 260 * math.sin(angle))

    for i, stakeholder in enumerate(stakeholders):
        angle = 2 * math.pi * i / max(1, len(stakeholders))
        stakeholder_positions[stakeholder] = (cx + 360 * math.cos(angle), cy + 360 * math.sin(angle))

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="#0f172a" rx="18"/>',
        '<style>text{font-family:Arial,sans-serif;font-size:11px;fill:#e5e7eb}.small{font-size:9px;fill:#cbd5e1}</style>',
    ]

    for row in rows:
        x1, y1 = company_positions[row["company_symbol"]]
        x2, y2 = stakeholder_positions[row["stakeholder_name"]]
        stroke_width = max(1, min(8, row["percent_share"] / 8))
        title = html.escape(f'{row["company_symbol"]} -> {row["stakeholder_name"]}: {row["percent_share"]:.2f}%')
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#64748b" stroke-opacity="0.45" stroke-width="{stroke_width:.1f}"><title>{title}</title></line>'
        )

    for company, (x, y) in company_positions.items():
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="#38bdf8"/>')
        parts.append(f'<text x="{x + 18:.1f}" y="{y + 4:.1f}">{html.escape(company)}</text>')

    for stakeholder, (x, y) in stakeholder_positions.items():
        related = [row for row in rows if row["stakeholder_name"] == stakeholder]
        total_percent = sum(row["percent_share"] for row in related)
        is_nvdr = any(row["is_thai_nvdr"] for row in related)
        radius = max(6, min(20, 6 + total_percent / 8))
        color = "#a78bfa" if is_nvdr else "#f59e0b"
        label = stakeholder if len(stakeholder) <= 34 else stakeholder[:31] + "..."
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}"/>')
        parts.append(f'<text class="small" x="{x + radius + 4:.1f}" y="{y + 3:.1f}">{html.escape(label)}</text>')

    parts.append('</svg>')
    return "".join(parts)


rows = load_rows()
companies = sorted({row["company_symbol"] for row in rows})

st.title("SET50 Top 5 Shareholders Network")
st.caption("HW1Napob | Data from SET major shareholder pages")

left, right = st.columns([1, 3])

with left:
    st.subheader("Filters")
    selected_companies = st.multiselect("เลือกบริษัท", companies, default=companies[:10])
    max_rank = st.slider("อันดับผู้ถือหุ้น", 1, 5, 5)
    include_nvdr = st.checkbox("รวม Thai NVDR", value=True)

filtered = [
    row
    for row in rows
    if row["company_symbol"] in selected_companies
    and row["stakeholder_rank"] <= max_rank
    and (include_nvdr or not row["is_thai_nvdr"])
]

with right:
    col1, col2, col3 = st.columns(3)
    col1.metric("Companies", len({row["company_symbol"] for row in filtered}))
    col2.metric("Stakeholders", len({row["stakeholder_name"] for row in filtered}))
    col3.metric("Relationships", len(filtered))

    if filtered:
        components.html(make_svg(filtered), height=780, scrolling=True)
    else:
        st.warning("ไม่มีข้อมูลตาม filter ที่เลือก")

st.subheader("Data")
st.dataframe(filtered, use_container_width=True, hide_index=True)
