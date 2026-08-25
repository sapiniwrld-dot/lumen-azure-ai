variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region for the project"
  type        = string
  default     = "eastus2"
}

variable "project_name" {
  description = "Short name used for Azure resources"
  type        = string
  default     = "lumen"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}
variable "search_location" {
  description = "Azure region for AI Search"
  type        = string
  default     = "centralus"
}

variable "alert_email" {
  description = "Email address that receives Azure Monitor alerts"
  type        = string
}

variable "monthly_budget_amount" {
  description = "Monthly Azure budget for the Lumen resource group"
  type        = number
  default     = 25
}
