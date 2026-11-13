"""Streamlit 대시보드 (P5, 뼈대).

실험 폴더를 골라 경보 목록·탐지기별 집계·호스트 구성을 보여줍니다.
데이터 로딩은 load.py(순수 함수)에 있고, 여기서는 화면만 그립니다.

실행 (대시보드 전용 venv에서):
    ~/.venvs/dash/bin/streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.load import alert_rows, list_runs, summarize  # noqa: E402


def main() -> None:
    st.set_page_config(page_title="LAN 공격 탐지 대시보드", page_icon="🛡️",
                       layout="wide")
    st.title("🛡️ LAN 공격 탐지 대시보드")

    runs = list_runs()
    if not runs:
        st.warning("data/runs 에 실험 결과가 없습니다. 먼저 env/run.py 를 실행하세요.")
        return

    names = [d.name for d in runs]
    choice = st.sidebar.selectbox("실험 선택", names)
    run_dir = next(d for d in runs if d.name == choice)
    s = summarize(run_dir)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("시나리오", s["scenario"])
    c2.metric("공격", ", ".join(s["attacks"]) or "-")
    c3.metric("경보 수", s["n_alerts"])
    c4.metric("차단 수", s["n_actions"])

    st.subheader("탐지기별 경보 수")
    if s["by_detector"]:
        st.bar_chart(s["by_detector"])
    else:
        st.info("아직 경보가 없습니다.")

    st.subheader("경보 목록")
    rows = alert_rows(run_dir)
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("경보 없음 (정상이거나 탐지기를 아직 안 돌림).")

    with st.expander("호스트 구성"):
        st.dataframe(s["hosts"], use_container_width=True)


if __name__ == "__main__":
    main()
