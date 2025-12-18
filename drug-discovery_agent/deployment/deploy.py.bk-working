# Copyright 2025 Google LLC
# Licensed under the Apache License, Version 2.0.

import os
import vertexai
from absl import app, flags
from dotenv import load_dotenv
from drug_discovery_agent.agent import root_agent
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP storage bucket for staging.")
flags.DEFINE_bool("create", False, "Creates a new agent.")

def create_agent(env_vars):
    """Creates a new Agent Engine using the OFFICIAL AdkApp wrapper."""
    print("🚀 Deploying NATIVE ADK AGENT with TELEMETRY...")
    
    # Standard ADK Wrapper
    adk_app = AdkApp(agent=root_agent)
    
    remote_agent = agent_engines.create(
        adk_app,
        display_name="agentic-tx-adk",
        requirements=[
            # 1. STABLE SDK (Critical for Gemini Ent)
            "google-cloud-aiplatform==1.126.1",
            
            # 2. TELEMETRY SUPPORT
            "google-adk>=1.17.0",
            "opentelemetry-instrumentation-google-genai>=0.4b0",
            "opentelemetry-exporter-gcp-logging",
            "opentelemetry-exporter-gcp-monitoring",
            "opentelemetry-exporter-otlp-proto-grpc",
            "opentelemetry-instrumentation-vertexai>=2.0b0",
            
            # 3. AGENT DEPENDENCIES
            "python-dotenv>=1.0.1",
            "biopython>=1.83",
            "pubchempy>=1.0.4",
            "google-search-results>=2.4.2",
            "pydantic==2.11.7",
            "cloudpickle==3.1.1"
        ],
        extra_packages=[
            "./drug_discovery_agent"
        ],
        env_vars=env_vars
    )
    print(f"✅ Created remote agent: {remote_agent.resource_name}")

def main(_):
    load_dotenv()
    
    # TELEMETRY & PLACEHOLDER CONFIGURATION
    env_vars = {
        # Placeholders allow deployment to succeed even if you lack keys right now.
        # The agent will run, but tools will return "Auth Error" instead of crashing.
        "TXGEMMA_PREDICT_ENDPOINT_ID": os.getenv("TXGEMMA_PREDICT_ENDPOINT_ID", "placeholder_predict"),
        "TXGEMMA_CHAT_ENDPOINT_ID": os.getenv("TXGEMMA_CHAT_ENDPOINT_ID", "placeholder_chat"),
        "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY", "placeholder_serp"),
        
        # Enable OTel Tracing/Logging
        "OTEL_SERVICE_NAME": "drug-discovery-agent",
        "OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED": "true",
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true"
    }
    
    # Clean empty values
    env_vars = {k: v for k, v in env_vars.items() if v}

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    
    vertexai.init(project=project_id, location=location, staging_bucket=f"gs://{bucket}")

    if FLAGS.create:
        create_agent(env_vars)

if __name__ == "__main__":
    app.run(main)