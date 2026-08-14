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
    PHONE_NUMBER_MODES,
    PROVIDERS,
    WEB_CONCURRENCY,
)
from cv_generator.generator import (
    GenerationOptions,
    GenerationResult,
    ResumeGenerator,
    is_demo_phone,
)


st.set_page_config(
    page_title="Synthetic CV Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


THEMES = {
    "Mint": {
        "swatches": ("#56E39F", "#59C9A5", "#5B6C5D", "#3B2C35", "#2A1F2D"),
        "light": {
            "page": "#F1F6F3", "surface": "#FCFEFD", "raised": "#FFFFFF",
            "sidebar": "#E5EFE9", "text": "#2A1F2D", "muted": "#5B6C5D",
            "border": "rgba(42,31,45,.14)", "accent": "#1B7257",
            "accent_2": "#315F51", "bright": "#56E39F", "soft": "rgba(89,201,165,.14)",
            "hero_a": "#2A1F2D", "hero_b": "#40594B", "button_text": "#FFFFFF",
        },
        "dark": {
            "page": "#171218", "surface": "#211922", "raised": "#2A1F2D",
            "sidebar": "#1B151C", "text": "#F3F8F5", "muted": "#A6B8AD",
            "border": "rgba(86,227,159,.18)", "accent": "#56E39F",
            "accent_2": "#59C9A5", "bright": "#56E39F", "soft": "rgba(86,227,159,.12)",
            "hero_a": "#2A1F2D", "hero_b": "#3B2C35", "button_text": "#16251D",
        },
    },
    "Petal": {
        "swatches": ("#E1D89F", "#CD8B76", "#C45BAA", "#7D387D", "#27474E"),
        "light": {
            "page": "#FBF8F0", "surface": "#FFFEFB", "raised": "#FFFFFF",
            "sidebar": "#F0E9D1", "text": "#27474E", "muted": "#71645F",
            "border": "rgba(39,71,78,.15)", "accent": "#913E82",
            "accent_2": "#7D387D", "bright": "#E1D89F", "soft": "rgba(196,91,170,.12)",
            "hero_a": "#27474E", "hero_b": "#7D387D", "button_text": "#FFFFFF",
        },
        "dark": {
            "page": "#181316", "surface": "#241B23", "raised": "#30222E",
            "sidebar": "#20171F", "text": "#FBF8F0", "muted": "#D0C3BD",
            "border": "rgba(225,216,159,.18)", "accent": "#E58CCE",
            "accent_2": "#CD8B76", "bright": "#E1D89F", "soft": "rgba(196,91,170,.14)",
            "hero_a": "#27474E", "hero_b": "#7D387D", "button_text": "#271523",
        },
    },
    "Electric": {
        "swatches": ("#0B3C49", "#731963", "#FFFDFD", "#CBD2D0", "#F0E100"),
        "light": {
            "page": "#F4F7F6", "surface": "#FFFDFD", "raised": "#FFFFFF",
            "sidebar": "#E7ECEB", "text": "#0B3C49", "muted": "#526467",
            "border": "rgba(11,60,73,.16)", "accent": "#651657",
            "accent_2": "#0B3C49", "bright": "#F0E100", "soft": "rgba(240,225,0,.16)",
            "hero_a": "#0B3C49", "hero_b": "#731963", "button_text": "#FFFFFF",
        },
        "dark": {
            "page": "#071F26", "surface": "#0B303A", "raised": "#123D47",
            "sidebar": "#092932", "text": "#FFFDFD", "muted": "#CBD2D0",
            "border": "rgba(240,225,0,.18)", "accent": "#F0E100",
            "accent_2": "#D2C600", "bright": "#F0E100", "soft": "rgba(240,225,0,.11)",
            "hero_a": "#501147", "hero_b": "#0B3C49", "button_text": "#0B3038",
        },
    },
    "Aurora": {
        "swatches": ("#2E0219", "#4A001F", "#6A0F49", "#A7C4C2", "#97EEE9"),
        "light": {
            "page": "#F2F8F8", "surface": "#FCFFFF", "raised": "#FFFFFF",
            "sidebar": "#DFECEB", "text": "#2E0219", "muted": "#526C6A",
            "border": "rgba(46,2,25,.14)", "accent": "#6A0F49",
            "accent_2": "#315F5D", "bright": "#97EEE9", "soft": "rgba(151,238,233,.20)",
            "hero_a": "#2E0219", "hero_b": "#6A0F49", "button_text": "#FFFFFF",
        },
        "dark": {
            "page": "#18010D", "surface": "#250217", "raised": "#2E0219",
            "sidebar": "#200111", "text": "#F5FAF9", "muted": "#A7C4C2",
            "border": "rgba(151,238,233,.18)", "accent": "#97EEE9",
            "accent_2": "#62C6C2", "bright": "#97EEE9", "soft": "rgba(151,238,233,.12)",
            "hero_a": "#4A001F", "hero_b": "#6A0F49", "button_text": "#210312",
        },
    },
}


def apply_theme(theme_name: str, dark_mode: bool) -> None:
    """Apply one of the app's accessible light/dark palette pairs."""
    palette = THEMES[theme_name]["dark" if dark_mode else "light"]
    color_scheme = "dark" if dark_mode else "light"
    shadow = "rgba(8,3,8,.34)" if dark_mode else "rgba(42,31,45,.10)"
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: {color_scheme}; }}
        .stApp {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
        .stApp {{
            color: {palette['text']};
            background:
                radial-gradient(circle at 86% 2%, {palette['soft']} 0, transparent 28rem),
                radial-gradient(circle at 8% 52%, {palette['soft']} 0, transparent 34rem),
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
            display: grid;
            grid-template-columns: minmax(0, 1.55fr) minmax(240px, .7fr);
            gap: clamp(1.5rem, 4vw, 4rem);
            align-items: end;
            padding: clamp(1.7rem, 4vw, 3.4rem);
            margin: 0.35rem 0 1.35rem;
            border: 1px solid rgba(255,255,255,.10);
            border-radius: 30px;
            background: linear-gradient(135deg, {palette['hero_a']} 0%, {palette['hero_b']} 100%);
            box-shadow: 0 26px 74px {shadow};
        }}
        .hero-shell::before {{
            content: "";
            position: absolute;
            width: 24rem;
            height: 24rem;
            right: -9rem;
            top: -12rem;
            border-radius: 50%;
            background: {palette['bright']};
            opacity: .14;
            filter: blur(1px);
            pointer-events: none;
        }}
        .hero-content {{ position: relative; z-index: 1; max-width: 720px; }}
        .eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: {palette['bright']};
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }}
        .eyebrow-dot {{
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 50%;
            background: {palette['bright']};
            box-shadow: 0 0 0 5px rgba(255,255,255,.10);
        }}
        .hero-title {{
            max-width: 700px;
            margin: 1rem 0 0.8rem;
            color: #FFFFFF;
            font-size: clamp(2.35rem, 5vw, 4.7rem);
            font-weight: 790;
            line-height: .96;
            letter-spacing: -0.055em;
        }}
        .hero-copy {{
            max-width: 650px;
            margin: 0;
            color: rgba(255,255,255,.78);
            font-size: 1.04rem;
            line-height: 1.65;
        }}
        .hero-meta {{ display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1.35rem; }}
        .hero-pill {{
            display: inline-flex;
            padding: 0.42rem 0.72rem;
            border: 1px solid rgba(255,255,255,.14);
            border-radius: 999px;
            color: rgba(255,255,255,.84);
            background: rgba(255,255,255,.07);
            font-size: 0.8rem;
            font-weight: 650;
        }}
        .route-card {{
            position: relative;
            z-index: 1;
            padding: 1.15rem;
            border: 1px solid rgba(255,255,255,.16);
            border-radius: 19px;
            background: rgba(255,255,255,.09);
            backdrop-filter: blur(10px);
        }}
        .route-label {{ color: rgba(255,255,255,.58); font-size: .72rem; font-weight: 750; letter-spacing: .11em; text-transform: uppercase; }}
        .route-number {{ margin: .55rem 0 1rem; color: #FFFFFF; font-size: 1.15rem; font-weight: 750; letter-spacing: .02em; }}
        .route-status {{ display: flex; align-items: center; gap: .5rem; color: rgba(255,255,255,.78); font-size: .8rem; }}
        .status-light {{ width: .55rem; height: .55rem; border-radius: 50%; background: {palette['bright']}; box-shadow: 0 0 0 4px rgba(255,255,255,.09); }}
        .side-brand {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.1rem; }}
        .brand-mark {{
            display: grid;
            width: 2.6rem;
            height: 2.6rem;
            place-items: center;
            border-radius: 13px;
            color: {palette['button_text']};
            background: linear-gradient(145deg, {palette['accent']}, {palette['accent_2']});
            box-shadow: 0 8px 20px {shadow};
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
        .palette-swatches {{ display: grid; grid-template-columns: repeat(5, 1fr); height: .42rem; overflow: hidden; border-radius: 99px; margin: -.4rem 0 .75rem; }}
        .st-key-generation_panel {{
            padding: clamp(1.15rem, 3vw, 2rem);
            border: 1px solid {palette['border']};
            border-radius: 22px;
            background: {palette['surface']};
            box-shadow: 0 18px 50px {shadow};
        }}
        .st-key-phone_mode [role="radiogroup"] {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: .65rem; }}
        .st-key-phone_mode [role="radiogroup"] label {{
            min-height: 3.1rem;
            margin: 0;
            padding: .75rem .85rem;
            border: 1px solid {palette['border']};
            border-radius: 13px;
            background: {palette['raised']};
        }}
        .st-key-phone_mode [role="radiogroup"] label:has(input:checked) {{
            border-color: {palette['accent']};
            background: {palette['soft']};
            box-shadow: inset 0 0 0 1px {palette['accent']};
        }}
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input {{
            color: {palette['text']} !important;
            background: {palette['raised']} !important;
            border-color: {palette['border']} !important;
        }}
        div[data-baseweb="tag"] {{
            color: {palette['text']} !important;
            background: {palette['soft']} !important;
        }}
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"] {{
            color: {palette['text']} !important;
            background: {palette['raised']} !important;
        }}
        li[role="option"] {{ color: {palette['text']} !important; }}
        li[role="option"]:hover {{ background: {palette['soft']} !important; }}
        [data-testid="stCheckbox"] svg,
        [data-testid="stToggle"] svg {{ color: {palette['accent']} !important; }}
        [data-testid="stButton"] button,
        [data-testid="stDownloadButton"] button {{
            min-height: 3rem;
            border: 0;
            border-radius: 13px;
            color: {palette['button_text']} !important;
            background: linear-gradient(120deg, {palette['accent']}, {palette['accent_2']});
            box-shadow: 0 10px 24px {shadow};
            font-weight: 760;
            transition: transform 150ms ease, box-shadow 150ms ease, filter 150ms ease;
        }}
        [data-testid="stButton"] button:hover,
        [data-testid="stDownloadButton"] button:hover {{
            filter: brightness(1.06);
            transform: translateY(-1px);
            box-shadow: 0 14px 30px {shadow};
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
            .hero-shell {{ grid-template-columns: 1fr; border-radius: 20px; padding: 1.4rem; }}
            .hero-title {{ font-size: 2.35rem; }}
            .route-card {{ display: none; }}
            .st-key-generation_panel {{ border-radius: 18px; padding: 1rem; }}
            .st-key-phone_mode [role="radiogroup"] {{ grid-template-columns: 1fr; }}
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
    theme_name = st.selectbox("Colour theme", options=list(THEMES), key="theme_name")
    swatches = "".join(
        f'<span style="background:{colour}"></span>'
        for colour in THEMES[theme_name]["swatches"]
    )
    st.markdown(
        f'<div class="palette-swatches">{swatches}</div>',
        unsafe_allow_html=True,
    )
    dark_mode = st.toggle("Dark appearance", key="dark_mode")

apply_theme(theme_name, dark_mode)

st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-content">
            <div class="eyebrow"><span class="eyebrow-dot"></span> Synthetic candidate studio</div>
            <div class="hero-title">Test people.<br>Real conversations.</div>
            <p class="hero-copy">Build credible US and UK candidate profiles in batches,
            route selected profiles through automated demo conversations, and export polished
            files—without storing your key or generated documents.</p>
            <div class="hero-meta">
                <span class="hero-pill">US + UK</span>
                <span class="hero-pill">Demo-ready +210</span>
                <span class="hero-pill">PDF · DOCX · TXT</span>
            </div>
        </div>
        <div class="route-card">
            <div class="route-label">Demo route</div>
            <div class="route-number">+210000000000</div>
            <div class="route-status"><span class="status-light"></span> Auto-response ready</div>
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
        2. Select countries, phone routing, profile mix, and formats.
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

with st.container(key="generation_panel"):
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

    st.markdown("#### Phone routing")
    phone_number_mode = st.radio(
        "Number source",
        options=list(PHONE_NUMBER_MODES),
        format_func=lambda value: PHONE_NUMBER_MODES[value],
        horizontal=True,
        key="phone_mode",
        label_visibility="collapsed",
    )
    phone_mode_copy = {
        "local": (
            "Every profile gets a fictional number reserved for its selected country. "
            "These are safe for display but are not messageable."
        ),
        "demo": (
            "Every profile gets its own unique **+210** number recognized by the chat server, "
            "so all generated conversations can auto-respond."
        ),
        "shared_demo": (
            "Every profile gets the same **+210** demo number that you provide. "
            "Use this when an entire batch should route to one shared conversation identity."
        ),
        "mixed": (
            "A fixed number of randomly selected profiles get unique **+210** demo numbers; "
            "the remainder use country-reserved numbers."
        ),
    }
    st.caption(phone_mode_copy[phone_number_mode])
    shared_demo_number = None
    if phone_number_mode == "mixed":
        demo_number_count = st.number_input(
            "Number of demo-ready CVs",
            min_value=1,
            max_value=MAX_RESUMES,
            value=min(3, int(count)),
            step=1,
            help="Must not exceed the total batch size. Assignment is random within the batch.",
        )
        if demo_number_count > count:
            st.warning(f"Choose {int(count)} or fewer demo-ready CVs for this batch.")
    elif phone_number_mode == "shared_demo":
        shared_demo_number = st.text_input(
            "Shared demo number",
            placeholder="+210000000000",
            help="Must be +210 followed by exactly 9 digits.",
        ).strip()
        if shared_demo_number and not is_demo_phone(shared_demo_number):
            st.error("Must be +210 followed by 9 digits (for example, +210000000000).")
        demo_number_count = 0
    else:
        demo_number_count = 0

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

    submitted = st.button(
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
        phone_number_mode=phone_number_mode,
        demo_number_count=int(demo_number_count),
        shared_demo_number=shared_demo_number,
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
