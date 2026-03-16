"""
Financial term explainer using st.expander + POST /api/explain.
Results are cached in st.session_state['term_cache'] to avoid repeated API calls.
"""

import streamlit as st
from services.api_client import APIClient, APIError


def render_term(term: str, display_text: str):
    """
    Render an expandable term explanation.

    term         — the raw financial term to explain (e.g. "arbitrage")
    display_text — the label shown on the expander (e.g. "Arbitrage")
    """
    if "term_cache" not in st.session_state:
        st.session_state["term_cache"] = {}

    with st.expander(f"📖 {display_text}"):
        cache = st.session_state["term_cache"]

        if term in cache:
            st.markdown(cache[term])
            return

        if st.button(f"Explain '{display_text}'", key=f"explain_{term}"):
            lang = st.session_state.get("language", "en")
            client = APIClient()
            with st.spinner("Asking AI…"):
                try:
                    result = client.post_explain(term, lang)
                    explanation = result.get("explanation", "No explanation returned.")
                    cache[term] = explanation
                    st.markdown(explanation)
                except APIError as e:
                    st.error(f"Could not fetch explanation: {e.message}")
        else:
            st.caption("Click the button above to get an AI explanation.")
