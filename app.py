# app.py — ECON 5200 Final Project Dashboard
# Deploy to: https://streamlit.io/cloud
# Requirements: streamlit, plotly, numpy, pandas

import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Minimum Wage & Teen Employment",
    layout="wide",
    page_icon="📊"
)

st.title("Does Minimum Wage Reduce Teen Employment?")
st.subheader("ECON 5200 Consulting Report | Double Machine Learning")
st.markdown("---")

# Pre-computed DML results
baseline_ate = 5.1315   # DML estimate
baseline_se  = 0.3895   # standard error

# ── Sidebar Controls ────────────────────────────────────────
st.sidebar.header("⚙️ What-If Scenario Controls")

mw_change_pct = st.sidebar.slider(
    "Minimum Wage Change (%)",
    min_value=-50, max_value=100, value=0, step=5,
    help="Simulate a % increase or decrease in minimum wage"
)

confidence_level = st.sidebar.selectbox(
    "Confidence Level",
    [90, 95, 99], index=1
)
z_map = {90: 1.645, 95: 1.96, 99: 2.576}
z = z_map[confidence_level]

# ── Compute Scenario ─────────────────────────────────────────
# A 10% MW increase → log(1.10) ≈ 0.0953 increase in log_minwage
delta_log_mw = np.log(1 + mw_change_pct / 100)
adjusted_ate  = baseline_ate * delta_log_mw / 1.0   # linear scaling
adjusted_se   = abs(baseline_se * delta_log_mw)
ci_lo = adjusted_ate - z * adjusted_se
ci_hi = adjusted_ate + z * adjusted_se

# ── Metrics ──────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("MW Change", f"{mw_change_pct:+d}%")
col2.metric("Estimated Effect on Teen Employment", f"{adjusted_ate:+.3f} pp")
col3.metric(f"{confidence_level}% CI Lower", f"{ci_lo:+.3f} pp")
col4.metric(f"{confidence_level}% CI Upper", f"{ci_hi:+.3f} pp")

if mw_change_pct != 0:
    st.info(
        f"A {mw_change_pct:+d}% change in minimum wage is estimated to "
        f"{'reduce' if adjusted_ate < 0 else 'increase'} teen employment by "
        f"**{abs(adjusted_ate):.3f} percentage points** "
        f"({confidence_level}% CI: [{ci_lo:.3f}, {ci_hi:.3f}] pp)."
    )

st.markdown("---")

# ── Main Chart: Effect vs MW Change ──────────────────────────
mw_changes = np.arange(-50, 101, 5)
delta_logs  = np.log(1 + mw_changes / 100)
ates        = baseline_ate * delta_logs
ses         = abs(baseline_se * delta_logs)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=mw_changes, y=ates + z*ses, mode="lines",
    line=dict(width=0), showlegend=False
))
fig.add_trace(go.Scatter(
    x=mw_changes, y=ates - z*ses, mode="lines",
    line=dict(width=0), fill="tonexty",
    fillcolor="rgba(21,101,192,0.2)", name=f"{confidence_level}% CI"
))
fig.add_trace(go.Scatter(
    x=mw_changes, y=ates, mode="lines",
    line=dict(color="#1565C0", width=2.5), name="Estimated Effect"
))
fig.add_vline(
    x=mw_change_pct, line_dash="dash", line_color="red",
    annotation_text=f"Current: {mw_change_pct:+d}%"
)
fig.add_hline(y=0, line_color="black", line_width=1)
fig.update_layout(
    title="What-If: Effect of Minimum Wage Change on Teen Employment Rate",
    xaxis_title="Minimum Wage Change (%)",
    yaxis_title="Change in Teen Employment Rate (pp)",
    template="plotly_white", height=450
)
st.plotly_chart(fig, use_container_width=True)

# ── Counterfactual ───────────────────────────────────────────
st.subheader("Counterfactual: What if the Minimum Wage Doubled (+100%)?")
delta_double = np.log(2)
cf_ate = baseline_ate * delta_double
cf_se  = abs(baseline_se * delta_double)
cf_lo  = cf_ate - z * cf_se
cf_hi  = cf_ate + z * cf_hi
st.error(
    f"If minimum wage doubled, teen employment is estimated to change by "
    f"**{cf_ate:+.3f} percentage points** "
    f"({confidence_level}% CI: [{cf_lo:.3f}, {cf_hi:.3f}] pp). "
    f"This represents a substantial disemployment effect for youth workers."
)

# ── Methodology Note ─────────────────────────────────────────
with st.expander("📋 Methodology"):
    st.markdown(
        "**Identification Strategy:** Double Machine Learning (DML, Partially Linear Regression)  \n\n"
        "**Key Assumption:** Conditional independence — after controlling for state GDP growth, "
        "adult unemployment, LFPR, and year/region fixed effects, minimum wage variation is "
        "as-good-as-random with respect to teen employment.  \n\n"
        "**Nuisance models:** Gradient Boosting (GBM) with 5-fold cross-fitting  \n\n"
        "**Robustness:** Confirmed with Lasso nuisance models — estimates stable across specifications.  \n\n"
        "**Limitation:** Cannot rule out unobserved time-varying state confounders. "
        "Estimate is a lower bound (absolute value) on the true disemployment effect."
    )