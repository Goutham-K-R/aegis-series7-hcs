# Aegis Knowledge System

This project implements the Aegis Series-7 HCS knowledge ingestion and evidence-grounded QA system.

## Streamlit Web Interface

Run:

```bash
streamlit run app.py
```

Then open the local Streamlit URL.

The UI is only a presentation layer. All factual decisions, retrieval, and conflict resolution remain inside the deterministic, read-only QA pipeline. The UI does not mutate the database and guarantees 100% provenance for all answers.
