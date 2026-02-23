# DEMO - GenAI RAG system using Databricks 

## Retrieval Augmented Generation using Databricks
<img width="707" height="363" alt="image" src="https://github.com/user-attachments/assets/8ccf1958-3542-4b68-9423-ca2a34cedb15" />

## Demo Architecture Diagram
```mermaid
%%{init: {'theme':'default', 'themeVariables': {'clusterBkg':'#fafafa'}}}%%
graph TB
    subgraph "Data Layer"
        CSV[📄 CSV Data Sources] --> DeltaLake[(🗄️ Delta Lake Tables)]
        DeltaLake --> VectorSearch[🔍 Vector Search Index]
    end
    
    subgraph "Unity Catalog"
        UC[🏛️ Unity Catalog]
        UCFunctions[⚙️ UC Functions as Tools]
        UC --> DeltaLake
        UC --> MLFlow
        UC --> VectorSearch
    end
    
    subgraph "ML & Agent Layer"
        AgentModel[🤖 Agent Model<br/>LangGraph-based]
        MLFlow[📊 MLflow<br/>Tracking & Registry]
        AgentModel --> MLFlow
        VectorSearch -.retrieval.-> AgentModel
        UCFunctions -.tools.-> AgentModel
    end
    
    subgraph "Mosaic AI Platform"
        MosaicAgent[✨ Mosaic AI Agent Framework]
        ModelServing[🚀 Model Serving Endpoint]
        AgentModel --> MosaicAgent
        MosaicAgent --> ModelServing
    end
    
    subgraph "Orchestration & Deployment"
        DAB[📦 Databricks Asset Bundle]
        Workflows[⚡ Databricks Workflows]
        CICD[🔄 CI/CD Jobs]
        DAB --> Workflows
        CICD --> DAB
    end
    
    subgraph "Application Layer"
        Streamlit[💬 Streamlit UI App]
        API[🔌 Databricks SDK]
        Streamlit --> API
        API --> ModelServing
    end
    
    subgraph "Development & Operations"
        Ingest[📥 ingest_data_deltalake.py]
        CreateIndex[🔨 create_vector_index.py]
        Register[📝 register_agent_model.py]
        Evaluate[✅ evaluate_agent_model.py]
        Serve[🌐 serve_agent_model.py]
        Rollback[⏮️ rollback_agent_model.py]
        Delete[🗑️ delete_project.py]
    end
    
    Workflows --> Ingest
    Ingest --> CreateIndex
    CreateIndex --> Register
    Register --> Evaluate
    Evaluate --> Serve
    Serve --> Rollback
    Rollback --> Delete
    
    CSV --> Ingest
    Ingest --> DeltaLake
    CreateIndex --> VectorSearch
    Register --> MLFlow
    Evaluate --> MLFlow
    Serve --> ModelServing
    
    style CSV fill:#bbdefb,stroke:#1565c0,stroke-width:3px,color:#000
    style DeltaLake fill:#81c784,stroke:#2e7d32,stroke-width:4px,color:#fff
    style VectorSearch fill:#fff176,stroke:#f57f17,stroke-width:3px,color:#000
    style UC fill:#00a972,stroke:#004d3a,stroke-width:4px,color:#fff
    style UCFunctions fill:#26a69a,stroke:#00695c,stroke-width:3px,color:#fff
    style AgentModel fill:#ba68c8,stroke:#6a1b9a,stroke-width:4px,color:#fff
    style MLFlow fill:#66bb6a,stroke:#2e7d32,stroke-width:4px,color:#fff
    style MosaicAgent fill:#ff3621,stroke:#b71c1c,stroke-width:4px,color:#fff
    style ModelServing fill:#ff5722,stroke:#d84315,stroke-width:4px,color:#fff
    style DAB fill:#ff9800,stroke:#e65100,stroke-width:4px,color:#fff
    style Workflows fill:#ffb74d,stroke:#f57c00,stroke-width:4px,color:#000
    style CICD fill:#ffd54f,stroke:#ff6f00,stroke-width:3px,color:#000
    style Streamlit fill:#42a5f5,stroke:#0d47a1,stroke-width:4px,color:#fff
    style API fill:#1e88e5,stroke:#0d47a1,stroke-width:3px,color:#fff
    style Ingest fill:#9575cd,stroke:#4527a0,stroke-width:3px,color:#fff
    style CreateIndex fill:#7986cb,stroke:#283593,stroke-width:3px,color:#fff
    style Register fill:#4fc3f7,stroke:#01579b,stroke-width:3px,color:#000
    style Evaluate fill:#4db6ac,stroke:#004d40,stroke-width:3px,color:#fff
    style Serve fill:#9ccc65,stroke:#33691e,stroke-width:3px,color:#000
    style Rollback fill:#ffb74d,stroke:#e65100,stroke-width:3px,color:#000
    style Delete fill:#ef5350,stroke:#b71c1c,stroke-width:3px,color:#fff
```
### Project Overview
The **Electronics Agent System** is a production-ready, enterprise-grade AI agent platform built on the latest Databricks GenAI stack. It manages electronic component data through intelligent RAG (Retrieval-Augmented Generation) capabilities, featuring full MLOps lifecycle management, version control, and automated deployment pipelines.

