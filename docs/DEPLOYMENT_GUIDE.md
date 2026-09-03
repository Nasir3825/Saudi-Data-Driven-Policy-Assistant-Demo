# Deployment Guide

## Pre-deployment checklist

- `pytest` passes.
- `streamlit run app.py` starts locally.
- No real API key appears in any file or notebook output.
- `.env` and `secrets.toml` are ignored by Git.
- `app.py` and `requirements.txt` are at repository root.
- The official snapshot access date is visible in the app.

## Private GitHub repository

Create a private repository, upload all project contents, and verify the repository visibility under **Settings > General > Change repository visibility**. Hidden configuration files are helpful but not required for the first Streamlit deployment.

## Streamlit Secrets

In Streamlit Community Cloud, add the Groq key in the app's Secrets panel. Do not add quotes around the full TOML block and do not paste the key into `app.py`.

## Troubleshooting

- **Model not found:** set `GROQ_MODEL = "auto"`, save the secrets, and reboot the app.
- **Module not found:** confirm `requirements.txt` is in the same folder as `app.py`, then reboot the app.
- **Python mismatch:** choose Python 3.12 in Streamlit's advanced deployment settings.
- **Blank chart:** confirm dates and numeric values in the CSV are valid.
- **No generated synthesis:** add a valid Groq key; offline retrieval is the expected fallback.
- **DataSaudi API failure:** continue with the packaged snapshot for the demonstration and refresh later.
