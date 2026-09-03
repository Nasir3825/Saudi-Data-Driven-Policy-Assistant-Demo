from __future__ import annotations

import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from src.config import APP_TITLE, DATA_SNAPSHOT_DATE
from src.data import (
    build_evidence_documents,
    format_period_label,
    load_knowledge,
    load_series,
    load_snapshot,
)
from src.indicator_api import (
    fetch_enabled_indicators,
    load_api_registry,
    merge_live_series,
    merge_live_snapshot,
)
from src.llm import answer_question
from src.policy_brief import build_markdown_brief
from src.retrieval import EvidenceRetriever

load_dotenv()
st.set_page_config(page_title=APP_TITLE, page_icon="🇸🇦", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2.2rem; max-width: 1450px;}
.hero {background:linear-gradient(115deg,#063c2d,#007a4d 58%,#14a46f);padding:28px 32px;border-radius:18px;color:#fff;margin:0 0 18px;box-shadow:0 10px 28px rgba(0,80,52,.18)}
.hero h1 {margin:0;font-size:2.15rem}.hero p {margin:.5rem 0 0;opacity:.92;font-size:1.04rem}
div[data-testid="stMetric"] {background:#fff;border:1px solid #e6ece9;border-radius:14px;padding:14px;box-shadow:0 3px 10px rgba(4,48,35,.05)}
div[data-testid="stMetricLabel"] {color:#4a6258} div[data-testid="stMetricValue"] {color:#063c2d}
.history-banner {
    background: linear-gradient(100deg, #e8f5ee, #f7fcf9);
    border-left: 6px solid #007a4d;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0 22px;
    box-shadow: 0 3px 10px rgba(4,48,35,.08);
}
.history-banner-title {
    color: #063c2d;
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 4px;
}
.history-banner-text {
    color: #28483b;
    font-size: 0.98rem;
}
.question-heading {
    background: #063c2d;
    color: white;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 12px 0 6px;
    font-size: 1.15rem;
    font-weight: 700;
}
.question-subheading {
    color: #4a6258;
    margin: 0 0 12px;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_data() -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    snapshot = load_snapshot()
    series = load_series()
    knowledge = build_evidence_documents(snapshot, series, load_knowledge())
    return snapshot, series, knowledge


snapshot, series, _ = get_data()
api_registry = load_api_registry()

st.markdown("""<div class="hero"><h1>Saudi Data-Driven Policy Assistant</h1><p>Executive economic intelligence for Saudi Arabia — live indicators, evidence-based analysis, and bilingual policy briefs.</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Response language", ["English", "العربية"])
    model = st.text_input(
        "Groq model",
        value=os.getenv("GROQ_MODEL", "auto"),
        help="Keep this as auto so the app selects a model available to your Groq account.",
    )
    entered_key = st.text_input("Groq API key (optional)", type="password")
    api_key = entered_key or os.getenv("GROQ_API_KEY")
    st.info("Use model = auto. Without a key, the app runs in safe offline retrieval mode.")
    st.divider()
    st.subheader("Live indicator APIs")
    enabled_count = sum(item["enabled"] for item in api_registry)
    st.caption(f"{enabled_count} of {len(api_registry)} configured indicators are enabled.")
    if st.button("Refresh latest API data", type="primary"):
        with st.spinner("Fetching enabled indicator APIs..."):
            live, api_status = fetch_enabled_indicators(api_registry)
        st.session_state["live_indicator_data"] = live
        st.session_state["api_status"] = api_status
    st.caption("Edit data/api_indicators.json, then redeploy or reboot the app.")
    st.markdown("[Open DataSaudi](https://datasaudi.sa/en)")
    st.caption("Decision-support tool. Validate official figures before publication or formal use.")

live_data = st.session_state.get("live_indicator_data", pd.DataFrame())
if not live_data.empty:
    snapshot = merge_live_snapshot(snapshot, live_data)
    series = merge_live_series(series, live_data)
    data_mode = "Live APIs with packaged fallback"
else:
    data_mode = "Packaged verified snapshot"
if live_data.empty:
    st.warning(
        "⚠️ Live indicator APIs have not been refreshed in this session. "
        "Any answer generated now will use the packaged historical evidence dataset, "
        "not newly refreshed API observations. Use **Refresh latest API data** in the sidebar "
        "before generating an answer."
    )
else:
    st.success(
        "✓ Live indicator API data has been refreshed for this session. "
        "The application will use refreshed observations where available."
    )
knowledge = build_evidence_documents(snapshot, series, load_knowledge())
retriever = EvidenceRetriever(knowledge)
st.caption(
    "Professional Saudi economic intelligence workspace | "
    f"Data mode: {data_mode} | Packaged snapshot: {DATA_SNAPSHOT_DATE}"
)

tabs = st.tabs(["💬 Ask the Policy Assistant", "📊 Overview", "Evidence Explorer", "API Status", "Methodology"])

with tabs[1]:
    all_indicators = sorted(snapshot["indicator"].dropna().unique().tolist())
    default_indicators = [
        "CPI inflation",
        "Real GDP at constant prices",
        "Merchandise exports",
        "Merchandise imports",
        "Saudi unemployment rate",
        "Purchasing Managers' Index",
    ]
    default_indicators = [name for name in default_indicators if name in all_indicators]

    st.subheader("Economic indicator overview")
    filter_column, select_all_column = st.columns([5, 1])
    with select_all_column:
        select_all = st.toggle("Select all", help="Include every available indicator.")
    with filter_column:
        chosen_indicators = st.multiselect(
            "Selected indicators",
            options=all_indicators,
            default=all_indicators if select_all else default_indicators,
            disabled=select_all,
            placeholder="Search and select indicators",
        )
    if select_all:
        chosen_indicators = all_indicators

    if not chosen_indicators:
        st.info("Select at least one indicator to display cards, charts, and data.")
    else:
        latest_snapshot = snapshot.loc[
            snapshot.groupby("indicator")["date"].idxmax()
        ].copy()
        selected_latest = latest_snapshot[
            latest_snapshot["indicator"].isin(chosen_indicators)
        ].sort_values(["category", "indicator"], na_position="last")

        st.markdown("#### Latest values")
        metric_columns = st.columns(4)
        for index, (_, row) in enumerate(selected_latest.iterrows()):
            with metric_columns[index % 4]:
                st.metric(row["indicator"], f"{row['value']:g} {row['unit']}")
                st.caption(
                    f"Period: {format_period_label(row['date'], row['frequency'])} · "
                    f"{row['frequency']}"
                )

        st.markdown("#### Visualizations")
        st.caption(
            "Indicators are charted separately by unit so values with different scales remain meaningful. "
            "Indicators without historical observations are shown with their latest available point."
        )
        series_columns = [
            "indicator", "date", "value", "unit", "source_name", "source_url", "accessed_on"
        ]
        snapshot_points = latest_snapshot[series_columns]
        missing_from_series = set(all_indicators).difference(series["indicator"].unique())
        chart_series = pd.concat(
            [
                series[series_columns],
                snapshot_points[snapshot_points["indicator"].isin(missing_from_series)],
            ],
            ignore_index=True,
        )
        selected_series = chart_series[
            chart_series["indicator"].isin(chosen_indicators)
        ].sort_values(["unit", "indicator", "date"])

        if selected_series.empty:
            st.info("No time-series observations are available for the selected indicators.")
        else:
            for unit, unit_data in selected_series.groupby("unit", dropna=False):
                unit_label = str(unit) if pd.notna(unit) else "Value"
                chart_type = st.selectbox(
                    f"Chart type — {unit_label}",
                    options=["Line", "Bar", "Area", "Scatter"],
                    key=f"chart-type-{unit_label}",
                    help=f"Choose the chart type independently for the {unit_label} visualization.",
                )
                chart_arguments = {
                    "data_frame": unit_data,
                    "x": "date",
                    "y": "value",
                    "color": "indicator",
                    "title": unit_label,
                    "labels": {
                        "value": unit_label,
                        "date": "Period",
                        "indicator": "Indicator",
                    },
                }
                if chart_type == "Bar":
                    figure = px.bar(**chart_arguments, barmode="group")
                elif chart_type == "Area":
                    figure = px.area(**chart_arguments, markers=True)
                elif chart_type == "Scatter":
                    figure = px.scatter(**chart_arguments)
                else:
                    figure = px.line(**chart_arguments, markers=True)
                figure.update_layout(
                    legend_title_text="Indicator",
                    hovermode="x unified",
                    margin={"l": 20, "r": 20, "t": 55, "b": 20},
                )
                st.plotly_chart(
                    figure,
                    width="stretch",
                    key=f"overview-chart-{chart_type}-{unit_label}",
                )

        st.markdown("#### View and download indicator data")
        latest_data_tab, history_data_tab = st.tabs(["Latest values", "Time series"])
        with latest_data_tab:
            latest_download = selected_latest.copy()
            latest_download.insert(
                2,
                "period",
                latest_download.apply(
                    lambda row: format_period_label(row["date"], row["frequency"]), axis=1
                ),
            )
            latest_download["date"] = latest_download["date"].dt.strftime("%Y-%m-%d")
            latest_download["accessed_on"] = latest_download["accessed_on"].dt.strftime("%Y-%m-%d")
            st.dataframe(latest_download, width="stretch", hide_index=True)
            st.download_button(
                "Download selected latest values (CSV)",
                data=latest_download.to_csv(index=False).encode("utf-8"),
                file_name="selected_indicator_latest_values.csv",
                mime="text/csv",
                key="download-overview-latest",
            )
        with history_data_tab:
            history_download = selected_series.copy()
            history_download["date"] = history_download["date"].dt.strftime("%Y-%m-%d")
            if "accessed_on" in history_download:
                history_download["accessed_on"] = pd.to_datetime(
                    history_download["accessed_on"], errors="coerce"
                ).dt.strftime("%Y-%m-%d")
            st.dataframe(history_download, width="stretch", hide_index=True)
            st.download_button(
                "Download selected time series (CSV)",
                data=history_download.to_csv(index=False).encode("utf-8"),
                file_name="selected_indicator_time_series.csv",
                mime="text/csv",
                key="download-overview-history",
            )

with tabs[0]:
    st.subheader("Ask the Saudi Data-Driven Policy Assistant")

    historical_indicator_count = series["indicator"].nunique()
    historical_observation_count = len(series)

    st.markdown(
        f"""
        <div class="history-banner">
            <div class="history-banner-title">Available Economic Evidence</div>
            <div class="history-banner-text">
                Searches the available history: <b>{historical_observation_count:,} observations</b>
                across <b>{historical_indicator_count} indicators</b>.
                Refresh enabled APIs from the sidebar to load the latest available history.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    suggestions = {
        "English": [
            "How has CPI inflation changed over the available historical period?",
            "What do the latest inflation indicators suggest for Saudi Arabia?",
            "Summarize the latest real GDP performance and its policy relevance.",
            "How have oil and non-oil real GDP activities changed over time?",
            "What does the Purchasing Managers' Index indicate about business activity?",
            "How have merchandise exports, imports, and the trade balance changed?",
            "What is the latest Saudi unemployment rate and how has it evolved?",
            "Compare CPI inflation and Wholesale Price Index inflation.",
            "What does the available data show about tourism in Saudi Arabia?",
            "Which indicators show the strongest recent economic improvement?",
            "Give me a short evidence-based Saudi economic briefing.",
            "What are the main risks or limitations when interpreting these indicators?",
        ],
        "العربية": [
            "كيف تغير التضخم في المملكة خلال الفترة التاريخية المتاحة؟",
            "ماذا تظهر أحدث مؤشرات التضخم في المملكة العربية السعودية؟",
            "لخص أحدث أداء للناتج المحلي الإجمالي الحقيقي وأهميته للسياسات الاقتصادية.",
            "كيف تغير الناتج المحلي الإجمالي الحقيقي للأنشطة النفطية وغير النفطية؟",
            "ماذا يشير مؤشر مديري المشتريات حول نشاط الأعمال؟",
            "كيف تغيرت الصادرات والواردات والميزان التجاري للسلع؟",
            "ما هو أحدث معدل بطالة للسعوديين وكيف تطور عبر الوقت؟",
            "قارن بين تضخم أسعار المستهلكين وتضخم أسعار الجملة.",
            "ماذا تظهر البيانات المتاحة حول السياحة في المملكة؟",
            "ما المؤشرات التي تظهر أقوى تحسن اقتصادي في الفترة الأخيرة؟",
            "قدم لي موجزاً اقتصادياً سعودياً قصيراً مبنياً على الأدلة.",
            "ما أهم المخاطر أو القيود عند تفسير هذه المؤشرات؟",
        ],
    }
    if "question_text" not in st.session_state:
        st.session_state["question_text"] = suggestions[language][0]

    def use_suggested_question(selected_question: str) -> None:
        st.session_state["question_text"] = selected_question

    st.markdown(
        '<div class="question-heading">Ask Your Economic Policy Question</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="question-subheading">Choose a response format, then write your question or select one from the suggestions.</div>',
        unsafe_allow_html=True,
    )

    response_mode = st.radio(
        "Choose the response format",
        options=["Policy brief", "Detailed policy analysis"],
        horizontal=True,
        help=(
            "Policy brief provides a concise executive summary. "
            "Detailed policy analysis provides a fuller evidence-based discussion, "
            "including policy options, trade-offs, and limitations."
        ),
    )

    if response_mode == "Policy brief":
        st.caption("Concise executive summary with key evidence, policy relevance, and caveats.")
    else:
        st.caption(
            "Fuller evidence-based analysis with policy options, implementation considerations, "
            "trade-offs, risks, and limitations."
        )

    question = st.text_area(
        "Your question",
        key="question_text",
        height=120,
        placeholder="Ask a question about Saudi economic indicators...",
    )

    with st.expander("Suggested research questions", expanded=False):
        st.caption(
            "Select a question to place it automatically in the question box above."
        )

        for row_start in range(0, len(suggestions[language]), 2):
            left_column, right_column = st.columns(2)

            for column, question_number in zip(
                [left_column, right_column],
                range(row_start, min(row_start + 2, len(suggestions[language]))),
            ):
                suggested_question = suggestions[language][question_number]

                column.button(
                    suggested_question,
                    key=f"suggestion_{language}_{question_number}",
                    use_container_width=True,
                    on_click=use_suggested_question,
                    args=(suggested_question,),
                )
    top_k = st.slider("Historical evidence passages", 3, 12, 8)
    if live_data.empty:
        st.info(
            "To use the latest available API history, click **Refresh latest API data** "
            "in the sidebar. You may also continue using the packaged historical data."
        )

        use_packaged_history = st.checkbox(
            "I understand that this answer will use packaged historical data because the live APIs have not been refreshed.",
            value=False,
        )
    else:
        use_packaged_history = True

    generate_answer = st.button(
        "Generate evidence-grounded answer",
        type="primary",
        disabled=not use_packaged_history,
    )

    if generate_answer:
        evidence = retriever.search(question, top_k=top_k)
        try:
            answer = answer_question(
                question,
                evidence,
                language,
                api_key=api_key,
                model=model,
                response_mode=response_mode,
            )
        except Exception as exc:
            st.error(f"The language-model request failed. Check the key/model or use offline mode. Details: {exc}")
        else:
            st.session_state["last_question"] = question
            st.session_state["last_answer"] = answer
            st.session_state["last_evidence"] = evidence
            st.session_state["last_response_mode"] = response_mode

    if "last_answer" in st.session_state:
        st.markdown(st.session_state["last_answer"])
        evidence = st.session_state["last_evidence"]
        with st.expander("Retrieved evidence and sources", expanded=True):
            for item in evidence:
                st.markdown(
                    f"**[{item.source_id}] {item.title}** — similarity {item.score:.2f}  \n"
                    f"{item.text}  \n[{item.source_name}]({item.source_url}) · as of {item.as_of}"
                )
        response_mode_used = st.session_state.get("last_response_mode", "Policy brief")

        brief = build_markdown_brief(
            st.session_state["last_question"],
            st.session_state["last_answer"],
            evidence,
            response_mode_used,
        )        
        
        st.download_button(
            f"Download {response_mode_used.lower()}",
            data=brief,
            file_name=(
                "saudi_detailed_policy_analysis.md"
                if response_mode_used == "Detailed policy analysis"
                else "saudi_economic_policy_brief.md"
            ),
            mime="text/markdown",
        )

with tabs[2]:
    st.subheader("Verified snapshot")
    display = snapshot.copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    display["accessed_on"] = display["accessed_on"].dt.strftime("%Y-%m-%d")
    st.dataframe(display, width="stretch", hide_index=True)
    st.download_button(
        "Download snapshot CSV",
        data=display.to_csv(index=False).encode("utf-8"),
        file_name="official_snapshot.csv",
        mime="text/csv",
    )

with tabs[3]:
    st.subheader("Indicator API status")
    st.caption("Configured endpoints are read only after you select Refresh enabled APIs.")
    status = st.session_state.get("api_status")
    if status is None:
        status = pd.DataFrame(
            [
                {
                    "id": item["id"],
                    "indicator": item["indicator"],
                    "status": "Enabled — ready to refresh" if item["enabled"] else "Disabled — add endpoint then enable",
                }
                for item in api_registry
            ]
        )
    st.dataframe(status, width="stretch", hide_index=True)
    st.download_button(
        "Download API configuration",
        data=json.dumps(api_registry, indent=2).encode("utf-8"),
        file_name="api_indicators.json",
        mime="application/json",
    )

with tabs[4]:
    st.subheader("Methodology and governance")
    st.markdown(
        """
1. Official observations and curated definitions are loaded from the packaged evidence base.
2. Optional configured indicator APIs can replace matching packaged observations after a manual refresh.
3. TF-IDF retrieval ranks the most relevant passages for the user's question.
4. Groq receives only the question and retrieved evidence, with instructions to cite every factual claim.
5. If no API key is available, the app returns retrieved evidence without calling an LLM.
6. The user can inspect sources and download the resulting brief.

**Governance:** The packaged CSV is a point-in-time reference dataset, not a complete national database. Retrieval similarity does not prove factual sufficiency, and generated interpretations require expert review.
"""
    )
    st.caption("Prepared by Syed Nasir Hussain Shah | Saudi Economic Policy Analysis")
