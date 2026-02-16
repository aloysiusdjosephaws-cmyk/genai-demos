<img width="2613" height="1682" alt="image" src="https://github.com/user-attachments/assets/3cd91ef1-6fd5-4536-9b7f-95dbdc5925a0" />

# DEMO: GenAI Agent Platform for Electronic Components

The **Electronics** project is a production-ready Python package for managing, deploying, and scaling agentic AI models on the **Databricks Mosaic AI** platform. It utilizes a state-of-the-art stack including **LangGraph** for orchestration, **Unity Catalog (UC)** for governance, and **Databricks Asset Bundles (DABs)** for CI/CD.

## 🏗️ Architecture Overview

The system follows a modular "Agent-as-a-Model" architecture governed by Unity Catalog:

1.  **Data Layer**: Raw CSVs ingested into **Delta Lake** with Liquid Clustering.
2.  **Retrieval Layer**: **Databricks Vector Search** provides semantic retrieval over the ingested data.
3.  **Agent Logic**: **LangGraph** orchestrates the reasoning loop, using **UC Functions** as tools for real-time data access.
4.  **Ops/MLOps**: Managed via **MLflow** for tracking and **Databricks Asset Bundles (DABs)** for multi-environment deployment.
5.  **Interface**: A **Streamlit** application consuming a **Mosaic AI Model Serving** endpoint.

---

## 🛠️ Tech Stack & Components

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Governance** | [Unity Catalog](https://www.databricks.com) | Centralized management of Delta tables, Volumes, and UC Functions. |
| **Orchestration**| [LangGraph](https://www.langchain.com) | Stateful, multi-turn agent logic and tool-calling flows. |
| **Agent Tooling** | [UC Functions](https://docs.databricks.com) | Python/SQL functions in UC registered as tools for the agent. |
| **Model Tracking**| [MLflow](https://mlflow.org) | Versioning for LangGraph agents and evaluation metrics. |
| **Serving** | [Mosaic AI Model Serving](https://www.databricks.com) | Low-latency endpoint hosting the agent as a model. |
| **Infrastructure**| [Databricks Asset Bundles (DABs)](https://docs.databricks.com) | Infrastructure-as-code for CI/CD and Workflow orchestration. |

---

## 🚀 Execution Workflow

1.  **Data Ingestion**: `ingest_data_deltalake.py` streams CSV data into Delta Lake and triggers `create_vector_index.py` to sync embeddings.
2.  **Development**: `agent_model.py` defines the LangGraph logic, incorporating `utils.py` for config management.
3.  **Registration**: `register_agent_model.py` logs the agent to MLflow and registers it in Unity Catalog as a Model.
4.  **Deployment**: The `databricks.yml` bundle automates the creation of Model Serving endpoints via `serve_agent_model.py`.
5.  **Evaluation**: `evaluate_agent_model.py` runs systematic tests against the endpoint to ensure accuracy.
6.  **UX**: Users interact with the agent through `app.py` (Streamlit), which provides a governed chat interface.

---

## 📂 Project Structure

- `source_pkg/`: Core logic including the `agent_model.py` and tool definitions.
- `databricks.yml`: The primary DAB configuration for CI/CD jobs and resources.
- `ingest/`: Scripts for Delta Lake and Vector Search maintenance.
- `deployment/`: Scripts for serving, registration, and version rollbacks.
- `tests/`: Evaluation and unit testing for agent responses.

---

## 🔧 Deployment Commands

Manage the project lifecycle using the [Databricks CLI](https://docs.databricks.com):

```bash
# Validate the bundle configuration
databricks bundle validate --target dev

# Deploy the stack to the dev environment
databricks bundle deploy --target dev

# Run the app UI
databricks bundle run app-ui --target dev 

