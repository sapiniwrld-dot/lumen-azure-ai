output "resource_group_name" {
  description = "Azure resource group"
  value       = azurerm_resource_group.main.name
}

output "azure_openai_endpoint" {
  description = "Azure OpenAI API endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "chat_deployment_name" {
  description = "Azure OpenAI chat deployment"
  value       = azurerm_cognitive_deployment.chat.name
}
output "embedding_deployment_name" {
  description = "Azure OpenAI embedding deployment"
  value       = azurerm_cognitive_deployment.embeddings.name
}

output "azure_search_endpoint" {
  description = "Azure AI Search endpoint"
  value       = azurerm_search_service.main.endpoint
}

output "storage_account_name" {
  description = "Document storage account"
  value       = azurerm_storage_account.documents.name
}

output "document_container_name" {
  description = "Private document container"
  value       = azurerm_storage_container.documents.name
}


output "application_url" {
  description = "Public Lumen application URL"
  value       = "https://${azurerm_container_app.web.ingress[0].fqdn}"
}
