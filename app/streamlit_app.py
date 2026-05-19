"""
streamlit_app.py — NrityaAI Streamlit frontend (vibrant compact redesign).

Run:
    streamlit run app/streamlit_app.py
"""

import sys
import time
from pathlib import Path

import requests
import streamlit as st
import plotly.graph_objects as go

_SRC = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(_SRC))

from utils import CLASSES

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="NrityaAI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Reset & base ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="block-container"] {
    background-color: #0A0A0F !important;
    color: #F8FAFC !important;
    padding-top: 0 !important;
}
.block-container {
    padding: 0.5rem 1rem !important;
    max-width: 100% !important;
}
#MainMenu, footer, header, [data-testid="stSidebar"] { visibility: hidden; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #12121A; }
::-webkit-scrollbar-thumb { background: #7C3AED; border-radius: 2px; }

/* ── Tabs ── */
[data-testid="stTabs"] { margin-top: 0; }
[data-testid="stTabs"] button {
    background: transparent !important;
    color: #94A3B8 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 6px 16px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #F8FAFC !important;
    border-bottom: 2px solid #7C3AED !important;
}
[data-testid="stTabsContent"] { padding-top: 0.5rem !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #EC4899) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    font-size: 0.85rem !important;
    width: 100%;
}
.stButton > button:hover { opacity: 0.9 !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 1px dashed #7C3AED !important;
    border-radius: 8px !important;
    background: #12121A !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] { display: none; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div {
    background: #12121A !important;
    border: 1px solid #1E1E2E !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
}

/* ── Checkbox ── */
[data-testid="stCheckbox"] label { font-size: 0.82rem !important; color: #94A3B8 !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #7C3AED !important; }

/* ── Columns gap ── */
[data-testid="column"] { padding: 0 4px !important; }

/* ── Video ── */
video { border-radius: 8px; border: 1px solid #1E1E2E; }

/* ── Metric ── */
[data-testid="stMetric"] label { color: #94A3B8 !important; font-size: 0.72rem !important; }
[data-testid="stMetricValue"] { color: #F8FAFC !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

STYLE_COLORS = {
    "bharatanatyam": "#7C3AED",
    "kathak":        "#EC4899",
    "odissi":        "#06B6D4",
}

def _card(content: str, padding: str = "12px 14px") -> None:
    st.markdown(
        f'<div style="background:#12121A;border:1px solid #1E1E2E;'
        f'border-radius:10px;padding:{padding};">{content}</div>',
        unsafe_allow_html=True,
    )

def _metric_card(label: str, value: str, color: str, bar_pct: float = None) -> str:
    bar_html = ""
    if bar_pct is not None:
        bar_html = (
            f'<div style="background:#1E1E2E;border-radius:2px;height:3px;margin-top:6px;">'
            f'<div style="background:{color};width:{min(bar_pct,100)}%;height:3px;border-radius:2px;"></div>'
            f'</div>'
        )
    return (
        f'<div style="background:#12121A;border:1px solid #1E1E2E;border-radius:10px;'
        f'padding:10px 12px;border-bottom:2px solid {color};">'
        f'<div style="font-size:9px;font-weight:700;color:#94A3B8;letter-spacing:0.08em;'
        f'text-transform:uppercase;margin-bottom:4px;">{label}</div>'
        f'<div style="font-size:18px;font-weight:800;color:{color};">{value}</div>'
        f'{bar_html}</div>'
    )

def _conf_color(pct: float) -> str:
    return "#10B981" if pct >= 80 else ("#F59E0B" if pct >= 50 else "#EF4444")

def _score_color(score: float) -> str:
    return "#10B981" if score >= 75 else ("#F59E0B" if score >= 40 else "#EF4444")

@st.cache_data(ttl=5)
def _health():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.json()
    except Exception:
        return None

# ── Page header ───────────────────────────────────────────────────────────────

health = _health()
api_ok = health is not None and health.get("model_loaded")

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
    padding:10px 0 8px;border-bottom:1px solid #1E1E2E;margin-bottom:6px;">
  <div>
    <div style="font-size:22px;font-weight:800;color:#7C3AED;line-height:1;">NrityaAI</div>
    <div style="font-size:12px;color:#94A3B8;margin-top:1px;">Dance Intelligence System</div>
  </div>
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="background:#7C3AED20;color:#7C3AED;border:1px solid #7C3AED40;
        border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600;">Bharatanatyam</span>
    <span style="background:#EC489920;color:#EC4899;border:1px solid #EC489940;
        border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600;">Kathak</span>
    <span style="background:#06B6D420;color:#06B6D4;border:1px solid #06B6D440;
        border-radius:20px;padding:3px 10px;font-size:11px;font-weight:600;">Odissi</span>
    <span style="font-size:11px;color:{'#10B981' if api_ok else '#EF4444'};margin-left:8px;">
        {'API Connected' if api_ok else 'API Offline'}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["Analyse Video", "Live Webcam"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Analyse Video
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    col_left, col_right = st.columns([45, 55], gap="small")

    # ── Left: upload + video ──────────────────────────────────────────────────
    with col_left:
        st.markdown(
            '<div style="background:#12121A;border:1px dashed #7C3AED;border-radius:8px;'
            'padding:8px;margin-bottom:6px;">'
            '<div style="font-size:12px;font-weight:600;color:#F8FAFC;margin-bottom:2px;">'
            'Drop video file here</div>'
            '<div style="font-size:11px;color:#94A3B8;">Supported: MP4, AVI</div>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "", type=["mp4", "avi"], key="video_upload", label_visibility="collapsed"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if uploaded:
            st.markdown(
                '<div style="max-height:220px;overflow:hidden;border-radius:8px;'
                'border:1px solid #1E1E2E;margin-bottom:6px;">',
                unsafe_allow_html=True,
            )
            st.video(uploaded)
            st.markdown("</div>", unsafe_allow_html=True)

        analyse = st.button("Analyse Dance Performance", key="analyse_btn", disabled=uploaded is None)

    # ── Right: results ────────────────────────────────────────────────────────
    with col_right:
        if "result_v1" not in st.session_state:
            st.session_state.result_v1 = None

        if analyse and uploaded:
            with st.spinner("Analysing dance performance..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/analyze-video",
                        files={"file": (uploaded.name, uploaded.getvalue(), "video/mp4")},
                        timeout=600,
                    )
                    resp.raise_for_status()
                    st.session_state.result_v1 = resp.json()
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Start: uvicorn api.main:app")
                    st.session_state.result_v1 = None
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.result_v1 = None

        result = st.session_state.result_v1

        if result is None:
            st.markdown(
                '<div style="background:#12121A;border:1px solid #1E1E2E;border-radius:10px;'
                'height:300px;display:flex;align-items:center;justify-content:center;">'
                '<span style="color:#94A3B8;font-size:13px;">Results will appear here</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            predicted_raw = result.get("predicted_style", "unknown")
            confidence    = result.get("confidence", 0.0)
            # API returns pose_score as 0-100; display as X/100
            pose_score    = round(float(result.get("pose_score", 0.0)), 1)
            probs         = result.get("class_probabilities", {})
            corrections   = result.get("corrections", [])

            # "Other" threshold: if max class confidence < 60%, not a known ICD style
            OTHER_THRESHOLD = 60.0
            is_other  = confidence < OTHER_THRESHOLD
            predicted = "Other" if is_other else predicted_raw.title()
            style_color = "#94A3B8" if is_other else STYLE_COLORS.get(predicted_raw, "#7C3AED")

            if is_other:
                st.markdown(
                    '<div style="background:#F59E0B15;border:1px solid #F59E0B50;border-radius:8px;'
                    'padding:8px 12px;margin-bottom:6px;">'
                    '<div style="font-size:12px;font-weight:700;color:#F59E0B;">Unrecognised Dance Form</div>'
                    '<div style="font-size:11px;color:#94A3B8;margin-top:2px;">'
                    'No class exceeded the 60% confidence threshold. This video does not appear to '
                    'be Bharatanatyam, Kathak, or Odissi — or the dancer is not fully visible.</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # Row 1: metric cards
            m1, m2 = st.columns(2, gap="small")
            with m1:
                st.markdown(_metric_card("Dance Style", predicted, style_color), unsafe_allow_html=True)
            with m2:
                st.markdown(_metric_card("Confidence", f"{confidence:.1f}%",
                                         _conf_color(confidence), bar_pct=confidence),
                            unsafe_allow_html=True)

            st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)

            # Row 2: plotly chart (keep existing logic, restyle only)
            if probs:
                labels = [s.title() for s in probs]
                values = list(probs.values())
                bar_colors = [style_color if s == predicted_raw else "#1E1E2E" for s in probs]
                bar_borders = [style_color if s == predicted_raw else "#94A3B8" for s in probs]
                fig = go.Figure(go.Bar(
                    x=values, y=labels, orientation="h",
                    marker_color=bar_colors,
                    marker_line_color=bar_borders,
                    marker_line_width=1,
                    text=[f"{v:.1f}%" for v in values],
                    textposition="outside",
                    textfont=dict(color="#F8FAFC", size=11),
                ))
                fig.update_layout(
                    title=dict(text="Classification Confidence",
                               font=dict(color="#94A3B8", size=12), x=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(visible=False, range=[0, 120]),
                    yaxis=dict(tickfont=dict(color="#F8FAFC", size=12), gridcolor="rgba(0,0,0,0)"),
                    margin=dict(l=0, r=0, t=24, b=0),
                    height=130,
                    showlegend=False,
                    font=dict(color="#F8FAFC"),
                )
                st.plotly_chart(fig, use_container_width=True)

            # Row 3: corrections
            st.markdown(
                '<div style="border-top:1px solid #1E1E2E;padding-top:6px;margin-top:2px;"></div>',
                unsafe_allow_html=True,
            )
            if is_other:
                st.markdown(
                    '<div style="background:#94A3B810;border:1px solid #94A3B830;border-radius:8px;'
                    'padding:8px 12px;color:#94A3B8;font-size:12px;">'
                    'Pose corrections are not available for unrecognised dance forms.</div>',
                    unsafe_allow_html=True,
                )
            elif not corrections or corrections == ["Great form! Keep it up."]:
                st.markdown(
                    '<div style="background:#10B98110;border:1px solid #10B981;border-radius:8px;'
                    'padding:8px 12px;display:flex;align-items:center;gap:10px;">'
                    '<span style="font-weight:700;color:#10B981;font-size:13px;">Perfect Form</span>'
                    '<span style="color:#94A3B8;font-size:12px;">Posture matches reference</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                rows_html = ""
                for c in corrections[:6]:
                    parts = c.split(":", 1)
                    joint = parts[0].strip() if len(parts) > 1 else "Joint"
                    text  = parts[1].strip() if len(parts) > 1 else c
                    deg   = ""
                    if "deviation:" in c:
                        try:
                            deg = c.split("deviation:")[-1].replace("°)", "").strip()
                        except Exception:
                            deg = ""
                    badge = (
                        f'<span style="background:#EF444420;color:#EF4444;border-radius:4px;'
                        f'padding:1px 6px;font-size:10px;white-space:nowrap;">{deg} deg</span>'
                        if deg else ""
                    )
                    rows_html += (
                        f'<div style="background:#12121A;border-left:2px solid #EF4444;'
                        f'border-radius:0 6px 6px 0;padding:8px 10px;margin-bottom:4px;'
                        f'display:flex;align-items:center;justify-content:space-between;gap:8px;">'
                        f'<span style="font-weight:700;color:#F8FAFC;font-size:12px;'
                        f'white-space:nowrap;">{joint}</span>'
                        f'<span style="color:#94A3B8;font-size:12px;flex:1;'
                        f'text-align:right;">{text}</span>'
                        f'{badge}</div>'
                    )
                st.markdown(
                    f'<div style="max-height:160px;overflow-y:auto;">{rows_html}</div>',
                    unsafe_allow_html=True,
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Live Webcam
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    _cv2_ok = _mp_ok = True
    try:
        import cv2
    except ImportError:
        _cv2_ok = False
    try:
        import mediapipe as mp
    except ImportError:
        _mp_ok = False

    if not _cv2_ok or not _mp_ok:
        missing = ([] if _cv2_ok else ["opencv-python"]) + ([] if _mp_ok else ["mediapipe"])
        st.error(f"Missing: {', '.join(missing)}")
    else:
        if "score_history" not in st.session_state:
            st.session_state.score_history = []
        if "final_score" not in st.session_state:
            st.session_state.final_score = None

        col_left2, col_right2 = st.columns([52, 48], gap="small")

        with col_left2:
            # header row
            run_webcam = st.checkbox("Start Webcam Analysis", value=False, key="webcam_toggle")
            status_badge = (
                '<span style="background:#EF444420;color:#EF4444;border:1px solid #EF444440;'
                'border-radius:12px;padding:2px 8px;font-size:10px;font-weight:700;">LIVE</span>'
                if run_webcam else
                '<span style="background:#94A3B820;color:#94A3B8;border:1px solid #94A3B840;'
                'border-radius:12px;padding:2px 8px;font-size:10px;font-weight:700;">READY</span>'
            )
            style_choice = st.selectbox(
                "Reference style", options=[c.title() for c in CLASSES],
                key="webcam_style", label_visibility="collapsed"
            )
            style_key = style_choice.lower()

            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'margin-bottom:4px;">'
                f'<span style="font-size:14px;font-weight:700;color:#F8FAFC;">Live Analysis</span>'
                f'{status_badge}</div>',
                unsafe_allow_html=True,
            )

            frame_placeholder = st.empty()
            fps_placeholder   = st.empty()

        with col_right2:
            st.markdown(
                '<div style="font-size:12px;font-weight:700;color:#F8FAFC;margin-bottom:6px;">'
                'Live Metrics</div>',
                unsafe_allow_html=True,
            )
            metric_placeholder = st.empty()
            st.markdown(
                '<div style="font-size:12px;font-weight:700;color:#F8FAFC;margin:6px 0 4px;">'
                'Live Corrections</div>',
                unsafe_allow_html=True,
            )
            correction_placeholder = st.empty()
            st.markdown(
                '<div style="font-size:12px;font-weight:700;color:#F8FAFC;margin:8px 0 4px;">'
                'Score History <span style="color:#94A3B8;font-size:10px;font-weight:400;">'
                '(snapshot every 10s)</span></div>',
                unsafe_allow_html=True,
            )
            history_placeholder = st.empty()

            _hbtn1, _hbtn2 = st.columns(2, gap="small")
            with _hbtn1:
                _get_final = st.button("Get Final Score", key="final_score_btn")
            with _hbtn2:
                _clear_hist = st.button("Clear History", key="clear_hist_btn")
            _final_ph = st.empty()

            if _get_final and st.session_state.score_history:
                avg = round(
                    sum(v for _, v in st.session_state.score_history)
                    / len(st.session_state.score_history), 1
                )
                st.session_state.final_score = avg
            if _clear_hist:
                st.session_state.score_history = []
                st.session_state.final_score = None

            if st.session_state.final_score is not None:
                _fs  = st.session_state.final_score
                _fsc = _score_color(_fs)
                _final_ph.markdown(
                    f'<div style="background:#12121A;border:1px solid {_fsc}50;'
                    f'border-radius:10px;padding:10px 12px;margin-top:6px;">'
                    f'<div style="font-size:9px;font-weight:700;color:#94A3B8;'
                    f'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">'
                    f'Final Score</div>'
                    f'<div style="font-size:22px;font-weight:800;color:{_fsc};">'
                    f'{_fs} / 100</div>'
                    f'<div style="color:#94A3B8;font-size:10px;margin-top:2px;">'
                    f'avg of {len(st.session_state.score_history)} snapshots</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        if not run_webcam:
            frame_placeholder.markdown(
                '<div style="background:#12121A;border:1px solid #1E1E2E;border-radius:8px;'
                'height:300px;display:flex;align-items:center;justify-content:center;">'
                '<span style="color:#94A3B8;font-size:13px;">'
                'Enable checkbox above to start webcam</span></div>',
                unsafe_allow_html=True,
            )
        else:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision
            _MODEL_PATH = str(Path(__file__).parent.parent / "models" / "pose_landmarker.task")

            _base_opts = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
            _opts = mp_vision.PoseLandmarkerOptions(
                base_options=_base_opts,
                running_mode=mp_vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
            )
            _CONNECTIONS = [
                (11,12),(11,13),(13,15),(12,14),(14,16),
                (11,23),(12,24),(23,24),(23,25),(24,26),(25,27),(26,28),
            ]

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("Could not open webcam.")
            else:
                frame_count      = 0
                corrections_cache: list[str] = []
                score_cache: float           = 0.0
                t_prev           = time.time()
                t_last_snapshot  = time.time()

                with mp_vision.PoseLandmarker.create_from_options(_opts) as detector:
                    while run_webcam:
                        ret, frame = cap.read()
                        if not ret:
                            st.warning("Webcam feed lost.")
                            break

                        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                        det    = detector.detect(mp_img)

                        if det.pose_landmarks:
                            lms   = det.pose_landmarks[0]
                            h, w  = frame.shape[:2]
                            for a, b in _CONNECTIONS:
                                x1,y1 = int(lms[a].x*w), int(lms[a].y*h)
                                x2,y2 = int(lms[b].x*w), int(lms[b].y*h)
                                cv2.line(frame, (x1,y1), (x2,y2), (124,58,237), 2)
                            for lm in lms:
                                cx,cy = int(lm.x*w), int(lm.y*h)
                                cv2.circle(frame, (cx,cy), 4, (6,182,212), -1)

                            if frame_count % 30 == 0:
                                kps = [[lm.x,lm.y,lm.z,lm.visibility] for lm in lms]
                                try:
                                    r = requests.post(
                                        f"{API_BASE}/analyze-frame",
                                        json={"keypoints": kps, "style": style_key},
                                        timeout=5,
                                    )
                                    if r.ok:
                                        data              = r.json()
                                        corrections_cache = data.get("corrections", [])
                                        # API returns 0-100; display as X/100
                                        # API /analyze-frame returns overall_score() → 0-100
                                        score_cache = round(float(data.get("pose_score", 0.0)), 1)
                                except Exception:
                                    pass

                        t_now = time.time()
                        fps   = 1.0 / max(t_now - t_prev, 0.001)
                        t_prev = t_now

                        # Snapshot score every 10 seconds
                        if t_now - t_last_snapshot >= 10.0:
                            st.session_state.score_history.append(
                                (time.strftime("%H:%M:%S"), score_cache)
                            )
                            t_last_snapshot = t_now

                        # Update score history panel
                        with history_placeholder.container():
                            if not st.session_state.score_history:
                                st.markdown(
                                    '<span style="color:#94A3B8;font-size:11px;">'
                                    'Snapshots appear every 10s…</span>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                _hist_html = ""
                                for _ts, _sc in st.session_state.score_history[-6:]:
                                    _hc = _score_color(_sc)
                                    _bw = min(_sc, 100)
                                    _hist_html += (
                                        f'<div style="display:flex;align-items:center;gap:8px;'
                                        f'margin-bottom:5px;">'
                                        f'<span style="font-size:10px;color:#94A3B8;'
                                        f'white-space:nowrap;min-width:54px;">{_ts}</span>'
                                        f'<div style="flex:1;background:#1E1E2E;border-radius:2px;height:4px;">'
                                        f'<div style="background:{_hc};width:{_bw}%;height:4px;'
                                        f'border-radius:2px;transition:width 0.4s;"></div></div>'
                                        f'<span style="font-size:11px;font-weight:700;color:{_hc};'
                                        f'white-space:nowrap;min-width:36px;text-align:right;">'
                                        f'{_sc:.0f}</span>'
                                        f'</div>'
                                    )
                                st.markdown(
                                    f'<div style="max-height:110px;overflow-y:auto;">{_hist_html}</div>',
                                    unsafe_allow_html=True,
                                )

                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                        fps_placeholder.markdown(
                            f'<span style="font-size:11px;color:#94A3B8;">{fps:.0f} FPS</span>',
                            unsafe_allow_html=True,
                        )

                        sc_color = _score_color(score_cache)
                        with metric_placeholder.container():
                            ma, mb = st.columns(2, gap="small")
                            with ma:
                                st.markdown(
                                    _metric_card("Style", style_choice,
                                                 STYLE_COLORS.get(style_key, "#7C3AED")),
                                    unsafe_allow_html=True,
                                )
                            with mb:
                                st.markdown(
                                    _metric_card("Pose Score", f"{score_cache} / 100", sc_color),
                                    unsafe_allow_html=True,
                                )

                        with correction_placeholder.container():
                            if not corrections_cache or corrections_cache == ["Great form! Keep it up."]:
                                st.markdown(
                                    '<div style="background:#10B98110;border:1px solid #10B981;'
                                    'border-radius:8px;padding:8px 10px;font-size:12px;">'
                                    '<span style="color:#10B981;font-weight:700;">Perfect Form</span>'
                                    '<span style="color:#94A3B8;"> — Posture matches reference</span>'
                                    '</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                rows = ""
                                for c in corrections_cache[:4]:
                                    parts = c.split(":", 1)
                                    joint = parts[0].strip() if len(parts)>1 else ""
                                    text  = parts[1].strip() if len(parts)>1 else c
                                    deg   = ""
                                    if "deviation:" in c:
                                        try:
                                            deg = c.split("deviation:")[-1].replace("°)","").strip()
                                        except Exception:
                                            pass
                                    badge = (
                                        f'<span style="background:#EF444420;color:#EF4444;'
                                        f'border-radius:4px;padding:1px 5px;font-size:10px;">'
                                        f'{deg} deg</span>' if deg else ""
                                    )
                                    rows += (
                                        f'<div style="background:#12121A;border-left:2px solid #EF4444;'
                                        f'border-radius:0 6px 6px 0;padding:8px 10px;margin-bottom:4px;">'
                                        f'<div style="display:flex;justify-content:space-between;'
                                        f'align-items:center;">'
                                        f'<span style="font-weight:700;color:#F8FAFC;font-size:12px;">'
                                        f'{joint}</span>{badge}</div>'
                                        f'<div style="color:#94A3B8;font-size:11px;margin-top:2px;">'
                                        f'{text}</div></div>'
                                    )
                                st.markdown(
                                    f'<div style="max-height:200px;overflow-y:auto;">{rows}</div>',
                                    unsafe_allow_html=True,
                                )

                        frame_count += 1
                        time.sleep(0.033)

                cap.release()
