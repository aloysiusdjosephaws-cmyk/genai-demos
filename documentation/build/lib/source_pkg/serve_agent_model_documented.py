import time
import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ServedEntityInput, EndpointCoreConfigInput, EndpointStateConfigUpdate
from source_pkg.utils import get_config

def main():
    """
    Deploys a Databricks model to a serving endpoint using MLflow and the Databricks SDK.

    This function automates the deployment of a machine learning model to a Databricks serving endpoint.
    It retrieves model information, configures the endpoint with the model, and handles potential errors such
    as endpoint already existing or configuration updates in progress.  It leverages MLflow for experiment
    tracking and Databricks SDK for endpoint deployment and management.

    Raises:
        Exception: If any unexpected error occurs during the deployment process (other than endpoint already exists).
    """
    #auto log
    mlflow.langchain.autolog()
    config = get_config()

    MODEL_NAME = config.model_name
    EXPERIMENT_PATH = config.experiment_path
    ALIAS = config.alias
    WORKLOAD_SIZE = config.workload_size
    SERVING_ENDPOINT_NAME = config.serving_endpoint_name

    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(EXPERIMENT_PATH)

    try:
        with mlflow.start_run() as run:
            print(f"SUCCESS: Run ID: {run.info.run_id}")

            w = WorkspaceClient()

            model_info = w.model_versions.get_by_alias(
                full_name=MODEL_NAME,
                alias=ALIAS
            )
            configuration = EndpointCoreConfigInput(
                name=SERVING_ENDPOINT_NAME,
                served_entities=[
                    ServedEntityInput(
                        name="primary",
                        entity_name=f"{MODEL_NAME}",
                        entity_version=str(model_info.version),
                        scale_to_zero_enabled=True,
                        workload_size=WORKLOAD_SIZE
                    )
                ]
            )

            try:
                print(f"Deploying {SERVING_ENDPOINT_NAME}...")
                status = w.serving_endpoints.create_and_wait(name=SERVING_ENDPOINT_NAME, config=configuration)
                print(f"Active! URL: {status.task_ids}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("Endpoint exists, checking for pending updates...")

                    # Poll until the endpoint is ready for a new configuration
                    while w.serving_endpoints.get(SERVING_ENDPOINT_NAME).state.config_update == EndpointStateConfigUpdate.IN_PROGRESS:
                        print("Update in progress, waiting 30s...")
                        time.sleep(30)

                    status = w.serving_endpoints.update_config_and_wait(
                        name=SERVING_ENDPOINT_NAME,
                        served_entities=configuration.served_entities
                    )
                    print("Update complete")
                else:
                    raise e

    except Exception as ee:
        print(f"ERROR: An exception occurred inside the mlflow.start_run() block: {ee}")

# Standard boilerplate for direct execution/testing
if __name__ == "__main__":
    main()