### Technology Stack

#### Core Databricks Components
- **Unity Catalog**: Centralized governance for data, models, and functions with fine-grained access control
- **Delta Lake**: ACID-compliant data lake with liquid clustering optimization and change data feed capabilities
- **Vector Search**: Managed vector database for semantic similarity search with auto-sync capabilities
- **MLflow**: Experiment tracking, model registry, and lifecycle management
- **Databricks SDK**: Python API for programmatic interaction with Databricks services

#### AI/ML Framework
- **LangGraph**: Orchestrates complex agent workflows with state management
- **Mosaic AI Agent Framework**: Enterprise-grade agent deployment and management
- **UC Functions as Tools**: Registered Unity Catalog functions serve as callable tools for agents
- **Agents as Models**: Agents packaged and versioned as MLflow models

#### DevOps & Deployment
- **Databricks Asset Bundles (DAB)**: Infrastructure-as-code for resource management via `databricks.yml`
- **CI/CD Workflows**: Automated pipelines for validation, deployment, and testing
- **Databricks Workflows**: Orchestrates data ingestion, indexing, training, evaluation, and serving jobs

### System Architecture

#### Data Pipeline
1. **Ingestion**: CSV files → Delta Lake tables (via `ingest_data_deltalake.py`)
2. **Indexing**: Delta Lake → Vector Search indexes (via `create_vector_index.py`)
3. **Optimization**: Liquid clustering and change data feed for performance

#### Agent Lifecycle
1. **Development**: Agent model defined using LangGraph with UC Functions as tools (`agent_model.py`)
2. **Registration**: Model registered to MLflow with Unity Catalog integration (`register_agent_model.py`)
3. **Evaluation**: Performance testing against predefined Q&A pairs (`evaluate_agent_model.py`)
4. **Deployment**: Model served via Databricks Model Serving endpoints (`serve_agent_model.py`)
5. **Versioning**: Rollback capabilities for model versions (`rollback_agent_model.py`)

#### Application Layer
- **Streamlit UI** (`app.py`): Interactive chat interface for end-users
- **Databricks SDK**: Handles API communication between UI and model serving endpoints
- **Session Management**: Persistent chat history and conversation tracking

### Key Features

**MLOps Capabilities**
- Automated model versioning and tracking
- A/B testing and canary deployments via serving endpoints
- Rollback to previous model versions
- Comprehensive evaluation framework
- Metric logging and monitoring

**Governance & Security**
- Unity Catalog-based access controls
- Audit logging for data and model access
- Secure credential management
- Project isolation and resource management

**Operational Excellence**
- Infrastructure-as-code deployment
- Automated CI/CD pipelines
- Project documentation generation (`document_project.py`)
- Complete resource cleanup (`delete_project.py`)
- Environment reproducibility via `requirements.txt` and `setup.py`

### Deployment Workflow

