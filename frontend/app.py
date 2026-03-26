"""Streamlit frontend for the thermal power plant AI copilot MVP."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.config import PLANT_CONFIG  # noqa: E402
from backend.services.pipeline import PlantMonitoringSystem  # noqa: E402
from backend.services.reference_data import ReferenceDataRepository  # noqa: E402


st.set_page_config(
    page_title="Thermal Plant AI Copilot",
    layout="wide",
    initial_sidebar_state="expanded",
)


def format_mode(mode: str) -> str:
    return mode.replace("_", " ").title()


def build_operator_brief(result) -> str:
    values = result.snapshot.values
    if result.detection.severity == "critical":
        return (
            f"Critical plant condition detected in {format_mode(result.snapshot.anomaly_mode)} mode. "
            f"Superheater temperature is {values.get('SH_TEMP', 0):.1f} degC and drum level is "
            f"{values.get('DRUM_LEVEL', 0):.1f} mm. Follow the approved safe actions immediately."
        )
    if result.detection.severity == "warning":
        key_issue = result.detection.anomalies[0] if result.detection.anomalies else "an abnormal operating trend"
        return (
            f"Attention required: {key_issue}. "
            f"The unit is still operating, but corrective action should be taken to stabilize temperature, "
            f"pressure, feedwater, and combustion conditions."
        )
    return (
        "Plant auxiliaries are operating within the expected safe range. "
        "No immediate intervention is required beyond routine monitoring."
    )


def build_action_summary(result) -> list[str]:
    control_state = result.snapshot.control_state
    items: list[str] = []
    coal_feed = control_state.get("COAL_FEED_CMD", 0.0)
    spray = control_state.get("SH_SPRAY_WATER_CMD", 0.0)
    feedwater = control_state.get("FEEDWATER_CV_CMD", 0.0)
    recirc = control_state.get("BFP_RECIRC_VALVE_CMD", 0.0)
    trip = control_state.get("MASTER_FUEL_TRIP", 0.0)

    if trip >= 1.0:
        items.append("Fuel trip protection is active and fuel demand has been forced to a safe state.")
    elif coal_feed <= 5.0:
        items.append("Fuel demand is fully blocked to protect the boiler from unsafe thermal conditions.")
    else:
        items.append(f"Fuel demand is being held near {coal_feed:.0f}% of current command.")

    items.append(f"Superheater spray-water demand is around {spray:.0f}% to control outlet temperature.")
    items.append(f"Feedwater control valve demand is around {feedwater:.0f}% to maintain drum inventory.")
    items.append(f"Boiler feed pump recirculation demand is around {recirc:.0f}% to protect pump operation.")
    return items


def build_data_health_summary(result) -> list[str]:
    source = result.snapshot.source_records
    quality = source.get("scada_quality", "GOOD").title()
    alarm_state = source.get("dcs_alarm_state", "NORMAL").title()
    plc_state = source.get("plc_packet", "GOOD").title()
    return [
        f"SCADA data quality is reported as {quality}.",
        f"Control system alarm state is {alarm_state}.",
        f"PLC communication health is reported as {plc_state}.",
    ]


def bootstrap_system() -> PlantMonitoringSystem:
    system = PlantMonitoringSystem()
    system.warmup(40)
    return system


@st.cache_resource
def get_system() -> PlantMonitoringSystem:
    return bootstrap_system()


def run_realtime_cycle(system: PlantMonitoringSystem) -> None:
    result = system.run_cycle()
    history = system.history()
    reference_repo = ReferenceDataRepository()

    records = []
    for snapshot in history:
        record = {"timestamp": snapshot.timestamp, **snapshot.values}
        records.append(record)
    df = pd.DataFrame(records)

    st.title("Mechanical Advantage - Thermal Plant AI Copilot")

    with st.sidebar:
        st.subheader("Run Controls")
        auto_refresh = st.checkbox("Auto refresh", value=False)
        refresh_seconds = st.slider("Refresh interval (s)", min_value=1, max_value=10, value=2)
        st.write(f"Audit log: `{system.audit_logger.path}`")
        llm_status_text = "Connected" if result.llm_status.startswith("ollama:") else "Standard AI summary"
        st.write(f"AI summary mode: `{llm_status_text}`")

    kpi_cols = st.columns(4)
    kpi_cols[0].metric("Severity", result.detection.severity.upper())
    kpi_cols[1].metric("Fault Probability", f"{result.detection.fault_probability:.0%}")
    kpi_cols[2].metric("Anomalies", len(result.detection.anomalies))
    kpi_cols[3].metric("Plant Mode", format_mode(result.snapshot.anomaly_mode))

    metric_cols = st.columns(3)
    tag_names = list(PLANT_CONFIG.tags.keys())
    for index, tag in enumerate(tag_names):
        col = metric_cols[index % 3]
        value = result.snapshot.values[tag]
        unit = PLANT_CONFIG.tags[tag].unit
        col.metric(tag, f"{value:.2f} {unit}")

    st.subheader("Real-Time Trends")
    chart_tags = ["SH_TEMP", "SH_PRESS", "DRUM_LEVEL", "BFP_FLOW", "FURNACE_TEMP", "FURNACE_O2"]
    plot_df = df.melt(id_vars="timestamp", value_vars=chart_tags, var_name="tag", value_name="value")
    fig = px.line(plot_df, x="timestamp", y="value", color="tag", markers=False)
    fig.update_layout(height=460, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.subheader("Engineering Diagnosis")
        st.write(result.diagnosis.summary)
        st.markdown("**Likely Causes**")
        for item in result.diagnosis.likely_causes:
            st.write(f"- {item}")
        st.markdown("**Recommended Actions**")
        for item in result.guardrail.approved_actions:
            st.write(f"- {item}")
        st.markdown("**Automatic Protective Response**")
        for item in build_action_summary(result):
            st.write(f"- {item}")

    with detail_cols[1]:
        st.subheader("Safety Guardrails")
        if result.guardrail.blocked_actions:
            st.error("Unsafe suggestions were blocked.")
            for item in result.guardrail.blocked_actions:
                st.write(f"- {item}")
        else:
            st.success("All active recommendations are guardrail-approved.")
        st.markdown("**Evidence**")
        for item in result.detection.evidence or ["No abnormal evidence in current cycle."]:
            st.write(f"- {item}")
        st.markdown("**Triggered Interlocks**")
        for item in result.detection.triggered_interlocks or ["No trip or block condition is active."]:
            st.write(f"- {item}")
        st.markdown("**Guardrail Notes**")
        for item in result.guardrail.notes:
            st.write(f"- {item}")

    source_cols = st.columns(2)
    with source_cols[0]:
        st.subheader("System Response")
        for item in build_data_health_summary(result):
            st.write(f"- {item}")
        if result.guardrail.enforced_commands:
            st.write("- Protective commands have been issued automatically to keep the unit in a safe operating state.")
        else:
            st.write("- No automatic command override is required in the current cycle.")

    with source_cols[1]:
        st.subheader("AI Operator Note")
        st.write(build_operator_brief(result))
        if result.llm_status.startswith("ollama:") and result.llm_summary:
            st.caption("Additional AI explanation")
            st.write(result.llm_summary)

    st.subheader("Latest Telemetry Table")
    st.dataframe(df.tail(12), use_container_width=True)

    scada_rows = reference_repo.load_table("sample_scada.csv")
    plc_rows = reference_repo.load_table("sample_plc_events.csv")
    dcs_rows = reference_repo.load_table("sample_dcs_alarms.csv")
    table_cols = st.columns(3)
    with table_cols[0]:
        st.subheader("Sample SCADA Data")
        st.dataframe(pd.DataFrame(scada_rows).head(6), use_container_width=True)
    with table_cols[1]:
        st.subheader("Sample PLC Events")
        st.dataframe(pd.DataFrame(plc_rows).head(6), use_container_width=True)
    with table_cols[2]:
        st.subheader("Sample DCS Alarms")
        st.dataframe(pd.DataFrame(dcs_rows).head(6), use_container_width=True)

    if auto_refresh:
        time.sleep(refresh_seconds)
        st.rerun()


def main() -> None:
    system = get_system()
    run_realtime_cycle(system)


if __name__ == "__main__":
    main()
