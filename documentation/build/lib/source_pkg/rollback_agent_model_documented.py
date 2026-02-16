import mlflow
from mlflow import MlflowClient
from packaging import version
from source_pkg.utils import get_config

def main():
    """Rolls back a registered MLflow model to the previous version.

    This function automates the rollback process by identifying the current version,
    searching for all available versions, determining the previous version, and
    re-assigning the alias to the previous version. It handles potential errors
    during the rollback process and provides informative messages to the user.

    Auto-logging of Langchain experiments is enabled at the start.
    """
    #auto log
    mlflow.langchain.autolog() 

    config = get_config()
    MODEL_NAME = config.model_name
    ALIAS = config.alias

    mlflow.set_registry_uri("databricks-uc")
    client = MlflowClient()

    try:
        current_ver_obj = client.get_model_version_by_alias(MODEL_NAME, ALIAS)
        cur_v = version.parse(current_ver_obj.version)    

        all_versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        version_objects = sorted([version.parse(v.version) for v in all_versions])

        if cur_v <= version_objects[0]:
            print(f"Cannot rollback: Version {cur_v} is already the oldest version.")
            return

        # Find the version just below current prod
        prev_v = max([v for v in version_objects if v < cur_v])

        # Re-assign the Alias
        print(f"Rolling back {MODEL_NAME} from v{cur_v} to v{prev_v}...")
        client.set_registered_model_alias(MODEL_NAME, ALIAS, str(prev_v))
        
        print(f"Success! Traffic is now routed to version {prev_v}.")

    except Exception as e:
        print(f"Rollback failed: {str(e)}")

# Standard boilerplate for direct execution
if __name__ == "__main__":
    main()
