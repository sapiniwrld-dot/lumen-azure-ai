# Lumen — Azure AI Day & Knowledge Copilot

[![CI](https://github.com/sapiniwrld-dot/lumen-azure-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/sapiniwrld-dot/lumen-azure-ai/actions/workflows/ci.yml)

Lumen is a production-style retrieval-augmented generation assistant built on Azure. It answers general questions, helps users plan their day, and grounds support-policy answers in indexed documents with citations.

**[Try the live application](https://ca-lumen-dev-web.thankfulsea-81ba702c.eastus2.azurecontainerapps.io)**

## What this project demonstrates

- Terraform infrastructure as code
- Azure OpenAI and Azure AI Search
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
      |                    +-> Azure OpenAI
      |                    +-> Azure AI Search -> Blob Storage
      |
      +-> Azure Monitor -> Email alerts
      ^
      |
    Five-region health test

    Terraform provisions the Azure resources.
    Managed Identity and RBAC secure service-to-service access.

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

Prerequisites: Python 3.14, Azure CLI, Terraform, and an authenticated Azure account.

1. Clone the repository.
2. Create and activate `.venv`.
3. Install `requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Run `uvicorn app.main:app --reload`.
6. Open `http://127.0.0.1:8000`.

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

Run tests with `pytest -q`.

Load the sample support handbook into Azure AI Search with `python -m scripts.ingest`.

Tests mock paid AI calls and verify the API, health response, grounded answers, and rate limiting.

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

Built and deployed a Terraform-managed RAG assistant on Azure using Azure OpenAI, AI Search, Blob Storage, Managed Identity, FastAPI, Docker, and Container Apps. Added multi-region availability monitoring, performance alerts, cost budgets, rate limiting, automated tests, and GitHub Actions CI.
