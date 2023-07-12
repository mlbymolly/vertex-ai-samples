from typing import Any, Mapping, List, Dict, Optional, Tuple, Sequence, Union
from pydantic import BaseModel, root_validator
from google.cloud import discoveryengine_v1beta
import vertexai
from vertexai.preview.language_models import TextGenerationModel
from google.protobuf.json_format import MessageToDict
from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens
from langchain.chains.base import Chain
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import LLMChain
from langchain.callbacks.manager import CallbackManagerForChainRun
from typing import List
from pydantic import BaseModel
import json

#@title ### You will need to update these values
VERTEX_API_PROJECT = 'vtxdemos' #@param {"type": "string"}
VERTEX_API_LOCATION = 'us-central1' #@param {"type": "string"}
vertexai.init(project=VERTEX_API_PROJECT, location=VERTEX_API_LOCATION)
class _VertexCommon(BaseModel):
    """Wrapper around Vertex AI large language models.
    To use, you should have the
    ``google-cloud-aiplatform`` python package installed.
    """
    client: Any = None #: :meta private:
    model_name: str = "text-bison@001"
    """Model name to use."""
    temperature: float = 0.2
    """What sampling temperature to use."""
    top_p: int = 0.8
    """Total probability mass of tokens to consider at each step."""
    top_k: int = 40
    """The number of highest probability tokens to keep for top-k filtering."""
    max_output_tokens: int = 200
    """The maximum number of tokens to generate in the completion."""
    @property
    def _default_params(self) -> Mapping[str, Any]:
        """Get the default parameters for calling Vertex AI API."""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens
        }
    def _predict(self, prompt: str, stop: Optional[List[str]]) -> str:
        res = self.client.predict(prompt, **self._default_params)
        return self._enforce_stop_words(res.text, stop)
    def _enforce_stop_words(self, text: str, stop: Optional[List[str]]) -> str:
        if stop:
            return enforce_stop_tokens(text, stop)
        return text
    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "vertex_ai"
class VertexLLM(_VertexCommon, LLM):
    model_name: str = "text-bison@001"
    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            from vertexai.preview.language_models import TextGenerationModel
        except ImportError:
            raise ValueError(
                "Could not import Vertex AI LLM python package. "
            )
        try:
            values["client"] = TextGenerationModel.from_pretrained(values["model_name"])
        except AttributeError:
            raise ValueError(
                "Could not set Vertex Text Model client."
            )
        return values
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call out to Vertex AI's create endpoint.
        Args:
            prompt: The prompt to pass into the model.
        Returns:
            The string generated by the model.
        """
        return self._predict(prompt, stop)
#@title Additional Enterprise Search Classes and helper functions
class EnterpriseSearchRetriever():
  """Retriever class to fetch documents or snippets from a search engine."""
  def __init__(self,
               project,
               search_engine,
               location='global',
               serving_config_id='default_config'):
    self.search_client = discoveryengine_v1beta.SearchServiceClient()
    self.serving_config: str = self.search_client.serving_config_path(
            project=project,
            location=location,
            data_store=search_engine,
            serving_config=serving_config_id,
            )
  def _search(self, query:str):
    """Helper function to run a search"""
    request = discoveryengine_v1beta.SearchRequest(serving_config=self.serving_config, query=query)
    return self.search_client.search(request)
  def get_relevant_snippets(self, query: str) -> List[str]:
    """Retrieve snippets from a search query"""
    res = self._search(query)
    snippets = []
    for result in res.results:
        data = MessageToDict(result.document._pb)
        if data.get('derivedStructData', {}) == {}:
            snippets.append(json.dumps(data.get('structData', {})))
        else:
            link = data.get('derivedStructData', {}).get('link')
            snippets.extend([d.get('snippet') + f"\t{link}" for d in data.get('derivedStructData', {}).get('snippets', []) if d.get('snippet') is not None])
    with open("snippets_out.txt", "w") as f:
        for i in snippets:
            f.write(i+"\n")
    return snippets
class EnterpriseSearchChain(Chain):
    """Chain that queries an Enterprise Search Engine and summarizes the responses."""
    chain: Optional[LLMChain]
    search_client: Optional[EnterpriseSearchRetriever]
    def __init__(self,
                 project,
                 search_engine,
                 chain,
                 location='global',
                 serving_config_id='default_config'):
        super().__init__()
        self.chain = chain
        self.search_client = EnterpriseSearchRetriever(project, search_engine, location, serving_config_id)
    @property
    def input_keys(self) -> List[str]:
        return ['query']
    @property
    def output_keys(self) -> List[str]:
        return ['summary']
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        _run_manager = CallbackManagerForChainRun.get_noop_manager()
        query = inputs['query']
        print(query)
        _run_manager.on_text(query, color="green", end="\n", verbose=self.verbose)
        snippets = self.search_client.get_relevant_snippets(query)
        _run_manager.on_text(snippets, color="white", end="\n", verbose=self.verbose)
        summary = self.chain.run(snippets)
        return {'summary': summary}
    @property
    def _chain_type(self) -> str:
        return "google_enterprise_search_chain"