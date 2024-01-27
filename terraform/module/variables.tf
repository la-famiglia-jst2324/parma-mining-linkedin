variable "env" {
  description = "staging or prod environment"
  type        = string
}

variable "project" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
}

variable "ANALYTICS_BASE_URL" {
  description = "value"
  type        = string
}

/* ------------------------ Analytics and Sourcing Auth Flow ------------------------ */

variable "PARMA_SHARED_SECRET_KEY" {
  description = "Shared secret key for the analytics and sourcing auth flow"
  type        = string
  sensitive   = true
}

/* ----------------------------------- Linkedin ----------------------------------- */

variable "APIFY_API_KEY" {
  description = "Apify API key"
  type        = string
  sensitive   = true
}

variable "APIFY_ACTOR_ID" {
  description = "Apify actor ID"
  type        = string
  sensitive   = false
}

variable "LINKEDIN_COOKIE" {
  description = "Linkedin cookie"
  type        = string
  sensitive   = true
}
