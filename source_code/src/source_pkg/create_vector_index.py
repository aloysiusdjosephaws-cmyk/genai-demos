import time
from datetime import timedelta
from databricks.sdk import WorkspaceClient
from source_pkg.utils import get_config
from databricks.sdk.service.vectorsearch import (
    EndpointType, VectorIndexType, PipelineType,
    DeltaSyncVectorIndexSpecRequest,  
    EmbeddingSourceColumn            
)
import mlflow

def main():
    #auto log
    mlflow.langchain.autolog()    
    
    config = get_config()

    w = WorkspaceClient()
    
    SOURCE_TABLE = config.table_name
    VS_INDEX_NAME = config.vs_index_name
    VS_ENDPOINT_NAME = config.vs_endpoint_name
    EMBEDDING_LLM_MODEL = config.embedding_llm_model

    # Create Endpoint if missing
    if not any(e.name == VS_ENDPOINT_NAME for e in w.vector_search_endpoints.list_endpoints()):
        print(f"Creating Vector Search Endpoint: {VS_ENDPOINT_NAME}...")
        w.vector_search_endpoints.create_endpoint(
            name=VS_ENDPOINT_NAME, 
            endpoint_type=EndpointType.STANDARD
        ).result(timeout=timedelta(minutes=15))

    # Check and Create/Sync Index
    print(f"Checking if Vector Index exists: {VS_INDEX_NAME}...")
    if not any(i.name == VS_INDEX_NAME for i in w.vector_search_indexes.list_indexes(endpoint_name=VS_ENDPOINT_NAME)):
        print(f"Index {VS_INDEX_NAME} not found. Creating with Hybrid Search...")
        w.vector_search_indexes.create_index(
            name=VS_INDEX_NAME,
            endpoint_name=VS_ENDPOINT_NAME,
            primary_key="id",
            index_type=VectorIndexType.DELTA_SYNC,
            delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
                source_table=SOURCE_TABLE,
                pipeline_type=PipelineType.TRIGGERED,
                #columns_to_sync=["title", "category", "description"] # sync all columns to index
                embedding_source_columns=[
                    EmbeddingSourceColumn(
                        name="description", #embed only description for semantic search, other columns keyword search for hybrid
                        embedding_model_endpoint_name=EMBEDDING_LLM_MODEL
                    )
                ]
            )
        )
        print("Index creation request sent.")
    else:
        print(f"Index {VS_INDEX_NAME} already exists. Triggering manual sync...")
        w.vector_search_indexes.sync_index(VS_INDEX_NAME)

    # Wait for the index to be ready
    print("⏳ Waiting for initial sync to complete...")
    while True:
        status = w.vector_search_indexes.get_index(VS_INDEX_NAME).status
        if status.ready:
            print(f"Index is ready! Status: {status.message}")
            break
        elif "ERROR" in status.message.upper():
            print(f"Error detected in index status: {status.message}")
            break
        
        print(f"Current status: {status.message}. Waiting 20 seconds...")
        time.sleep(20)

# Standard boilerplate for direct execution/testing
if __name__ == "__main__":
    main()


