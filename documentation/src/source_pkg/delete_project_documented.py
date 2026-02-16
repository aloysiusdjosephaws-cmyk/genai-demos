```python
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
        Manually bridges between Python and Bundle State by unbinding a resource.

        Args:
            resource_key (str): The key of the resource to unbind.
            target (str): The target to unbind the resource from.

        Returns:
            subprocess.CompletedProcess: The result of the subprocess call.
        """
        cmd = [
            "databricks", "bundle", "deployment", "unbind", resource_key,
            "--target", target,
            #"--profile", profile
        ]
        return subprocess.run(cmd, capture_output=True, text=True)
    
def main():
    """
    Main function to perform project cleanup operations.
    """
    #auto log
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
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)

    w = WorkspaceClient()
    
    def check_permissions():
        """
        Validates identity and checks access to the schema.

        Returns:
            bool: True if authentication and schema access are successful, False otherwise.
        """
        try:
            user_info = w.current_user.me()
            logger.info(f"Authenticated as: {user_info.user_name}")
            try:
                w.schemas.get(f"{CATALOG}.{SCHEMA}")
                logger.info(f"Verified access to {CATALOG}.{SCHEMA}")
            except Exception:
                logger.warning(f"Schema {CATALOG}.{SCHEMA} not found. Continuing to clean other resources.")
            return True
        except Exception as e:
            print(e)
            logger.error(f"Authentication Check Failed: {e}")
            return False

    def safe_delete(action_name, func, is_critical=True, *args, **kwargs):
        """
        Handles idempotency and dependency gating for resource deletion.

        Args:
            action_name (str): The name of the action being performed.
            func (callable): The function to execute for deletion.
            is_critical (bool): Whether the action is critical and should halt execution on failure.
            *args: Variable length argument list to pass to the function.
            **kwargs: Arbitrary keyword arguments to pass to the function.

        Returns:
            bool: True if the action was successful or skipped, False otherwise.
        """
        try:
            if args and args[0] in [None, "", "your-app-name", "your_index_name"]:
                logger.warning(f"{action_name} skipped: Placeholder config detected.")
                return True
                
            logger.info(f"Starting: {action_name}...")
            func(*args, **kwargs)
            logger.info(f"{action_name} successful.")
            return True
        except Exception as e:
            print(e)
            err_msg = str(e).lower()
            not_found_indicators = ["not found", "404", "does not exist", "not_found"]
            
            if any(indicator in err_msg for indicator in not_found_indicators):
                logger.warning(f"{action