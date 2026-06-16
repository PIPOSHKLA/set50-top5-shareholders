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
        '<div id="network-wrap">',
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="#0f172a" rx="18"/>',
        """
        <style>
        text{font-family:Arial,sans-serif;font-size:11px;fill:#e5e7eb;pointer-events:none}
        .small{font-size:9px;fill:#cbd5e1;opacity:.7}
        .node{cursor:pointer;transition:opacity .15s ease,transform .15s ease}
        .node circle{stroke:#e5e7eb;stroke-width:0;transition:stroke-width .15s ease,filter .15s ease}
        .edge{transition:opacity .15s ease,stroke .15s ease,stroke-width .15s ease;pointer-events:stroke}
        .dim{opacity:.12}
        .focus circle{stroke-width:3;filter:drop-shadow(0 0 7px #f8fafc)}
        .focus text{font-weight:700;opacity:1}
        .active-edge{stroke:#f8fafc;stroke-opacity:.95!important;stroke-width:5!important}
        </style>
        """,
    ]

    for row in rows:
        company = row["company_symbol"]
        stakeholder = row["stakeholder_name"]
        x1, y1 = company_positions[row["company_symbol"]]
        x2, y2 = stakeholder_positions[row["stakeholder_name"]]
        stroke_width = max(1, min(8, row["percent_share"] / 8))
        title = html.escape(f'{row["company_symbol"]} -> {row["stakeholder_name"]}: {row["percent_share"]:.2f}%')
        source = html.escape(company, quote=True)
        target = html.escape(stakeholder, quote=True)
        parts.append(
            f'<line class="edge" data-source="{source}" data-target="{target}" '
            f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#64748b" stroke-opacity="0.45" stroke-width="{stroke_width:.1f}"><title>{title}</title></line>'
        )

    for company, (x, y) in company_positions.items():
        node = html.escape(company, quote=True)
        label = html.escape(company)
        parts.append(f'<g class="node company" data-node="{node}">')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="#38bdf8"/>')
        parts.append(f'<text x="{x + 18:.1f}" y="{y + 4:.1f}">{label}</text>')
        parts.append('</g>')

    for stakeholder, (x, y) in stakeholder_positions.items():
        related = [row for row in rows if row["stakeholder_name"] == stakeholder]
        total_percent = sum(row["percent_share"] for row in related)
        is_nvdr = any(row["is_thai_nvdr"] for row in related)
        radius = max(6, min(20, 6 + total_percent / 8))
        color = "#a78bfa" if is_nvdr else "#f59e0b"
        label = stakeholder if len(stakeholder) <= 34 else stakeholder[:31] + "..."
        node = html.escape(stakeholder, quote=True)
        title = html.escape(stakeholder)
        parts.append(f'<g class="node stakeholder" data-node="{node}">')
        parts.append(f'<title>{title}</title>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}"/>')
        parts.append(f'<text class="small" x="{x + radius + 4:.1f}" y="{y + 3:.1f}">{html.escape(label)}</text>')
        parts.append('</g>')

    parts.append('</svg>')
    parts.append(
        """
        <script>
        const root = document.currentScript.parentElement;
        const nodes = [...root.querySelectorAll('.node')];
        const edges = [...root.querySelectorAll('.edge')];
        let lockedNode = null;

        function clearHighlight() {
          nodes.forEach(node => node.classList.remove('dim', 'focus'));
          edges.forEach(edge => edge.classList.remove('dim', 'active-edge'));
        }

        function highlight(name) {
          const related = new Set([name]);
          edges.forEach(edge => {
            if (edge.dataset.source === name || edge.dataset.target === name) {
              related.add(edge.dataset.source);
              related.add(edge.dataset.target);
              edge.classList.add('active-edge');
              edge.classList.remove('dim');
            } else {
              edge.classList.remove('active-edge');
              edge.classList.add('dim');
            }
          });
          nodes.forEach(node => {
            if (related.has(node.dataset.node)) {
              node.classList.add('focus');
              node.classList.remove('dim');
            } else {
              node.classList.remove('focus');
              node.classList.add('dim');
            }
          });
        }

        nodes.forEach(node => {
          node.addEventListener('mouseenter', () => {
            if (!lockedNode) highlight(node.dataset.node);
          });
          node.addEventListener('mouseleave', () => {
            if (!lockedNode) clearHighlight();
          });
          node.addEventListener('click', () => {
            lockedNode = lockedNode === node.dataset.node ? null : node.dataset.node;
            lockedNode ? highlight(lockedNode) : clearHighlight();
          });
        });
        root.addEventListener('dblclick', () => {
          lockedNode = null;
          clearHighlight();
        });
        </script>
        </div>
        """
    )
    return "".join(parts)


rows = load_rows()
companies = sorted({row["company_symbol"] for row in rows})

st.title("SET50 Top 5 Shareholders Network")
st.caption("HW1Napob | Data from SET major shareholder pages")

left, right = st.columns([1, 3])

with left:
    st.subheader("Filters")
    show_all_companies = st.checkbox("แสดงครบทั้ง SET50", value=True)
    default_companies = companies if show_all_companies else companies[:10]
    selected_companies = st.multiselect("เลือกบริษัท", companies, default=default_companies)
    max_rank = st.slider("อันดับผู้ถือหุ้น", 1, 5, 5)

filtered = [
    row
    for row in rows
    if row["company_symbol"] in selected_companies
    and row["stakeholder_rank"] <= max_rank
]

with right:
    col1, col2, col3 = st.columns(3)
    col1.metric("Companies", len({row["company_symbol"] for row in filtered}))
    col2.metric("Stakeholders", len({row["stakeholder_name"] for row in filtered}))
    col3.metric("Relationships", len(filtered))

    expected_relationships = len(selected_companies) * max_rank
    if len(filtered) == expected_relationships:
        st.success(f"ข้อมูลครบ: {len(selected_companies)} บริษัท x {max_rank} ผู้ถือหุ้น = {len(filtered)} ความสัมพันธ์")
    else:
        st.warning(f"ข้อมูลที่แสดงมี {len(filtered)} จากที่คาด {expected_relationships} ความสัมพันธ์")

    if filtered:
        components.html(make_svg(filtered), height=780, scrolling=True)
    else:
        st.warning("ไม่มีข้อมูลตาม filter ที่เลือก")

st.subheader("Data")
st.dataframe(filtered, use_container_width=True, hide_index=True)

with st.expander("ตรวจจำนวนผู้ถือหุ้นต่อบริษัท"):
    counts = []
    for company in companies:
        company_rows = [row for row in rows if row["company_symbol"] == company]
        counts.append(
            {
                "company_symbol": company,
                "holder_count": len(company_rows),
                "status": "ครบ 5" if len(company_rows) == 5 else "ไม่ครบ",
            }
        )
    st.dataframe(counts, use_container_width=True, hide_index=True)
