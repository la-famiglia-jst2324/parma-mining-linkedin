terraform {
  required_version = "1.5.3"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.12.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
  backend "gcs" {
    bucket      = "la-famiglia-jst2324-tf-state"
    prefix      = "terraform/state/prod/mining/linkedin"
    credentials = "../.secrets/la-famiglia-parma-ai.json"
  }
}

locals {
  project = "la-famiglia-parma-ai"
  region  = "europe-west1"
}

provider "google" {
  credentials = file("../.secrets/la-famiglia-parma-ai.json")
  project     = local.project
  region      = local.region
}

module "main" {
  source           = "../module"
  env              = "prod"
  project          = local.project
  region           = local.region
  ANALYTICS_BASE_URL = var.ANALYTICS_BASE_URL

  PARMA_SHARED_SECRET_KEY = var.PARMA_SHARED_SECRET_KEY

  APIFY_API_KEY = var.APIFY_API_KEY
  APIFY_ACTOR_ID = var.APIFY_ACTOR_ID
  LINKEDIN_COOKIE = var.LINKEDIN_COOKIE
}
