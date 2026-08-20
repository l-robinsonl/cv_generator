# Synthetic CV Generator

A public Streamlit app for generating batches of realistic synthetic CVs with your own
OpenAI or Groq API key. Select the countries, industries, experience levels, career
progression, output formats, and ZIP layout from the browser.

The app supports:

- United States and United Kingdom CVs, with officially reserved fictional phone
  number ranges; UK CVs use mobile numbers only and never landlines
- Three clear phone-routing modes: country-reserved numbers, unique `+210` demo
  numbers for every CV, or an exact demo allocation with the remainder drawn from
  the selected-country mix or one chosen country's reserved range
- Twelve selectable colour themes, from restrained palettes to neon colourways, each
  with purpose-designed light and dark variants
- OpenAI (default: `gpt-4.1-mini`) and Groq, plus a custom OpenAI-compatible base URL
- Ten numbered industries, with separate Sales and Marketing selections
- Optional pasted or uploaded (TXT, Markdown, DOCX, or PDF) job descriptions, with
  an exact user-selected mix of good and intentionally poor matches
- PDF, DOCX, TXT, or a balanced/random mix
- Flat or industry/experience/progression ZIP layouts
- Balanced or random attribute distribution
- Input/output token totals and estimated cost breakdowns
- User-selectable request concurrency from 1 to 20, defaulting to 5

## Run locally

Python 3.12 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Enter your provider key in the app. Do not put API keys in the repository or in
`.streamlit/secrets.toml` for a public deployment.

## Industry codes

| Code | Industry |
| ---: | --- |
| 1 | Healthcare |
| 2 | IT and Technology |
| 3 | Professional Service and Finance |
| 4 | Education |
| 5 | Sales and Business Development |
| 6 | Marketing and Communications |
| 7 | Engineering and Manufacturing |
| 8 | Human Resources and Recruitment |
| 9 | Retail and Hospitality |
| 10 | Construction and Skilled Trades |

## Deploy on Streamlit Community Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub.
2. Choose **Create app** and select this repository.
3. Set the branch to `main` and the entrypoint to `streamlit_app.py`.
4. Leave secrets empty: this app intentionally uses a key supplied by each user.
5. Deploy.

Streamlit installs the pinned Python packages in `requirements.txt`. The app does
not require system packages or a database.

## Privacy and responsible use

API keys are held only in Streamlit session/widget memory and sent directly to the
provider selected by the user. The application does not intentionally write keys,
prompts, generated CVs, or downloads to disk. Provider and hosting-platform policies
still apply; see [SECURITY.md](SECURITY.md) for details.

Generated work histories can name real organisations. Use the output only for
legitimate testing and demonstration, never to misrepresent a real person.

Cost figures are estimates based on the verified default-model rates in the source.
The provider invoice is authoritative, and custom model overrides display token usage
without an estimate when pricing is unknown.
