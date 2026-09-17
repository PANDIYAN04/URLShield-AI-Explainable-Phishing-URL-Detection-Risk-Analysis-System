"""Streamlit dashboard for URLShield AI."""
from __future__ import annotations

import io
import json
import time
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from explain import explain_result
from predict import analyze_url

MODEL_PATH = Path(__file__).parent / "model.pkl"
DEMO_URLS = ["https://example.com/", "http://192.168.1.10/login/verify", "http://secure-login-account-update.tk/confirm"]

st.set_page_config(page_title="URLShield AI", page_icon="🛡", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{--ink:#e9f2f1;--muted:#91aaa8;--panel:rgba(18,31,35,.84);--line:rgba(127,211,197,.18);--mint:#6fe3ca;--amber:#f4bd66;--red:#ff7183}
.stApp{background:radial-gradient(circle at 80% 0%,#183a3c 0,#0c191d 42%,#081013 100%);color:var(--ink);font-family:'Space Grotesk',sans-serif}.block-container{max-width:1320px;padding:2.5rem 3rem 4rem}h1,h2,h3{font-family:'Space Grotesk',sans-serif}.hero{border-bottom:1px solid var(--line);padding-bottom:1.6rem;margin-bottom:1.8rem}.eyebrow,.section-label{color:var(--mint);font:500 11px 'DM Mono',monospace;letter-spacing:1.7px}.hero h1{font-size:clamp(2.3rem,5vw,4.6rem);line-height:.98;margin:.45rem 0 .75rem}.sub,.small-note{color:var(--muted)}.online{float:right;color:var(--mint);font:500 12px 'DM Mono',monospace;border:1px solid #6fe3ca55;padding:.55rem .8rem;border-radius:99px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:1.15rem;box-shadow:0 15px 50px #00000029}.metric{background:#182d30bf;border:1px solid var(--line);border-radius:14px;padding:1rem;min-height:92px}.metric .label{color:var(--muted);font:11px 'DM Mono',monospace;text-transform:uppercase}.metric .value{font-size:1.22rem;font-weight:600;margin-top:.45rem}div[data-testid="stTextInput"] input{background:#102124;border:1px solid #2a5455;color:var(--ink);border-radius:10px;padding:.85rem 1rem}.stButton button{border-radius:10px;font-weight:700}.badge{display:inline-block;border-radius:99px;padding:.35rem .7rem;font:600 12px 'DM Mono',monospace}
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "result" not in st.session_state:
    st.session_state.result = None


def bundle() -> dict:
    return joblib.load(MODEL_PATH) if MODEL_PATH.exists() else {}


def card(label: str, value: str) -> None:
    st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## 🛡 URLShield AI")
    st.caption("Explainable phishing URL risk analyzer")
    page = st.radio("Workspace", ["Scanner", "Model insights", "Methodology"], label_visibility="collapsed")
    st.divider()
    st.markdown("**ENGINE STATUS**")
    st.success("AI engine online")
    st.caption("URL-only triage. No destination is contacted.")
    if st.button("Clear scan history", use_container_width=True):
        st.session_state.history = []
        st.rerun()

st.markdown('<div class="hero"><span class="online">● AI ENGINE ONLINE</span><div class="eyebrow">URLSHIELD AI / SECURITY INTELLIGENCE</div><h1>Explainable phishing<br>URL risk analyzer</h1><div class="sub">Turn opaque URL signals into a clear, defensible threat assessment.</div></div>', unsafe_allow_html=True)

if page == "Scanner":
    st.markdown('<div class="section-label">ANALYZE A URL</div>', unsafe_allow_html=True)
    choice = st.selectbox("Demo URL", ["Custom URL"] + DEMO_URLS, label_visibility="collapsed")
    with st.form("analysis_form"):
        typed_url = st.text_input("URL", value="" if choice == "Custom URL" else choice, placeholder="https://example.com/account", label_visibility="collapsed")
        submitted = st.form_submit_button("ANALYZE URL", type="primary")
    if submitted:
        try:
            progress = st.progress(0, text="Validating URL...")
            progress.progress(35, text="Extracting structural signals...")
            started = time.perf_counter()
            result = analyze_url(typed_url)
            result["elapsed_ms"] = (time.perf_counter() - started) * 1000
            progress.progress(75, text="Running model and explanation...")
            time.sleep(.12)
            progress.progress(100, text="Analysis complete")
            result["timestamp"] = datetime.now().astimezone().isoformat(timespec="seconds")
            result["explanations"] = explain_result(result)
            st.session_state.result = result
            st.session_state.history.insert(0, {"timestamp": result["timestamp"], "url": result["normalized_url"], "score": result["risk_score"], "classification": result["classification"], "confidence": result["confidence"]})
            st.session_state.history = st.session_state.history[:10]
        except FileNotFoundError as error:
            st.error(str(error))
        except ValueError as error:
            st.warning(str(error))
        except Exception:
            st.error("The URL could not be analyzed. Check its format and try again.")

    result = st.session_state.result
    if result and "phishing_probability" not in result:
        result = analyze_url(result["url"])
        st.session_state.result = result
    if result and "explanations" not in result:
        result["explanations"] = explain_result(result)
        result.setdefault("normalized_url", result["url"])
        result.setdefault("timestamp", datetime.now().astimezone().isoformat(timespec="seconds"))
        result.setdefault("elapsed_ms", 0.0)
    if result:
        features, explanations, score = result["features"], result["explanations"], result["risk_score"]
        accent = "#6fe3ca" if score <= 40 else "#f4bd66" if score <= 60 else "#ff7183"
        left, right = st.columns([1, 1.65], gap="large")
        with left:
            st.markdown('<div class="panel"><div class="section-label">AI RISK SCORE</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:3.5rem;font-weight:700;color:{accent};line-height:1">{score}<span style="font-size:1rem;color:#91aaa8"> / 100</span></div><div class="badge" style="margin-top:.8rem;color:{accent};border:1px solid {accent}55;background:{accent}22">{result["classification"]}</div>', unsafe_allow_html=True)
            gauge = go.Figure(go.Indicator(mode="gauge", value=score, gauge={"axis":{"range":[0,100],"tickcolor":"#91aaa8"},"bar":{"color":accent},"steps":[{"range":[0,40],"color":"#163c39"},{"range":[40,70],"color":"#493a25"},{"range":[70,100],"color":"#48252e"}]}))
            gauge.update_layout(height=210, margin=dict(l=15,r=15,t=10,b=5), paper_bgcolor="rgba(0,0,0,0)", font_color="#91aaa8")
            st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})
            st.caption("AI Risk Score is a model-based signal, not a guaranteed probability of maliciousness.")
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            cols = st.columns(5)
            values = [("Classification", result["classification"]), ("Confidence", f'{result["confidence"]:.0%}'), ("Phishing output", f'{result["phishing_probability"]:.0%}'), ("Features analyzed", str(len(result["feature_names"]))), ("Analysis time", f'{result["elapsed_ms"]:.1f} ms')]
            for col, item in zip(cols, values):
                with col: card(*item)
            st.markdown('<div style="height:1rem"></div><div class="panel"><div class="section-label">WHY DID THE AI MAKE THIS DECISION?</div>', unsafe_allow_html=True)
            for item in [x for x in explanations if "RISK SIGNAL" not in x["impact"]]:
                color = "#ff7183" if "HIGH" in item["impact"] else "#f4bd66"
                st.markdown(f'<div style="border-left:3px solid {color};padding:.45rem .8rem;margin:.5rem 0;background:#122226"><span style="font:10px DM Mono;color:{color}">{item["impact"]}</span><br>{item["text"]}</div>', unsafe_allow_html=True)
            safe = [x for x in explanations if "RISK SIGNAL" in x["impact"]]
            if safe:
                st.markdown('<div class="section-label" style="margin-top:1rem">POSITIVE SECURITY SIGNALS</div>', unsafe_allow_html=True)
                for item in safe: st.markdown(f'<div style="color:#6fe3ca;padding:.2rem 0">✓ {item["text"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        chart_col, intel_col = st.columns([1.15, 1], gap="large")
        with chart_col:
            st.markdown('<div class="panel"><div class="section-label">FEATURE IMPACT / LOCAL SIGNALS</div>', unsafe_allow_html=True)
            impact = [(x["text"], int(x["weight"])) for x in explanations if int(x["weight"]) > 0]
            if impact:
                labels, values = zip(*impact[:7])
                chart = go.Figure(go.Bar(x=list(values)[::-1], y=list(labels)[::-1], orientation="h", marker_color="#6fe3ca"))
                chart.update_layout(height=280, margin=dict(l=5,r=15,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#91aaa8", xaxis={"showgrid":False,"title":"relative impact"}, yaxis={"showgrid":False})
                st.plotly_chart(chart, use_container_width=True, config={"displayModeBar":False})
            else: st.info("No elevated URL signals were detected.")
            st.markdown('</div>', unsafe_allow_html=True)
        with intel_col:
            st.markdown('<div class="panel"><div class="section-label">URL INTELLIGENCE / ANATOMY</div>', unsafe_allow_html=True)
            anatomy = f'<div style="padding:.8rem;background:#102124;border:1px solid #2a5455;border-radius:10px;word-break:break-all"><span style="color:#6fe3ca">{features["protocol"]}://</span><b>{features["subdomain"] + "." if features["subdomain"] != "none" else ""}{features["domain"]}</b><span style="color:#f4bd66">{features["path"]}</span><span style="color:#91aaa8">{("?" + features["query"]) if features["query"] != "none" else ""}{("#" + features["fragment"]) if features["fragment"] != "none" else ""}</span></div>'
            st.markdown(anatomy, unsafe_allow_html=True)
            rows = [("Protocol", features["protocol"]),("Domain", features["domain"]),("Subdomain", features["subdomain"]),("TLD / Port", f'{features["tld"]} / {features["port"]}'),("Path / Query", f'{features["path"]} / {features["query"]}'),("Fragment", features["fragment"]),("URL / domain length", f'{features["url_length"]} / {features["hostname_length"]}'),("HTTPS / IP", f'{"enabled" if features["uses_https"] else "disabled"} / {"detected" if features["has_ip_address"] else "not detected"}'),("Keywords", features["suspicious_keywords"]),("Encoding / punycode", f'{"detected" if features["has_encoded_chars"] else "none"} / {"detected" if features["has_punycode"] else "none"}'),("Subdomain depth", str(features["subdomain_count"]))]
            st.dataframe(pd.DataFrame(rows, columns=["Signal", "Observed value"]), hide_index=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel"><div class="section-label">SECURITY ANALYSIS CHECKLIST</div>', unsafe_allow_html=True)
        checks = [("URL structure", features["url_length"] <= 90, f'{features["url_length"]} characters'),("HTTPS", bool(features["uses_https"]), "enabled" if features["uses_https"] else "not enabled"),("IP address", not bool(features["has_ip_address"]), "not detected" if not features["has_ip_address"] else "detected"),("Domain structure", features["subdomain_count"] <= 2, f'{features["subdomain_count"]} subdomain levels'),("Suspicious tokens", features["suspicious_keyword_count"] == 0, features["suspicious_keywords"]),("Encoding", not bool(features["has_encoded_chars"]), "none detected" if not features["has_encoded_chars"] else "encoded characters"),("TLD", not bool(features["suspicious_tld"]), features["tld"])]
        check_cols = st.columns(4)
        for i, (label, passed, detail) in enumerate(checks):
            with check_cols[i % 4]: st.markdown(f'<div style="padding:.45rem 0;color:{"#6fe3ca" if passed else "#ff7183"}">{"✓" if passed else "!"} <b>{label}</b><br><span class="small-note">{detail}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel"><div class="section-label">SCAN HISTORY</div>', unsafe_allow_html=True)
        if st.session_state.history: st.dataframe(pd.DataFrame(st.session_state.history), hide_index=True, use_container_width=True)
        else: st.caption("No scans in this session yet.")
        report = {key: result[key] for key in ["url", "normalized_url", "timestamp", "risk_score", "classification", "confidence", "benign_probability", "phishing_probability", "features", "explanations"]}
        csv_row = pd.json_normalize(report).to_csv(index=False).encode("utf-8")
        a, b = st.columns(2)
        with a: st.download_button("Download JSON report", json.dumps(report, indent=2, default=str), "urlshield-report.json", "application/json", use_container_width=True)
        with b: st.download_button("Download CSV report", csv_row, "urlshield-report.csv", "text/csv", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Model insights":
    data = bundle()
    st.markdown('<div class="section-label">MODEL INSIGHTS / SYNTHETIC DEMO DATA</div>', unsafe_allow_html=True)
    if not data: st.error("model.pkl is missing. Run python train_model.py first.")
    else:
        st.warning(data.get("data_note", "Demo data only"))
        metrics = data.get("metrics", {})
        cols = st.columns(6)
        for col, item in zip(cols, [("Model", data.get("model_name", "unknown")), ("Dataset size", str(data.get("dataset_size", "n/a"))), ("Features", str(len(data.get("feature_names", [])))), ("Accuracy", f'{metrics.get("accuracy", 0):.0%}'), ("Precision", f'{metrics.get("precision", 0):.0%}'), ("Recall / F1", f'{metrics.get("recall", 0):.0%} / {metrics.get("f1", 0):.0%}')]):
            with col: card(*item)
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        cm, fi = st.columns(2)
        with cm:
            st.subheader("Confusion matrix")
            st.dataframe(pd.DataFrame(data.get("confusion_matrix", []), index=["Actual benign", "Actual phishing"], columns=["Predicted benign", "Predicted phishing"]), use_container_width=True)
        with fi:
            st.subheader("Top feature importance")
            top = sorted(data.get("feature_importance", {}).items(), key=lambda x: x[1], reverse=True)[:8]
            st.bar_chart(pd.DataFrame(top, columns=["Feature", "Importance"]).set_index("Feature"))

elif page == "Methodology":
    st.markdown('<div class="section-label">ABOUT / METHODOLOGY</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><h2>Transparent URL triage</h2><p>URL → Validation → Feature Extraction → ML Prediction → Risk Scoring → Explainable AI</p><p class="small-note">The app parses URL structure locally and does not visit the destination. The demo dataset is synthetic and intended for an interview-ready engineering demonstration.</p><h3>Known limitations</h3><p class="small-note">URL analysis cannot guarantee that a website is malicious. HTTPS alone does not prove legitimacy. Production systems require threat-intelligence, redirect, domain-age, DNS, page-content, and human-review signals.</p></div>', unsafe_allow_html=True)
