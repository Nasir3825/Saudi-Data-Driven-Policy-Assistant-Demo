# Evaluation Plan

## Metrics

1. **Retrieval Hit@5:** required evidence occurs among the first five results.
2. **Numeric accuracy:** generated values match the snapshot exactly.
3. **Citation coverage:** factual sentences include an evidence marker.
4. **Faithfulness:** claims are supported by retrieved passages.
5. **Abstention accuracy:** unsupported questions receive an insufficient-evidence response.
6. **Bilingual quality:** two reviewers score clarity and terminology from 1 to 5.
7. **Latency:** median time for ten generated answers.

## Suggested acceptance criteria

- Retrieval Hit@5 at least 90% on the supplied question set.
- Numeric accuracy 100% for supported factual questions.
- Citation coverage at least 95%.
- Abstention accuracy 100% on deliberately unsupported questions.
- Average bilingual clarity at least 4 out of 5.

Record results in a table with question ID, retrieved sources, response, expected terms, pass/fail, latency, and reviewer notes.

