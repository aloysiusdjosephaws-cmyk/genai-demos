from setuptools import setup, find_packages
import yaml
import os

# Load the bundle name directly from your config file
with open("databricks.yml", "r") as f:
    bundle_config = yaml.safe_load(f)
    PROJECT_NAME = bundle_config.get("bundle", {}).get("name", "source_pkg")

setup(
    name=PROJECT_NAME,
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': [
            '_ingest_data_deltalake=source_pkg.ingest_data_deltalake:main',
            '_create_vector_index=source_pkg.create_vector_index:main',
            '_register_agent_model=source_pkg.register_agent_model:main',
            '_evaluate_agent_model=source_pkg.evaluate_agent_model:main',
            '_serve_agent_model=source_pkg.serve_agent_model:main',
            '_test_agent_model=source_pkg.test_agent_model:main',
            '_rollback_agent_model=source_pkg.rollback_agent_model:main',
            '_delete_project=source_pkg.delete_project:main',
            '_document_code=source_pkg.document_code:main',
            '_document_project=source_pkg.document_project:main',
        ],
    },
    install_requires=[
        "mlflow==3.9.0",
        "databricks-agents==1.9.3",
        "databricks-langchain==0.14.0",
        "databricks-vectorsearch==0.64",
        "langgraph==1.0.6",
        "langchain==1.2.6",
        "databricks-sdk==0.82.0",
        "databricks-sdk[openai]==0.82.0",
        "pandas",
        "pyyaml==6.0.3",
        "cloudpickle==3.1.2",
        "flask==3.1.2",
        "setuptools==80.10.2"
    ],
)
