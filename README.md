# Lumen — Azure AI Day & Knowledge Copilot

[![CI](https://github.com/sapiniwrld-dot/lumen-azure-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/sapiniwrld-dot/lumen-azure-ai/actions/workflows/ci.yml)

Lumen is a production-style retrieval-augmented generation assistant built on Azure. It answers general questions, helps users plan their day, and grounds support-policy answers in indexed documents with citations.

**[Try the live application](https://ca-lumen-dev-web.thankfulsea-81ba702c.eastus2.azurecontainerapps.io)**

## What this project demonstrates

- Terraform infrastructure as code
- Multi-provider generation with Azure OpenAI, Gemini API, and Vertex AI
- LangGraph two-agent orchestration for retrieval and grounded responses
- Pluggable retrieval with Azure AI Search or PostgreSQL and pgvector
- Private documents in Azure Blob Storage
- Managed Identity and Azure RBAC
- FastAPI and Azure Container Apps
- Per-IP prompt rate limiting
- Five-region availability testing
- Azure Monitor alerts and a $25 budget
- GitHub Actions tests and container builds

## Architecture

    User
      |
      v
    Azure Container Apps -> FastAPI
      |                    |
      |                    +-> Azure OpenAI / Gemini API / Vertex AI
      |                    +-> Azure AI Search -> Blob Storage
      |                    +-> PostgreSQL + pgvector (optional backend)
      |
      +-> Azure Monitor -> Email alerts
      ^
      |
    Five-region health test

    Terraform provisions the Azure resources.
    Managed Identity and RBAC secure service-to-service access.
    ### LangGraph support workflow

    START -> retrieval_agent -> response_agent -> END

The retrieval agent performs semantic search through the configured Azure AI Search or pgvector backend and prepares numbered evidence. The response agent sends that grounded context through the configured Azure OpenAI, Gemini API, or Vertex AI provider and returns an answer with citations.

The graph is compiled once and reused for stateless requests. It preserves the existing safety routing and uses one generation call per support question.

## Reliability and cost controls

Lumen monitors:

- HTTP 5xx server errors
- Responses averaging more than five seconds
- Container restarts
- Memory usage above 85%
- External health failures from at least three of five regions

The resource group has a $25 monthly budget with alerts at 50%, 80%, and 100%, plus a forecast warning.

The public `/ask` endpoint permits 10 prompts per IP address per minute and returns HTTP 429 when the limit is exceeded.

## Run locally

Prerequisites: Python 3.14, Azure CLI, Docker Desktop, Terraform, and an authenticated Azure account. Gemini API requires a Google AI Studio API key; Vertex AI also requires the Google Cloud CLI and a Google Cloud project.

1. Clone the repository.
2. Create and activate `.venv`.
3. Install `requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Add the Azure OpenAI endpoint and embedding deployment to `.env`; retrieval embeddings remain Azure-backed.
6. Choose a chat provider:
   - Azure OpenAI: set `CHAT_PROVIDER=azure_openai` and `AZURE_OPENAI_CHAT_DEPLOYMENT`.
   - Gemini API: set `CHAT_PROVIDER=gemini_api`, `GEMINI_MODEL=gemini-3.5-flash-lite`, and `GEMINI_API_KEY`.
   - Vertex AI: set `CHAT_PROVIDER=vertex_ai`, `GEMINI_MODEL=gemini-3.5-flash-lite`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION=global`; then authenticate locally with `gcloud auth application-default login`.
7. Choose and prepare a retrieval backend:
   - Azure AI Search: set `RETRIEVAL_BACKEND=azure_search`, then run `python -m scripts.ingest`.
   - pgvector: set `RETRIEVAL_BACKEND=pgvector`, run `docker compose up -d postgres`, then run `python -m scripts.ingest_pgvector`.
8. Run `uvicorn app.main:app --reload`.
9. Open `http://127.0.0.1:8000`.

## Container security

The production image installs current Debian security updates during the build, runs as an unprivileged `lumen` user, and includes a Docker health check for `/health`. Azure Container Apps deploys an immutable GHCR digest recorded in Terraform rather than a mutable tag.

Build, verify, and scan the image locally:

    docker build --pull --no-cache --tag lumen-azure-ai:local .
    docker run --detach --name lumen-local --env-file .env --publish 8000:8000 lumen-azure-ai:local
    docker inspect --format "{{.State.Health.Status}} {{.Config.User}}" lumen-local
    docker scout cves local://lumen-azure-ai:local

Review scanner findings against the installed runtime packages and upstream Debian security tracker before deployment. Do not suppress findings solely to make a scan pass.

## Provision Azure infrastructure

1. Run `az login`.
2. Copy `terraform.tfvars.example` to `terraform.tfvars`.
3. Add your subscription ID and alert email.
4. Run `terraform init`.
5. Run `terraform fmt -check` and `terraform validate`.
6. Review `terraform plan`.
7. Run `terraform apply`.

Never commit `.env`, `terraform.tfvars`, Terraform state, or saved plan files.

## Test and ingest

Run the test suite:

    pytest -q

Load the sample support handbook into Azure AI Search:

    python -m scripts.ingest

Or load it into PostgreSQL with pgvector:

    docker compose up -d postgres
    python -m scripts.ingest_pgvector

Tests mock paid AI calls and verify the API, health response, LangGraph agent execution, safety and question routing, grounded answers, rate limiting, chat provider routing, retrieval backend routing, and pgvector ingestion.

## Public API

Health endpoint:

    GET /health

Prompt endpoint:

    POST /ask
    Content-Type: application/json
    {"question":"Help me plan a productive afternoon."}

## Clean up

To avoid ongoing Azure charges, first review `terraform plan -destroy`, then run `terraform destroy` only when you intend to remove the project.

## Résumé description

Built and deployed a Terraform-managed RAG assistant on Azure using FastAPI, Docker, Container Apps, Managed Identity, Azure AI Search, and Blob Storage. Orchestrated support queries with a LangGraph two-agent workflow for semantic retrieval and cited response generation. Added pluggable generation across Azure OpenAI, Gemini API, and Vertex AI, plus interchangeable Azure AI Search and PostgreSQL/pgvector retrieval. Added multi-region monitoring, rate limiting, automated tests, and GitHub Actions CI.