import sys
import os
import logging
from databricks.sdk import WorkspaceClient
import mlflow
from source_pkg.utils import get_config
import subprocess


class BundleTools:
    """
    A class containing utility methods for managing Databricks bundles.
    """

    @staticmethod
    def unbind_resource(resource_key, target):
        """
        Manually unbinds a resource from a Databricks bundle deployment.

        This method acts as a bridge between Python and the Databricks bundle CLI.
        It executes a subprocess call to the Databricks CLI to perform the unbinding.

        Args:
            resource_key (str): The key of the resource to unbind.
            target (str): The target to unbind the resource from.

        Returns:
            subprocess.CompletedProcess: The result of the subprocess call.
        """
        cmd = [
            "databricks",
            "bundle",
            "deployment",
            "unbind",
            resource_key,
            "--target",
            target,
            # "--profile", profile,
        ]
        return subprocess.run(cmd, capture_output=True, text=True)


def main():
    """
    Main function to perform a full project cleanup in Databricks.

    This function orchestrates the deletion of various Databricks resources,
    including apps, serving endpoints, vector search indexes & endpoints,
    Unity Catalog tables, MLflow experiments, model versions, volumes,
    and unbinding bundle resources.  It incorporates error handling and
    logging to ensure a robust cleanup process.

    It also sets up basic logging and configures automatic MLflow logging.
    """
    # auto log
    mlflow.langchain.autolog()

    config = get_config()
    # --- CONFIGURATION ---
    VS_ENDPOINT_NAME = config.vs_endpoint_name
    APP_NAME = config.app_name
    VS_INDEX_NAME = config.vs_index_name
    CATALOG = config.catalog
    SCHEMA = config.schema
    TABLE_NAME = config.table_name
    SERVING_ENDPOINT_NAME = config.serving_endpoint_name
    EXPERIMENT_PATH = config.experiment_path
    ALIAS = config.alias
    LOG_FILE = f"{config.logs_path}/cleanup_report.log"

    # Ensure the directory exists before the logger starts
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Setup Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger(__name__)

    w = WorkspaceClient()

    def check_permissions():
        """
        Validates authentication and schema access.

        This function verifies the current user's identity and checks if they
        have access to the specified schema in Unity Catalog. It logs the
        authenticated user and any warnings related to schema access.

        Returns:
            bool: True if authentication and schema access are successful;
                  False otherwise.
        """
        try:
            user_info = w.current_user.me()
            logger.info(f"Authenticated as: {user_info.user_name}")
            try:
                w.schemas.get(f"{CATALOG}.{SCHEMA}")
                logger.info(f"Verified access to {CATALOG}.{SCHEMA}")
            except Exception:
                logger.warning(
                    f"Schema {CATALOG}.{SCHEMA} not found. Continuing to clean other resources."
                )
            return True
        except Exception as e:
            print(e)
            logger.error(f"Authentication Check Failed: {e}")
            return False

    def safe_delete(action_name, func, is_critical=True, *args, **kwargs):
        """
        Handles the deletion of resources with idempotency and dependency gating.

        This function attempts to delete a specified resource using the provided
        function. It includes error handling to skip resources that are already
        deleted and logs the success or failure of the deletion process. Critical
        deletions (marked by `is_critical=True`) will abort the script if they fail.
        It also skips cleanup steps if a placeholder config is detected

        Args:
            action_name (str): The name of the action being performed.
            func (callable): The function to call to delete