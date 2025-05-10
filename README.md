# Setting up GCloud for VertexAI RAG Corpus

- Create a project in [Google Cloud Console](https://console.cloud.google.com/)
- Copy the Project ID and run this command
```bash
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

- Verify your configuration
```bash
gcloud auth application-default print-access-token
```

- Run:
```bash
python rag/shared_libraries/prepare_corpus_and_data.py
```