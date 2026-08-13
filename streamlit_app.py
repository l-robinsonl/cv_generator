"""Public bring-your-own-key Streamlit interface for synthetic CV generation."""

from io import BytesIO
import zipfile

import streamlit as st

from cv_generator.config import (
    CAREER_PROGRESSIONS,
    COUNTRIES,
    EXPERIENCE_LEVELS,
    INDUSTRIES,
    MAX_RESUMES,
    OUTPUT_FORMATS,
    PROVIDERS,
    WEB_CONCURRENCY,
)
from cv_generator.generator import GenerationOptions, GenerationResult, ResumeGenerator


st.set_page_config(
    page_title="Synthetic CV Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme(dark_mode: bool) -> None:
    """Apply an accessible app-wide palette without relying on browser extensions."""
    palette = (
        {
            "page": "#121212",
            "page_glow": "rgba(0, 230, 118, 0.10)",
            "surface": "#181818",
            "surface_raised": "#1e1e1e",
            "sidebar": "#1e1e1e",
            "text": "#e0e0e0",
            "muted": "#a8b0ac",
            "border": "rgba(224, 224, 224, 0.14)",
            "accent": "#00e676",
            "accent_dark": "#00a854",
            "accent_soft": "rgba(0, 230, 118, 0.12)",
            "shadow": "rgba(0, 0, 0, 0.42)",
            "input": "#242424",
            "button_text": "#07150e",
        }
        if dark_mode
        else {
            "page": "#f8f9fa",
            "page_glow": "rgba(0, 128, 128, 0.10)",
            "surface": "#ffffff",
            "surface_raised": "#ffffff",
            "sidebar": "#e9ecef",
            "text": "#212529",
            "muted": "#5f686f",
            "border": "rgba(33, 37, 41, 0.14)",
            "accent": "#008080",
            "accent_dark": "#006666",
            "accent_soft": "rgba(0, 128, 128, 0.10)",
            "shadow": "rgba(33, 37, 41, 0.12)",
            "input": "#ffffff",
            "button_text": "#ffffff",
        }
    )
    color_scheme = "dark" if dark_mode else "light"
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: {color_scheme}; }}
        .stApp {{
            color: {palette['text']};
            background:
                radial-gradient(circle at 82% 4%, {palette['page_glow']} 0, transparent 30rem),
                radial-gradient(circle at 15% 40%, {palette['accent_soft']} 0, transparent 34rem),
                {palette['page']};
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stToolbar"] {{ color: {palette['text']}; }}
        [data-testid="stSidebar"] {{
            background: {palette['sidebar']};
            border-right: 1px solid {palette['border']};
        }}
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="collapsedControl"] button {{
            color: {palette['text']};
            background: {palette['surface']};
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding-top: 1.5rem; }}
        h1, h2, h3, p, label, .stMarkdown, [data-testid="stWidgetLabel"] {{
            color: {palette['text']};
        }}
        .hero-shell {{
            position: relative;
            overflow: hidden;
            padding: clamp(1.6rem, 4vw, 3.25rem);
            margin: 0.35rem 0 1.35rem;
            border: 1px solid {palette['border']};
            border-radius: 28px;
            background: linear-gradient(135deg, {palette['surface_raised']} 0%, {palette['surface']} 72%);
            box-shadow: 0 24px 70px {palette['shadow']};
        }}
        .hero-shell::after {{
            content: "CV";
            position: absolute;
            right: -0.2rem;
            bottom: -3.7rem;
            color: {palette['accent_soft']};
            font-size: clamp(8rem, 20vw, 16rem);
            font-weight: 900;
            line-height: 1;
            letter-spacing: -0.09em;
            pointer-events: none;
        }}
        .hero-content {{ position: relative; z-index: 1; max-width: 760px; }}
        .eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: {palette['accent']};
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }}
        .eyebrow-dot {{
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 50%;
            background: {palette['accent']};
            box-shadow: 0 0 0 5px {palette['accent_soft']};
        }}
        .hero-title {{
            max-width: 700px;
            margin: 1rem 0 0.8rem;
            color: {palette['text']};
            font-size: clamp(2.2rem, 5vw, 4.3rem);
            font-weight: 760;
            line-height: 0.98;
            letter-spacing: -0.055em;
        }}
        .hero-copy {{
            max-width: 650px;
            margin: 0;
            color: {palette['muted']};
            font-size: 1.04rem;
            line-height: 1.65;
        }}
        .hero-meta {{ display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1.35rem; }}
        .hero-pill {{
            display: inline-flex;
            padding: 0.42rem 0.72rem;
            border: 1px solid {palette['border']};
            border-radius: 999px;
            color: {palette['muted']};
            background: {palette['accent_soft']};
            font-size: 0.8rem;
            font-weight: 650;
        }}
        .side-brand {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.1rem; }}
        .brand-mark {{
            display: grid;
            width: 2.6rem;
            height: 2.6rem;
            place-items: center;
            border-radius: 13px;
            color: white;
            background: linear-gradient(145deg, {palette['accent']}, {palette['accent_dark']});
            box-shadow: 0 8px 20px {palette['shadow']};
            font-weight: 850;
            letter-spacing: -0.04em;
        }}
        .brand-name {{ color: {palette['text']}; font-weight: 780; line-height: 1.1; }}
        .brand-note {{ color: {palette['muted']}; font-size: 0.76rem; margin-top: 0.2rem; }}
        .section-kicker {{
            color: {palette['accent']};
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: -0.6rem;
        }}
        [data-testid="stForm"] {{
            padding: clamp(1.15rem, 3vw, 2rem);
            border: 1px solid {palette['border']};
            border-radius: 22px;
            background: {palette['surface']};
            box-shadow: 0 18px 50px {palette['shadow']};
        }}
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input {{
            color: {palette['text']} !important;
            background: {palette['input']} !important;
            border-color: {palette['border']} !important;
        }}
        div[data-baseweb="tag"] {{
            color: {palette['text']} !important;
            background: {palette['accent_soft']} !important;
        }}
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"] {{
            color: {palette['text']} !important;
            background: {palette['surface_raised']} !important;
        }}
        li[role="option"] {{ color: {palette['text']} !important; }}
        li[role="option"]:hover {{ background: {palette['accent_soft']} !important; }}
        [data-testid="stCheckbox"] svg,
        [data-testid="stToggle"] svg {{ color: {palette['accent']} !important; }}
        [data-testid="stFormSubmitButton"] button,
        [data-testid="stDownloadButton"] button {{
            min-height: 3rem;
            border: 0;
            border-radius: 13px;
            color: {palette['button_text']} !important;
            background: linear-gradient(120deg, {palette['accent']}, {palette['accent_dark']});
            box-shadow: 0 10px 24px {palette['shadow']};
            font-weight: 760;
            transition: transform 150ms ease, box-shadow 150ms ease, filter 150ms ease;
        }}
        [data-testid="stFormSubmitButton"] button:hover,
        [data-testid="stDownloadButton"] button:hover {{
            filter: brightness(1.06);
            transform: translateY(-1px);
            box-shadow: 0 14px 30px {palette['shadow']};
        }}
        [data-testid="stMetric"] {{
            padding: 1rem;
            border: 1px solid {palette['border']};
            border-radius: 16px;
            background: {palette['surface']};
        }}
        [data-testid="stExpander"], [data-testid="stAlert"] {{
            border-color: {palette['border']};
            border-radius: 14px;
        }}
        hr {{ border-color: {palette['border']} !important; }}
        .stCaption, [data-testid="stCaptionContainer"], small {{ color: {palette['muted']} !important; }}
        @media (max-width: 640px) {{
            .hero-shell {{ border-radius: 20px; padding: 1.4rem; }}
            .hero-title {{ font-size: 2.35rem; }}
            .hero-shell::after {{ opacity: 0.6; }}
            [data-testid="stForm"] {{ border-radius: 18px; padding: 1rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def make_zip(result: GenerationResult) -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for document in result.documents:
            archive.writestr(document.relative_path, document.content)
    return output.getvalue()


def show_usage(result: GenerationResult) -> None:
    st.subheader("Usage and estimated cost")
    usage = result.usage
    columns = st.columns(3)
    columns[0].metric("Input tokens", f"{usage.input_tokens:,}")
    columns[1].metric("Output tokens", f"{usage.output_tokens:,}")
    columns[2].metric("Total tokens", f"{usage.total_tokens:,}")
    if usage.cached_input_tokens:
        st.caption(f"Cached input tokens: {usage.cached_input_tokens:,}")

    if result.cost is None:
        st.info("Token usage is available, but pricing is not verified for this model override.")
        return
    costs = result.cost
    cost_columns = st.columns(3)
    cost_columns[0].metric("Input cost", f"${costs.input_cost:.6f}")
    cost_columns[1].metric("Output cost", f"${costs.output_cost:.6f}")
    cost_columns[2].metric("Estimated total", f"${costs.total_cost:.6f}")
    st.caption("Standard non-batch text pricing; your provider invoice is authoritative.")


with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="brand-mark">CV</div>
            <div><div class="brand-name">Synthetic CVs</div>
            <div class="brand-note">Test data, thoughtfully made</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    dark_mode = st.toggle("Dark mode", key="dark_mode")

apply_theme(dark_mode)

st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-content">
            <div class="eyebrow"><span class="eyebrow-dot"></span> Bring your own API key</div>
            <div class="hero-title">Realistic test CVs, ready in minutes.</div>
            <p class="hero-copy">Build credible US and UK candidate profiles in batches,
            control the career mix, and export polished PDF, DOCX, or text files—without
            storing your key or generated documents.</p>
            <div class="hero-meta">
                <span class="hero-pill">US + UK</span>
                <span class="hero-pill">10 industries</span>
                <span class="hero-pill">PDF · DOCX · TXT</span>
                <span class="hero-pill">OpenAI + Groq</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.divider()
    st.header("How it works")
    st.markdown(
        f"""
        1. Choose a provider and enter your API key.
        2. Select countries, industries, experience, and formats.
        3. Generate and download the result.

        The app uses **{WEB_CONCURRENCY} concurrent requests per session**. API keys
        are sent only to the selected provider and are not written to files, logs,
        caches, or the repository.
        """
    )
    st.warning(
        "Synthetic employment and education histories may mention real organizations. "
        "Use generated CVs only for testing, demos, or other legitimate purposes."
    )

st.markdown('<div class="section-kicker">Generation studio</div>', unsafe_allow_html=True)
st.subheader("Build your batch")
st.caption("Choose the profile mix and file formats. You can adjust every field before generation.")

with st.form("generator_form"):
    provider = st.selectbox(
        "API provider",
        options=list(PROVIDERS),
        format_func=lambda value: PROVIDERS[value]["label"],
    )
    left, right = st.columns(2)
    with left:
        api_key = st.text_input(
            f"{PROVIDERS[provider]['label']} API key",
            type="password",
            help="Used only for this generation request and never persisted by the app.",
        )
    with right:
        model = st.text_input(
            "Model",
            value=PROVIDERS[provider]["default_model"],
            key=f"model_{provider}",
            help="Cost is calculated only for models with verified pricing.",
        )

    count = st.number_input(
        "Number of CVs",
        min_value=1,
        max_value=MAX_RESUMES,
        value=10,
        step=1,
    )

    selection_left, selection_right = st.columns(2)
    with selection_left:
        countries = st.multiselect(
            "Countries",
            options=list(COUNTRIES),
            default=["US"],
            format_func=lambda value: f"{value} — {COUNTRIES[value]['label']}",
        )
        industry_codes = st.multiselect(
            "Industries",
            options=list(INDUSTRIES),
            default=list(INDUSTRIES),
            format_func=lambda value: f"{value} — {INDUSTRIES[value]}",
        )
        output_formats = st.multiselect(
            "Output formats",
            options=list(OUTPUT_FORMATS),
            default=list(OUTPUT_FORMATS),
            format_func=str.upper,
        )
    with selection_right:
        experience_levels = st.multiselect(
            "Experience levels",
            options=list(EXPERIENCE_LEVELS),
            default=list(EXPERIENCE_LEVELS),
        )
        career_progressions = st.multiselect(
            "Career progression",
            options=list(CAREER_PROGRESSIONS),
            default=list(CAREER_PROGRESSIONS),
        )
        distribute = st.checkbox(
            "Balance selected attributes",
            value=True,
            help="Keeps counts across selected values as even as possible.",
        )
        flat = st.checkbox(
            "Flat ZIP layout",
            value=True,
            help="When off, ZIP files use industry/experience/progression folders.",
        )

    with st.expander("Advanced API settings"):
        base_url = st.text_input(
            "Custom OpenAI-compatible base URL",
            value="",
            placeholder=PROVIDERS[provider]["base_url"],
            help="Leave empty to use the selected provider's official endpoint.",
        )

    submitted = st.form_submit_button(
        "Generate CVs",
        type="primary",
        use_container_width=True,
    )

if submitted:
    options = GenerationOptions(
        provider=provider,
        model=model,
        base_url=base_url.strip() or None,
        count=int(count),
        countries=tuple(countries),
        industry_codes=tuple(industry_codes),
        experience_levels=tuple(experience_levels),
        career_progressions=tuple(career_progressions),
        output_formats=tuple(output_formats),
        distribute=distribute,
        flat=flat,
    )
    progress_bar = st.progress(0, text="Preparing generation plan…")

    def update_progress(completed: int, total: int, identifier: str) -> None:
        progress_bar.progress(
            completed / total,
            text=f"Completed {completed} of {total} CVs",
        )

    try:
        with st.spinner("Generating CVs…"):
            generated = ResumeGenerator().generate(
                api_key=api_key,
                options=options,
                progress=update_progress,
            )
    except ValueError as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"Generation could not start: {error}")
    else:
        st.session_state["generation_result"] = generated
        progress_bar.progress(1.0, text="Generation finished")

result = st.session_state.get("generation_result")
if result:
    st.divider()
    successful = len(result.documents)
    if successful:
        st.success(f"Generated {successful} CV{'s' if successful != 1 else ''}.")
    if result.errors:
        with st.expander(f"{len(result.errors)} generation error(s)", expanded=not successful):
            for error in result.errors:
                st.error(error)

    if successful == 1:
        document = result.documents[0]
        st.download_button(
            "Download CV",
            data=document.content,
            file_name=document.relative_path.rsplit("/", 1)[-1],
            mime=document.mime_type,
            type="primary",
            use_container_width=True,
        )
    elif successful > 1:
        st.download_button(
            "Download CV bundle (.zip)",
            data=make_zip(result),
            file_name="synthetic_cvs.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
        with st.expander("Files in bundle"):
            for document in result.documents:
                st.code(document.relative_path, language=None)

    show_usage(result)
