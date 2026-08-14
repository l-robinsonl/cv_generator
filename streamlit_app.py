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
    MAX_WEB_CONCURRENCY,
    OUTPUT_FORMATS,
    PHONE_NUMBER_MODES,
    PROVIDERS,
    WEB_CONCURRENCY,
)
from cv_generator.generator import (
    GenerationOptions,
    GenerationResult,
    ResumeGenerator,
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
            "page": "#F6F8F7", "surface": "#FFFFFF", "raised": "#FBFCFB",
            "sidebar": "#F1F4F2", "text": "#17211C", "muted": "#66736C",
            "border": "#DDE4E0", "border_strong": "#C5D0CA", "accent": "#2D6F57",
            "accent_hover": "#245B48", "accent_text": "#FFFFFF", "soft": "#E4F0EB",
            "hero": "#1E2924", "hero_accent": "#59C9A5",
            "hero_text": "#F8FBF9", "hero_muted": "#C2CEC8",
        },
        "dark": {
            "page": "#101412", "surface": "#171C19", "raised": "#1C231F",
            "sidebar": "#121714", "text": "#EEF3F0", "muted": "#9DA9A2",
            "border": "#2A342E", "border_strong": "#3A483F", "accent": "#67C6A2",
            "accent_hover": "#7AD3B2", "accent_text": "#10241C", "soft": "#20362D",
            "hero": "#1A221E", "hero_accent": "#67C6A2",
            "hero_text": "#F4F8F6", "hero_muted": "#AEBDB5",
        },
    },
    "Petal": {
        "swatches": ("#E1D89F", "#CD8B76", "#C45BAA", "#7D387D", "#27474E"),
        "light": {
            "page": "#F8F7F6", "surface": "#FFFFFF", "raised": "#FCFBFB",
            "sidebar": "#F3F1F0", "text": "#251F23", "muted": "#70676D",
            "border": "#E5E0E3", "border_strong": "#CFC5CB", "accent": "#7A3D74",
            "accent_hover": "#63315E", "accent_text": "#FFFFFF", "soft": "#F1E8EF",
            "hero": "#29252A", "hero_accent": "#CD8B76",
            "hero_text": "#FCFAFB", "hero_muted": "#CDC5CA",
        },
        "dark": {
            "page": "#141214", "surface": "#1B181A", "raised": "#221E21",
            "sidebar": "#171416", "text": "#F3EFF1", "muted": "#AAA0A6",
            "border": "#332D31", "border_strong": "#473C43", "accent": "#D694C9",
            "accent_hover": "#E3A8D8", "accent_text": "#291424", "soft": "#382633",
            "hero": "#211D21", "hero_accent": "#D4A28A",
            "hero_text": "#FAF7F9", "hero_muted": "#BFB4BB",
        },
    },
    "Electric": {
        "swatches": ("#0B3C49", "#731963", "#FFFDFD", "#CBD2D0", "#F0E100"),
        "light": {
            "page": "#F5F7F7", "surface": "#FFFFFF", "raised": "#FBFCFC",
            "sidebar": "#EFF2F2", "text": "#14272C", "muted": "#65757A",
            "border": "#DCE4E6", "border_strong": "#C2D0D3", "accent": "#146074",
            "accent_hover": "#0B4A59", "accent_text": "#FFFFFF", "soft": "#E2EEF1",
            "hero": "#152C33", "hero_accent": "#D5CA16",
            "hero_text": "#F8FBFC", "hero_muted": "#B8C8CC",
        },
        "dark": {
            "page": "#0F1416", "surface": "#151B1E", "raised": "#1B2327",
            "sidebar": "#11171A", "text": "#F0F4F4", "muted": "#9EAAAD",
            "border": "#2A363B", "border_strong": "#3B4A50", "accent": "#69BDD0",
            "accent_hover": "#83CBDB", "accent_text": "#0D252C", "soft": "#1D3339",
            "hero": "#14262C", "hero_accent": "#DDD438",
            "hero_text": "#F5F9FA", "hero_muted": "#AABCC1",
        },
    },
    "Aurora": {
        "swatches": ("#2E0219", "#4A001F", "#6A0F49", "#A7C4C2", "#97EEE9"),
        "light": {
            "page": "#F6F8F8", "surface": "#FFFFFF", "raised": "#FBFCFC",
            "sidebar": "#F0F3F3", "text": "#20181C", "muted": "#687475",
            "border": "#DDE4E4", "border_strong": "#C3D0D0", "accent": "#256A68",
            "accent_hover": "#1C5755", "accent_text": "#FFFFFF", "soft": "#E1F0EF",
            "hero": "#25151E", "hero_accent": "#78D9D4",
            "hero_text": "#FCF9FB", "hero_muted": "#CCBFC6",
        },
        "dark": {
            "page": "#121315", "surface": "#181B1D", "raised": "#1E2325",
            "sidebar": "#151719", "text": "#F1F4F4", "muted": "#A1ABAB",
            "border": "#2E3638", "border_strong": "#424D4F", "accent": "#7BCFCC",
            "accent_hover": "#96DDDA", "accent_text": "#102524", "soft": "#203737",
            "hero": "#22151C", "hero_accent": "#7DDBD7",
            "hero_text": "#FAF7F9", "hero_muted": "#C2B7BD",
        },
    },
    "Neon Lime": {
        "swatches": ("#B6FF3B", "#72FF6A", "#10140D", "#20251C", "#F4FFE7"),
        "light": {
            "page": "#F7FAF3", "surface": "#FFFFFF", "raised": "#FBFDF9",
            "sidebar": "#F0F5EA", "text": "#192014", "muted": "#626D5A",
            "border": "#DDE6D5", "border_strong": "#C3D0B8", "accent": "#3F6F00",
            "accent_hover": "#315700", "accent_text": "#FFFFFF", "soft": "#E9F6D8",
            "hero": "#12180E", "hero_accent": "#B6FF3B",
            "hero_text": "#F7FFE9", "hero_muted": "#C0CFB3",
        },
        "dark": {
            "page": "#0A0D08", "surface": "#11150E", "raised": "#171C13",
            "sidebar": "#0E120C", "text": "#F2F8EC", "muted": "#9FAA98",
            "border": "#293022", "border_strong": "#3B4630", "accent": "#B6FF3B",
            "accent_hover": "#C5FF64", "accent_text": "#142000", "soft": "#26331B",
            "hero": "#0E140A", "hero_accent": "#B6FF3B",
            "hero_text": "#F5FFE8", "hero_muted": "#B6C8A7",
        },
    },
    "Laser Pink": {
        "swatches": ("#FF3CAC", "#784BA0", "#2B86C5", "#10101A", "#F7F0FF"),
        "light": {
            "page": "#F9F7FB", "surface": "#FFFFFF", "raised": "#FCFAFD",
            "sidebar": "#F3EFF7", "text": "#221629", "muted": "#716777",
            "border": "#E6DEEB", "border_strong": "#CEC1D6", "accent": "#A51D70",
            "accent_hover": "#851659", "accent_text": "#FFFFFF", "soft": "#F7E4F0",
            "hero": "#171421", "hero_accent": "#FF5DB7",
            "hero_text": "#FCF8FF", "hero_muted": "#C9C0D0",
        },
        "dark": {
            "page": "#0D0B13", "surface": "#14111D", "raised": "#1B1726",
            "sidebar": "#100D18", "text": "#F6F1FA", "muted": "#ADA3B5",
            "border": "#30293B", "border_strong": "#463952", "accent": "#FF66BC",
            "accent_hover": "#FF85C9", "accent_text": "#2B001B", "soft": "#352039",
            "hero": "#15101F", "hero_accent": "#FF66BC",
            "hero_text": "#FCF7FF", "hero_muted": "#C2B6CA",
        },
    },
    "Cobalt": {
        "swatches": ("#245BFF", "#12B5E5", "#0B163F", "#EFF5FF", "#8EA7FF"),
        "light": {
            "page": "#F6F8FD", "surface": "#FFFFFF", "raised": "#FBFCFF",
            "sidebar": "#EEF2FA", "text": "#111C3E", "muted": "#64708C",
            "border": "#DCE3F2", "border_strong": "#C0CBE1", "accent": "#2450C2",
            "accent_hover": "#193D9B", "accent_text": "#FFFFFF", "soft": "#E7EEFF",
            "hero": "#0E1B49", "hero_accent": "#5B83FF",
            "hero_text": "#F7F9FF", "hero_muted": "#BCC8E8",
        },
        "dark": {
            "page": "#0A0F1E", "surface": "#11182A", "raised": "#172139",
            "sidebar": "#0D1424", "text": "#F1F4FC", "muted": "#A2ACC4",
            "border": "#28344D", "border_strong": "#3A4A6A", "accent": "#7FA0FF",
            "accent_hover": "#9AB4FF", "accent_text": "#0C1734", "soft": "#202E52",
            "hero": "#0D183A", "hero_accent": "#69D6F3",
            "hero_text": "#F6F8FF", "hero_muted": "#AFBCDC",
        },
    },
    "Ember": {
        "swatches": ("#FF6B35", "#F7C548", "#2A1711", "#FFF7F2", "#8C2F16"),
        "light": {
            "page": "#FAF7F5", "surface": "#FFFFFF", "raised": "#FDFBFA",
            "sidebar": "#F5F0ED", "text": "#281B17", "muted": "#756861",
            "border": "#E9DED8", "border_strong": "#D4C2B8", "accent": "#A63D18",
            "accent_hover": "#843013", "accent_text": "#FFFFFF", "soft": "#F9E8E0",
            "hero": "#281711", "hero_accent": "#FF7A49",
            "hero_text": "#FFF9F6", "hero_muted": "#D5C0B7",
        },
        "dark": {
            "page": "#120D0B", "surface": "#1A1310", "raised": "#221915",
            "sidebar": "#160F0D", "text": "#F7F1EE", "muted": "#B0A098",
            "border": "#362821", "border_strong": "#4B382D", "accent": "#FF8A5B",
            "accent_hover": "#FFA17C", "accent_text": "#321105", "soft": "#3A231A",
            "hero": "#21130E", "hero_accent": "#FF8A5B",
            "hero_text": "#FFF8F4", "hero_muted": "#CEB7AC",
        },
    },
    "Ultraviolet": {
        "swatches": ("#7C3AED", "#A855F7", "#22D3EE", "#160B2E", "#F5F0FF"),
        "light": {
            "page": "#F8F6FC", "surface": "#FFFFFF", "raised": "#FCFAFF",
            "sidebar": "#F1EDF8", "text": "#211533", "muted": "#6E647C",
            "border": "#E2DCEE", "border_strong": "#C9BDE0", "accent": "#6D28D9",
            "accent_hover": "#5620AE", "accent_text": "#FFFFFF", "soft": "#EEE7FB",
            "hero": "#1B0E36", "hero_accent": "#22D3EE",
            "hero_text": "#FBF8FF", "hero_muted": "#C8B9DD",
        },
        "dark": {
            "page": "#0C0815", "surface": "#130E21", "raised": "#1A132B",
            "sidebar": "#100A1B", "text": "#F5F0FC", "muted": "#AAA0BA",
            "border": "#2E2442", "border_strong": "#44345F", "accent": "#B58AFF",
            "accent_hover": "#C5A5FF", "accent_text": "#21113F", "soft": "#2C2047",
            "hero": "#170C2D", "hero_accent": "#22D3EE",
            "hero_text": "#FAF7FF", "hero_muted": "#BEAFD3",
        },
    },
    "Solar": {
        "swatches": ("#F6C90E", "#FF8F00", "#3B2F00", "#FFF9E6", "#5A3D00"),
        "light": {
            "page": "#FAF9F4", "surface": "#FFFFFF", "raised": "#FDFCF9",
            "sidebar": "#F5F2E8", "text": "#282310", "muted": "#746D55",
            "border": "#E8E2CF", "border_strong": "#D1C6A6", "accent": "#7A5700",
            "accent_hover": "#604500", "accent_text": "#FFFFFF", "soft": "#FAF0CF",
            "hero": "#272008", "hero_accent": "#F6C90E",
            "hero_text": "#FFFCED", "hero_muted": "#D5CDAE",
        },
        "dark": {
            "page": "#111008", "surface": "#19170D", "raised": "#211E11",
            "sidebar": "#151309", "text": "#F7F4E8", "muted": "#AEA994",
            "border": "#34301C", "border_strong": "#494326", "accent": "#F6C90E",
            "accent_hover": "#FFDA3D", "accent_text": "#282000", "soft": "#332D14",
            "hero": "#201A07", "hero_accent": "#F6C90E",
            "hero_text": "#FFFBE9", "hero_muted": "#CBC3A1",
        },
    },
    "Ocean": {
        "swatches": ("#00B8D9", "#0077B6", "#023047", "#90E0EF", "#CAF0F8"),
        "light": {
            "page": "#F4F9FA", "surface": "#FFFFFF", "raised": "#FAFDFD",
            "sidebar": "#EDF5F7", "text": "#102A33", "muted": "#61757B",
            "border": "#D7E7EA", "border_strong": "#BAD2D8", "accent": "#006B85",
            "accent_hover": "#00546A", "accent_text": "#FFFFFF", "soft": "#E1F4F7",
            "hero": "#082D3A", "hero_accent": "#4FD3E8",
            "hero_text": "#F4FCFE", "hero_muted": "#B5CFD7",
        },
        "dark": {
            "page": "#071116", "surface": "#0C1A20", "raised": "#11242B",
            "sidebar": "#09161C", "text": "#EDF7F9", "muted": "#9DAEB3",
            "border": "#25373D", "border_strong": "#35505A", "accent": "#55D1E5",
            "accent_hover": "#76DCEB", "accent_text": "#08242B", "soft": "#17323A",
            "hero": "#092630", "hero_accent": "#55D1E5",
            "hero_text": "#F1FBFD", "hero_muted": "#AAC5CC",
        },
    },
    "Monochrome": {
        "swatches": ("#0A0A0A", "#4A4A4A", "#A0A0A0", "#E8E8E8", "#FFFFFF"),
        "light": {
            "page": "#F7F7F7", "surface": "#FFFFFF", "raised": "#FBFBFB",
            "sidebar": "#F1F1F1", "text": "#171717", "muted": "#686868",
            "border": "#E0E0E0", "border_strong": "#C7C7C7", "accent": "#252525",
            "accent_hover": "#0F0F0F", "accent_text": "#FFFFFF", "soft": "#EAEAEA",
            "hero": "#111111", "hero_accent": "#E8E8E8",
            "hero_text": "#FAFAFA", "hero_muted": "#BEBEBE",
        },
        "dark": {
            "page": "#0B0B0B", "surface": "#131313", "raised": "#1A1A1A",
            "sidebar": "#0F0F0F", "text": "#F2F2F2", "muted": "#A6A6A6",
            "border": "#2B2B2B", "border_strong": "#414141", "accent": "#F2F2F2",
            "accent_hover": "#FFFFFF", "accent_text": "#111111", "soft": "#2D2D2D",
            "hero": "#101010", "hero_accent": "#F2F2F2",
            "hero_text": "#FAFAFA", "hero_muted": "#BDBDBD",
        },
    },
}


