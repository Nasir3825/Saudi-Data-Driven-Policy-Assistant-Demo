# Security and Responsible AI

## Secrets

- Store the Groq API key only in `.env`, Streamlit Secrets, or an environment variable.
- Never commit `.env` or `.streamlit/secrets.toml`.
- Revoke and replace a key immediately if it appears in a screenshot, notebook output, or repository.

## Data and privacy

- The prototype uses public, aggregate economic indicators.
- Do not enter confidential government information, personal information, or unpublished statistics into the public deployment.
- Public deployments should retain no chat history beyond the current Streamlit session.

## Generative AI controls

- The LLM receives only the user's question and retrieved public evidence.
- The prompt requires citations and prohibits unsupported facts or causal claims.
- Basic prompt-injection patterns are rejected.
- Offline mode avoids the LLM entirely.
- All outputs require human review before policy or publication use.

## Known limitations

The security filter is lightweight and not a replacement for enterprise content controls, authentication, monitoring, rate limiting, or a formal threat model.
