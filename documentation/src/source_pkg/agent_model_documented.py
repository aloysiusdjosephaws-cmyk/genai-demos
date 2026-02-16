import uuid
import mlflow
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
from langgraph.prebuilt import create_react_agent
#from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool
from langgraph.checkpoint.memory import MemorySaver
from databricks_langchain import ChatDatabricks, UCFunctionToolkit

class ElectronicsAgent(ResponsesAgent):
    """
    An agent designed to assist users in finding products from an electronics catalog,
    leveraging a LangGraph React agent with Databricks Chat and function toolkit capabilities.

    The agent prioritizes searching the catalog and, if needed, falls back to the foundational
    model. It's designed to follow specific guidelines for product recommendations and
    specification responses.
    """
    def __init__(self):
        """
        Initializes the ElectronicsAgent.  The agent object is initialized to None
        and loaded in the load_context function.
        """
        self.agent = None

    def load_context(self, context=None):
        """
        Loads the context and initializes the LangGraph agent.

        Args:
            context (Optional[dict]): A dictionary containing configuration parameters
                for the agent, including the LLM endpoint, temperature, and function name.
                If None, default values will be used.

        """
        #auto log
        mlflow.langchain.autolog()

        config = context.model_config if context and context.model_config else {}
        print(config)
        llm_endpoint = config.get("llm_model")
        #vs_index_name = config.get("vs_index_name")
        temp = float(config.get("llm_temperature"))
        #vs_endpoint_name = config.get("vs_endpoint_name")
        function_name = config.get("function_name") 

        llm = ChatDatabricks(endpoint=llm_endpoint, temperature=temp)
        
        uc_toolkit = UCFunctionToolkit(functions=[function_name])

        #retriever_tool = VectorSearchRetrieverTool(
        #    index_name=vs_index_name,
        #    tool_name=f"search_{vs_endpoint_name}",
        #    tool_description=f"Search tool for {vs_endpoint_name}",
        #    search_kwargs={"k": 3}
        #)

        system_instructions = (
            "You are an expert Product Discovery Assistant. "
            "Always retun a response. If you cant find any thing say so."
            "Your primary goal is to help users find the right products from our catalog."
            "But if you cant find anything from catalog get from foundational model but say that and provide references.\n\n"
            "GUIDELINES:\n"
            "1. When a user asks for product recommendations or specifications, ALWAYS use the search tools first.\n"
            "2. If the search returns multiple products, summarize the key differences in a bulleted list.\n"
            "3. Use the 'description' field to explain why a product matches the user's specific needs.\n"
            "4. If the search results have a low similarity score (below 0.5), mention that these are 'potential matches' "
            "but may not perfectly fit the request.\n"
            "5. Do not hallucinate product names or features not found in catalog or from foundational model"            
        )

        #Hybrid search does semantic search for description and keyword search for all columns (as I did not specify columns to sync) in create_vector_index.py
        #and returns only the fields the select statement returns, which is sent as context along with original question to LLM

        # Build LangGraph Agent
        self.agent = create_react_agent(
            model=llm,
            #tools=[retriever_tool],
            tools=uc_toolkit.tools,
            prompt=system_instructions,
            checkpointer=MemorySaver(),
        )

    #@mlflow.trace(span_type="AGENT")
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """
        Generates a response based on the given request using the initialized LangGraph agent.

        Args:
            request (ResponsesAgentRequest): The request object containing input messages.

        Returns:
            ResponsesAgentResponse: The response object containing the assistant's output.
        """
        if self.agent is None:
            self.load_context()
        context