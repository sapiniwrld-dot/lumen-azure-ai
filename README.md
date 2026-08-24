# Lumen — Azure AI Support Copilot

Lumen is a retrieval-augmented generation (RAG) assistant for customer-support teams. It retrieves relevant policy passages from Azure AI Search, generates grounded answers with Azure OpenAI, and returns citations for verification.

## Highlights

- Infrastructure defined entirely with Terraform
- GPT-5 Mini and text-embedding-3-small on Azure OpenAI
- Hybrid keyword and vector retrieval with Azure AI Search
- Private source-document storage in Azure Blob Storage
- Keyless authentication through Microsoft Entra ID and Azure RBAC
- FastAPI service with generated OpenAPI documentation
- Grounded answers with source citations
- Automated tests that avoid paid cloud calls

## Architecture

```text
Client
  |
  v
FastAPI
  |
  +--> Azure AI Search ----> relevant document passages
  |
  +--> Azure OpenAI -------> grounded answer with citations
  |
  +--> Blob Storage -------> private source documents