def apply_theme(theme_name: str, dark_mode: bool) -> None:
    """Apply one of the app's accessible light/dark palette pairs."""
    palette = THEMES[theme_name]["dark" if dark_mode else "light"]
    color_scheme = "dark" if dark_mode else "light"
    shadow = "rgba(0,0,0,.20)" if dark_mode else "rgba(23,33,28,.07)"
    appearance_icon_color = "#DCEBFF" if dark_mode else "#E49B0F"
    appearance_focus = (
        "rgba(176, 207, 255, .45)" if dark_mode else "rgba(228, 155, 15, .35)"
    )
    st.markdown(
        f"""
        <style>
        :root {{
            color-scheme: {color_scheme};
            --primary-color: {palette['accent']};
        }}
        .stApp {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: {palette['text']};
            background: {palette['page']};
        }}
        [data-testid="stMainBlockContainer"], .main .block-container {{
            width: 100%;
            max-width: 1480px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }}
        [data-testid="stHeader"] {{ background: {palette['page']}; }}
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
            grid-template-columns: minmax(0, 1fr);
            gap: clamp(2rem, 5vw, 5rem);
            align-items: center;
            padding: clamp(2rem, 4vw, 3rem);
            margin: 0 0 1.75rem;
            border: 1px solid {palette['border_strong']};
            border-radius: 20px;
            background: {palette['hero']};
            box-shadow: 0 14px 34px {shadow};
        }}
        .hero-shell::before {{
            content: "";
            position: absolute;
            inset: 0 0 auto;
            height: 3px;
            background: {palette['hero_accent']};
            pointer-events: none;
        }}
        .hero-content {{ position: relative; z-index: 1; max-width: 680px; }}
        .eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: {palette['hero_accent']};
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}
        .eyebrow-dot {{
            width: 0.48rem;
            height: 0.48rem;
            border-radius: 50%;
            background: {palette['hero_accent']};
        }}
        .hero-title {{
            max-width: 620px;
            margin: 0.85rem 0 0.75rem;
            color: {palette['hero_text']};
            font-size: clamp(2.2rem, 4vw, 3.65rem);
            font-weight: 760;
            line-height: 1.02;
            letter-spacing: -0.045em;
        }}
        .hero-copy {{
            max-width: 620px;
            margin: 0;
            color: {palette['hero_muted']};
            font-size: 1rem;
            line-height: 1.6;
        }}
        .hero-meta {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.2rem; }}
        .hero-pill {{
            display: inline-flex;
            padding: 0.38rem 0.65rem;
            border: 1px solid {palette['border_strong']};
            border-radius: 999px;
            color: {palette['hero_muted']};
            background: transparent;
            font-size: 0.76rem;
            font-weight: 600;
        }}
        .side-brand {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.1rem; }}
        .brand-mark {{
            display: grid;
            width: 2.45rem;
            height: 2.45rem;
            place-items: center;
            border-radius: 10px;
            color: {palette['accent_text']};
            background: {palette['accent']};
            font-weight: 800;
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
        .palette-swatches {{ display: grid; grid-template-columns: repeat(5, 1fr); height: .25rem; overflow: hidden; border-radius: 99px; margin: -.35rem 0 .8rem; opacity: .72; }}
        .side-note {{
            margin-top: 1rem;
            padding: .85rem .9rem;
            border: 1px solid {palette['border']};
            border-radius: 10px;
            color: {palette['muted']};
            background: {palette['surface']};
            font-size: .78rem;
            line-height: 1.55;
        }}
        .st-key-generation_panel {{
            padding: clamp(1.2rem, 2.5vw, 1.75rem);
            border: 1px solid {palette['border']};
            border-radius: 16px;
            background: {palette['surface']};
            box-shadow: 0 10px 28px {shadow};
        }}
        .st-key-phone_mode [role="radiogroup"] {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: .65rem; }}
        .st-key-phone_mode [data-baseweb="radio"] {{
            min-height: 4.6rem;
            margin: 0;
            padding: .68rem .8rem;
            border: 1px solid {palette['border']};
            border-radius: 10px;
            background: {palette['raised']};
        }}
        .st-key-phone_mode [data-baseweb="radio"]:has(input:checked) {{
            border-color: {palette['accent']};
            background: {palette['soft']};
            box-shadow: none;
        }}
        .st-key-remainder_panel {{
            margin-top: .35rem;
            padding: 1rem 1.1rem;
            border: 1px solid {palette['border']};
            border-radius: 12px;
            background: {palette['raised']};
        }}
        .st-key-remainder_mode [role="radiogroup"] {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: .65rem; }}
        .st-key-remainder_mode [data-baseweb="radio"] {{
            min-height: 4.2rem;
            margin: 0;
            padding: .65rem .75rem;
            border: 1px solid {palette['border']};
            border-radius: 10px;
            background: {palette['surface']};
        }}
        .st-key-remainder_mode [data-baseweb="radio"]:has(input:checked) {{
            border-color: {palette['accent']};
            background: {palette['soft']};
        }}
        [data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked) > div:first-of-type {{
            background-color: {palette['accent']} !important;
        }}
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input {{
            color: {palette['text']} !important;
            background: {palette['raised']} !important;
            border-color: {palette['border']} !important;
        }}
        div[data-baseweb="select"]:focus-within > div,
        div[data-baseweb="input"]:focus-within > div,
        [data-testid="stNumberInput"]:focus-within,
        [data-testid="stTextInput"]:focus-within {{
            border-color: {palette['accent']} !important;
            box-shadow: 0 0 0 2px {palette['soft']} !important;
        }}
        [data-baseweb="tag"] {{
            color: {palette['accent']} !important;
            background: {palette['soft']} !important;
            border: 1px solid {palette['border']} !important;
        }}
        [data-baseweb="tag"] * {{
            color: {palette['accent']} !important;
            fill: {palette['accent']} !important;
        }}
        [data-baseweb="popover"],
        [data-baseweb="popover"] > div,
        [data-testid="stPopoverBody"],
        [data-testid="stPopoverBody"] div,
        [data-testid="stPopoverBody"] [data-testid="stVerticalBlock"],
        [data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"],
        [data-baseweb="menu"],
        [data-baseweb="menu"] > *,
        [role="listbox"],
        [role="listbox"] > * {{
            color: {palette['text']} !important;
            background-color: {palette['raised']} !important;
        }}
        [data-testid="stPopoverBody"] p,
        [data-testid="stPopoverBody"] strong {{
            color: {palette['text']} !important;
        }}
        [data-testid="stPopoverBody"] code {{
            color: {palette['accent']} !important;
            background-color: {palette['soft']} !important;
        }}
        [data-baseweb="menu"] *:not(svg),
        [role="listbox"] *:not(svg),
        [role="option"],
        [role="option"] * {{ color: {palette['text']} !important; }}
        [role="option"]:hover,
        [role="option"]:hover * {{
            color: {palette['accent']} !important;
            background-color: {palette['soft']} !important;
        }}
        [role="option"][aria-selected="true"],
        [role="option"][aria-selected="true"] * {{
            color: {palette['accent']} !important;
            background-color: {palette['soft']} !important;
        }}
        [data-testid="stCheckbox"] [data-baseweb="checkbox"]:has(input:checked) > span {{
            border-color: {palette['accent']} !important;
            background-color: {palette['accent']} !important;
        }}
        .st-key-appearance_toggle [data-testid="stButton"] button {{
            width: 2.5rem;
            min-width: 2.5rem;
            min-height: 2.5rem;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 50%;
            color: {appearance_icon_color} !important;
            background: transparent !important;
            box-shadow: none !important;
            font-size: 1.65rem;
            line-height: 1;
        }}
        .st-key-appearance_toggle [data-testid="stButton"] button * {{
            color: {appearance_icon_color} !important;
        }}
        .st-key-appearance_toggle [data-testid="stButton"] button:hover {{
            color: {appearance_icon_color} !important;
            background: transparent !important;
            transform: scale(1.1);
        }}
        .st-key-appearance_toggle [data-testid="stButton"] button:focus-visible {{
            outline: 2px solid {appearance_focus} !important;
            outline-offset: 2px;
            background: transparent !important;
        }}
        [data-baseweb="progress-bar"] > div > div > div {{
            background-color: {palette['accent']} !important;
        }}
        [data-testid="stSpinner"] svg {{
            color: {palette['accent']} !important;
            fill: {palette['accent']} !important;
        }}
        [data-testid="stPopover"] button {{
            min-height: 2.35rem;
            border-color: {palette['border']} !important;
            color: {palette['text']} !important;
            background: {palette['raised']} !important;
        }}
        [data-testid="stPopover"] button:hover {{
            border-color: {palette['accent']} !important;
            color: {palette['accent']} !important;
        }}
        [data-testid="stButton"] button,
        [data-testid="stDownloadButton"] button {{
            min-height: 3rem;
            border: 0;
            border-radius: 10px;
            color: {palette['accent_text']} !important;
            background: {palette['accent']} !important;
            box-shadow: none;
            font-weight: 700;
            transition: background 150ms ease, transform 150ms ease;
        }}
        [data-testid="stButton"] button *,
        [data-testid="stDownloadButton"] button * {{
            color: {palette['accent_text']} !important;
        }}
        [data-testid="stButton"] button:hover,
        [data-testid="stDownloadButton"] button:hover {{
            background: {palette['accent_hover']} !important;
            transform: translateY(-1px);
        }}
        [data-testid="stMetric"] {{
            padding: 1rem;
            border: 1px solid {palette['border']};
            border-radius: 12px;
            background: {palette['surface']};
        }}
        [data-testid="stExpander"], [data-testid="stAlert"] {{
            border-color: {palette['border']};
            border-radius: 10px;
        }}
        hr {{ border-color: {palette['border']} !important; }}
        .stCaption, [data-testid="stCaptionContainer"], small {{ color: {palette['muted']} !important; }}
        @media (max-width: 900px) {{
            .st-key-phone_mode [role="radiogroup"] {{ grid-template-columns: 1fr; }}
        }}
        @media (max-width: 640px) {{
            [data-testid="stMainBlockContainer"], .main .block-container {{ padding-top: 1rem; }}
            .hero-shell {{ border-radius: 14px; padding: 1.4rem; }}
            .hero-title {{ font-size: 2.2rem; }}
            .st-key-generation_panel {{ border-radius: 12px; padding: 1rem; }}
            .st-key-phone_mode [role="radiogroup"] {{ grid-template-columns: 1fr; }}
            .st-key-remainder_mode [role="radiogroup"] {{ grid-template-columns: 1fr; }}
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
    if "appearance_mode" not in st.session_state:
        st.session_state.appearance_mode = (
            "dark" if st.session_state.get("dark_mode", False) else "light"
        )
    dark_mode = st.session_state.appearance_mode == "dark"
    appearance_icon = "☾" if dark_mode else "☀"
    appearance_help = (
        "Switch to light appearance" if dark_mode else "Switch to dark appearance"
    )
    if st.button(
        appearance_icon,
        key="appearance_toggle",
        help=appearance_help,
        type="tertiary",
    ):
        st.session_state.appearance_mode = "light" if dark_mode else "dark"
        st.rerun()

apply_theme(theme_name, dark_mode)

st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-content">
            <div class="eyebrow"><span class="eyebrow-dot"></span> Candidate data studio</div>
            <div class="hero-title">Synthetic CVs for serious testing.</div>
            <p class="hero-copy">Create credible US and UK profiles in batches, route selected
            candidates through automated demo conversations, and export production-ready files.</p>
            <div class="hero-meta">
                <span class="hero-pill">US + UK</span>
                <span class="hero-pill">Demo-ready +210</span>
                <span class="hero-pill">PDF · DOCX · TXT</span>
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
        2. Select countries, phone routing, profile mix, and formats.
        3. Generate and download the result.

        You can run **1–{MAX_WEB_CONCURRENCY} concurrent requests**. The default is
        **{WEB_CONCURRENCY}**. API keys are sent only to the selected provider and are
        not written to files, logs, caches, or the repository.
        """
    )
    st.markdown(
        """
        <div class="side-note"><strong>Use responsibly.</strong><br>
        Synthetic histories may mention real organisations. Generated CVs are for testing,
        demos, and other legitimate uses only.</div>
        """,
        unsafe_allow_html=True,
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

    batch_left, batch_right = st.columns(2)
    with batch_left:
        count = st.number_input(
            "Number of CVs",
            min_value=1,
            max_value=MAX_RESUMES,
            value=10,
            step=1,
        )
    with batch_right:
        concurrency = st.number_input(
            "Concurrent requests",
            min_value=1,
            max_value=MAX_WEB_CONCURRENCY,
            value=WEB_CONCURRENCY,
            step=1,
            help=(
                "Higher values can finish batches faster, but provider rate limits may "
                "cause requests to fail."
            ),
        )
    if concurrency > 10:
        st.warning(
            "High concurrency may trigger provider rate limits. If requests fail, reduce "
            "this value and try again."
        )

    st.markdown("#### Candidate countries")
    countries = st.multiselect(
        "Countries",
        options=list(COUNTRIES),
        default=["US"],
        format_func=lambda value: f"{value} — {COUNTRIES[value]['label']}",
        label_visibility="collapsed",
    )

    st.markdown("#### Phone routing")
    phone_number_mode = st.radio(
        "Number source",
        options=list(PHONE_NUMBER_MODES),
        format_func=lambda value: PHONE_NUMBER_MODES[value],
        captions=(
            "Reserved fictional range matched to each CV country.",
            "Every CV gets a different +210 auto-response number.",
            "Choose an exact demo count and how to number the remainder.",
        ),
        horizontal=True,
        key="phone_mode",
        label_visibility="collapsed",
    )
    reserved_phone_country = None
    if phone_number_mode == "mixed":
        with st.container(key="remainder_panel"):
            demo_limit = max(1, int(count) - 1)
            demo_number_count = st.number_input(
                "Number of unique demo numbers",
                min_value=1,
                max_value=demo_limit,
                value=min(3, demo_limit),
                step=1,
                help="These are assigned randomly within the batch; each one is unique.",
            )
            if count == 1:
                st.warning("Increase the batch size to at least 2 to use a fixed allocation.")
            remainder_mode = st.radio(
                "Country-reserved remainder",
                options=("selected", "single"),
                format_func=lambda value: {
                    "selected": "Selected-country mix",
                    "single": "One reserved country",
                }[value],
                captions=(
                    "Each remaining number matches its CV's assigned country.",
                    "Every remaining number comes from one country you choose.",
                ),
                horizontal=True,
                key="remainder_mode",
                label_visibility="visible",
            )
            if remainder_mode == "single":
                reserved_phone_country = st.selectbox(
                    "Reserved-number country",
                    options=list(countries) or list(COUNTRIES),
                    format_func=lambda value: COUNTRIES[value]["label"],
                    help="Only the phone-number range is fixed; CV locations still follow the profile mix.",
                )
    else:
        demo_number_count = 0
        if phone_number_mode == "local":
            with st.popover("ⓘ Number examples"):
                st.markdown(
                    """
                    **United States**

                    `+1 202-555-01XX`

                    **United Kingdom**

                    `+44 7700 900XXX`
                    """
                )

    st.markdown("#### Profile details")
    selection_left, selection_right = st.columns(2)
    with selection_left:
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
        reserved_phone_country=reserved_phone_country,
        concurrency=int(concurrency),
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
