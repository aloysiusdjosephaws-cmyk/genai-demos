import sys
import os
import logging
from databricks.sdk import WorkspaceClient
import mlflow
from source_pkg.utils import get_config
import subprocess

class BundleTools:
    @staticmethod
    def unbind_resource(resource_key, target):
        """Manual bridge between Python and Bundle State"""
        cmd = [
            "databricks", "bundle", "deployment", "unbind", resource_key,
            "--target", target,
            #"--profile", profile
        ]
        return subprocess.run(cmd, capture_output=True, text=True)
    
def main():
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
        """Validates identity. Warns if schema is missing but doesn't block."""
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
        """Handles idempotency and dependency gating."""
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
                logger.warning(f"{action_name} skipped: Resource already gone.")
                return True
            else:
                logger.error(f"{action_name} failed: {e}")
                if is_critical:
                    logger.critical(f"Aborting: {action_name} failure blocks downstream steps.")
                    sys.exit(1)
                return False

    def cleanup():
        if not check_permissions():
            sys.exit(1)
        logger.info("--- Starting Full Project Cleanup ---")

        # 1. DELETE APP
        safe_delete("Delete App", w.apps.delete, True, APP_NAME)

        # 2. SERVING ENDPOINT
        safe_delete("Delete Serving Endpoint", w.serving_endpoints.delete, True, SERVING_ENDPOINT_NAME)

        # 3. VECTOR SEARCH INDEX (Workspace Level)
        safe_delete("Delete Vector Search Index", w.vector_search_indexes.delete_index, True, index_name=VS_INDEX_NAME)

        # 3b. VECTOR SEARCH ENDPOINT (The Cluster)
        # Delete the cluster after the index is gone ONLY IF NOT SHARING WITH OTHERS
        safe_delete("Delete Vector Search Endpoint", w.vector_search_endpoints.delete_endpoint, 
                    True, endpoint_name=VS_ENDPOINT_NAME)
        
        # 4. TABLE (with internal INDEX) (Unity Catalog Level)
        safe_delete("Delete Unity Catalog Table Index", w.tables.delete, True, TABLE_NAME)

        # 5. MLFLOW EXPERIMENT
        def del_exp(path):
            exp = mlflow.get_experiment_by_name(path)
            if exp: mlflow.delete_experiment(exp.experiment_id)
            else: raise Exception("404")
        safe_delete("Delete MLflow Experiment", del_exp, False, EXPERIMENT_PATH)

        # 6. CLEAR MODEL VERSIONS
        try:
            models = w.registered_models.list(catalog_name=CATALOG, schema_name=SCHEMA)
            for m in models:
                versions = w.model_versions.list(full_name=m.full_name)
                for v in versions:
                    safe_delete(f"Delete Version {v.version} of {m.name}", 
                                w.model_versions.delete, False, m.full_name, v.version)
                safe_delete(f"Delete Model Container {m.name}", 
                            w.registered_models.delete, False, m.full_name)
        except Exception:
            logger.info("No models found to clear.")

        # 7. CLEAR VOLUMES (Keep the Schema, wipe the files)
        try:
            volumes = w.volumes.list(catalog_name=CATALOG, schema_name=SCHEMA)
            for vol in volumes:
                safe_delete(f"Delete Volume {vol.name}", w.volumes.delete, False, vol.full_name)
            logger.info(f"Schema {CATALOG}.{SCHEMA} is now empty but remains active.")
        except Exception:
            logger.info("No volumes found to clear.")

        # 8. unbind app
        BundleTools.unbind_resource(APP_NAME, ALIAS)

        # 9. DROP SCHEMA (The "Nuclear" Option)
        # Adding 'CASCADE' via SQL is often more reliable than the SDK delete
        #try:
        #    logger.info(f"Dropping Schema {CATALOG}.{SCHEMA} CASCADE...")
        #    spark.sql(f"DROP SCHEMA IF EXISTS {CATALOG}.{SCHEMA} CASCADE")
        #    logger.info("Schema and all remaining contents (tables/volumes) deleted.")
        #except Exception as e:
        #    logger.error(f"Failed to drop schema: {e}")

        logger.info("--- Cleanup Finished Successfully ---")

    # call the cleanup
    cleanup()

if __name__ == "__main__":
    main()