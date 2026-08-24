resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

locals {
  prefix = "${var.project_name}-${var.environment}"
  suffix = random_string.suffix.result

  tags = {
    project     = "azure-ai-support-copilot"
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.tags
}
resource "azurerm_cognitive_account" "openai" {
  name                          = "aoai-${local.prefix}-${local.suffix}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  kind                          = "OpenAI"
  sku_name                      = "S0"
  custom_subdomain_name         = "aoai-${local.prefix}-${local.suffix}"
  local_auth_enabled            = false
  public_network_access_enabled = true
  tags                          = local.tags
}
resource "azurerm_cognitive_deployment" "chat" {
  name                 = "gpt-5-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-5-mini"
    version = "2025-08-07"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 10
  }
}
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "developer_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_client_config.current.object_id
}
resource "azurerm_search_service" "main" {
  name                          = "srch-${local.prefix}-${local.suffix}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = var.search_location
  sku                           = "free"
  local_authentication_enabled  = false
  public_network_access_enabled = true
  tags                          = local.tags
}
resource "azurerm_storage_account" "documents" {
  name                            = "st${var.project_name}${var.environment}${local.suffix}"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false
  tags                            = local.tags
}
resource "azurerm_role_assignment" "developer_blob_contributor" {
  scope                = azurerm_storage_account.documents.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "developer_search_service_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Service Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "developer_search_index_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_id    = azurerm_storage_account.documents.id
  container_access_type = "private"
}
resource "azurerm_cognitive_deployment" "embeddings" {
  name                 = "text-embedding-3-small"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 10
  }
}


resource "azurerm_user_assigned_identity" "app" {
  name                = "id-${local.prefix}-app"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags
}

resource "azurerm_role_assignment" "app_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

resource "azurerm_role_assignment" "app_search_reader" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

resource "azurerm_role_assignment" "app_blob_reader" {
  scope                = azurerm_storage_account.documents.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${local.prefix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  logs_destination           = "log-analytics"
  tags                       = local.tags
}

resource "azurerm_container_app" "web" {
  name                         = "ca-${local.prefix}-web"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 0
    max_replicas = 1

    container {
      name   = "lumen"
      image  = "ghcr.io/sapiniwrld-dot/lumen-azure-ai@sha256:b6d6a5edfc479980176344e193ca31ba0f4ae89881e63b144db92462fa5b9644"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = azurerm_cognitive_account.openai.endpoint
      }

      env {
        name  = "AZURE_OPENAI_CHAT_DEPLOYMENT"
        value = azurerm_cognitive_deployment.chat.name
      }

      env {
        name  = "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        value = azurerm_cognitive_deployment.embeddings.name
      }

      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = azurerm_search_service.main.endpoint
      }

      env {
        name  = "AZURE_SEARCH_INDEX"
        value = "lumen-documents"
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT"
        value = azurerm_storage_account.documents.name
      }

      env {
        name  = "AZURE_STORAGE_CONTAINER"
        value = azurerm_storage_container.documents.name
      }

      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.app.client_id
      }

    }
  }

  depends_on = [
    azurerm_role_assignment.app_openai_user,
    azurerm_role_assignment.app_search_reader,
    azurerm_role_assignment.app_blob_reader,
  ]
}

resource "azurerm_monitor_action_group" "lumen_alerts" {
  name                = "ag-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "lumen-alert"
  tags                = local.tags

  email_receiver {
    name                    = "lumen-owner"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }
}

resource "azurerm_monitor_metric_alert" "server_errors" {
  name                = "alert-${local.prefix}-server-errors"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_container_app.web.id]
  description         = "Lumen returned more than two HTTP 5xx responses within five minutes."
  severity            = 1
  frequency           = "PT1M"
  window_size         = "PT5M"
  auto_mitigate       = true
  tags                = local.tags

  criteria {
    metric_namespace = "Microsoft.App/containerApps"
    metric_name      = "Requests"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 2

    dimension {
      name     = "statusCodeCategory"
      operator = "Include"
      values   = ["5xx"]
    }
  }

  action {
    action_group_id = azurerm_monitor_action_group.lumen_alerts.id
  }
}

resource "azurerm_monitor_metric_alert" "slow_responses" {
  name                = "alert-${local.prefix}-slow-responses"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_container_app.web.id]
  description         = "Lumen average response time exceeded five seconds."
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"
  auto_mitigate       = true
  tags                = local.tags

  criteria {
    metric_namespace = "Microsoft.App/containerApps"
    metric_name      = "ResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5000
  }

  action {
    action_group_id = azurerm_monitor_action_group.lumen_alerts.id
  }
}

resource "azurerm_monitor_metric_alert" "container_restarts" {
  name                = "alert-${local.prefix}-container-restarts"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_container_app.web.id]
  description         = "A Lumen container replica restarted."
  severity            = 1
  frequency           = "PT1M"
  window_size         = "PT5M"
  auto_mitigate       = true
  tags                = local.tags

  criteria {
    metric_namespace = "Microsoft.App/containerApps"
    metric_name      = "RestartCount"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 0
  }

  action {
    action_group_id = azurerm_monitor_action_group.lumen_alerts.id
  }
}

resource "azurerm_monitor_metric_alert" "high_memory" {
  name                = "alert-${local.prefix}-high-memory"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_container_app.web.id]
  description         = "Lumen memory usage remained above 85 percent."
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"
  auto_mitigate       = true
  tags                = local.tags

  criteria {
    metric_namespace = "Microsoft.App/containerApps"
    metric_name      = "MemoryPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }

  action {
    action_group_id = azurerm_monitor_action_group.lumen_alerts.id
  }
}
