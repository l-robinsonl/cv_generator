# Security and privacy

This is a bring-your-own-key application. Users should create a provider key with the
lowest practical permissions and spending limit, and revoke it if they suspect it has
been exposed.

The app does not intentionally persist API keys or generated documents. Values exist
in the Streamlit process/session long enough to make provider requests and prepare a
download. Keys are masked in the interface and are not included in generated files,
ZIP archives, application logs, repository files, or Streamlit secrets.

Deployments still depend on Streamlit hosting, the selected AI provider, TLS, and the
operator's configuration. Do not use the app with confidential personal information.

To report a vulnerability, open a private security advisory on the GitHub repository.
