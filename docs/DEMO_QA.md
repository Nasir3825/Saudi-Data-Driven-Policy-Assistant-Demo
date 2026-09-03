# Demonstration Questions and Suggested Answers

## What problem does the project solve?

It reduces the time required to find, interpret, and summarize official Saudi economic indicators while keeping the evidence and data date visible to the user.

## Why use RAG instead of asking an LLM directly?

RAG supplies relevant official evidence at question time. This reduces unsupported answers and allows the system to cite sources. It does not eliminate hallucinations, so the application also shows evidence and requires review.

## Why use TF-IDF rather than an embedding model?

TF-IDF is lightweight, transparent, free, and reproducible for a focused prototype. A future version can replace it with multilingual embeddings and a vector database.

## What makes the project Generative AI?

The LLM produces a structured policy synthesis from retrieved evidence. Prompt engineering controls language, structure, citations, caveats, and abstention.

## How do you reduce hallucinations?

The system restricts the prompt to retrieved evidence, demands citations for factual claims, uses low temperature, includes evidence dates, supports abstention, and lets the user inspect every retrieved passage.

## Why does the app work without an API key?

Offline mode provides a reliable demonstration and avoids sending data to an external model. It returns extractive evidence rather than generated synthesis.

## What are the main limitations?

The data snapshot is intentionally small, TF-IDF has limited semantic recall, and generated policy interpretations require expert review. The application is not an official forecasting or decision system.

## How would you improve it?

Add automated data refresh, multilingual embeddings, a larger official-document corpus, quantitative tool calling, authentication, feedback logging, citation verification, and a formal evaluation dataset.