Using Databricks Asset Bundles, the system supports:
1. **Validation**: `databricks bundle validate`
2. **Deployment**: `databricks bundle deploy -t dev`
3. **Testing**: Automated evaluation jobs
4. **Serving**: Model endpoint activation
5. **Monitoring**: MLflow tracking and metrics
6. **Rollback**: Version control with one-command rollback
7. **Cleanup**: `databricks bundle destroy`

## 🔧 Deployment Commands

Manage the project lifecycle using the [Databricks CLI](https://docs.databricks.com):

```bash
# Validate the bundle configuration
databricks bundle validate --target dev

# Deploy the stack to the dev environment
databricks bundle deploy --target dev

# Run the app UI
databricks bundle run app-ui --target dev 
```

<img width="1317" height="984" alt="image" src="https://github.com/user-attachments/assets/854b1ea9-b3ee-428d-b144-4943f3d04c00" />

## DevSecOps

### Development
```mermaid
graph TD
    User((User / Streamlit UI)) -->|1. Query| GuardIn{Input Guardrail}
    GuardIn -->|Unsafe| Abort[Policy Violation Redaction]
    
    subgraph "Agent Decision Logic"
    GuardIn -->|Safe| Agent[Electronics Agent]
    Agent -->|2. Internal Prompt| SystemPrompt[Prompt: Use Catalog First]
    Agent -->|3. Tool Metadata| ToolDesc[Function Comments]
    Agent -->|4. Decides to Use| Tool[UC Search Tool]
    end

    subgraph "Hybrid Search Mechanism"
    Tool -->|5. Embed Query| EmbedLLM[Embedding LLM]
    EmbedLLM -->|Vector Search| VIndex[Description Vector Index]
    Tool -->|Keyword Search| Category[Category Column]
    VIndex & Category -->|Retrieve| Context[Delta Lake Context]
    end

    subgraph "Response Generation"
    Context -->|6. Check Data| Choice{Found in Catalog?}
    Choice -->|Yes| Finalize[Format Agent Response]
    Choice -->|No| Foundation[Foundational LLM + Source Note]
    Foundation --> Finalize
    end

    Finalize --> GuardOut{Output Guardrail}
    GuardOut -->|Safe| Success[Final Result + TraceID]
    Success -->|7. Observe| MLflow[(MLflow Traces)]
    Success --> User

```
### Operations
```mermaid
graph TD
    subgraph "1. Infrastructure as Code (DAB)"
        DAB[databricks.yml Blueprint]
        WHEEL[Python Wheel Packaging]
        CONFIG[YAML Configs: No Hardcoding]
        
        DAB --- WHEEL
        DAB --- CONFIG
    end

    subgraph "2. Automated Orchestration (Jobs & Tasks)"
        JOB[DAB Job Trigger]
        TASK1[Task: Ingest CSV to Delta Lake]
        CDF[Change Data Feed Enabled]
        TASK2[Task: Create Vector Index & Endpoint]
        TASK3[Task: Deploy Agent to Mosaic AI]
        DELETE[Task: Resource Cleanup / Delete]

        JOB --> TASK1
        TASK1 --- CDF
        TASK1 --> TASK2
        TASK2 --> TASK3
        TASK3 -.-> DELETE
    end

    subgraph "3. Governance Layer (Unity Catalog)"
        UC{Unity Catalog}
        TABLES[(Delta Tables)]
        FUNCS[Search Functions / Tools]
        MODELS[Agent Models]
        
        UC --- TABLES
        UC --- FUNCS
        UC --- MODELS
    end

    subgraph "4. AI-Assisted Maintenance"
        COPY[Project Copy Task]
        DOCS[Auto-Docstring Generation]
        SUMMARY[Weak LLM: Code & Arch Summary]
        
        COPY --> DOCS
        DOCS --> SUMMARY
    end

    subgraph "5. Production Support & Observability"
        REST[REST API Serving Endpoint]
        MLFLOW[(MLflow Trace & Lineage UI)]
        STREAM[Streamlit UI Connection]
    end

    %% Connection Flows
    DAB -->|Deploy Bundle| JOB
    TASK3 -->|Register Artifacts| UC
    UC -->|Served via| REST
    REST -->|Logs TraceID| MLFLOW
    STREAM -->|Queries| REST
e


```

