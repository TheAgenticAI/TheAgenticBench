# agentic-one
- install dependencies using `pip install -r requirements.txt`
- configure `.env` (using example `.env.copy`)
- either run `python -m src.main` in root folder
- or run `uvicorn --reload --access-log --host 0.0.0.0 --port 8001 src.main:app` to use with frontend

### RAG Agent

#### Indexing and Querying
The RAG Agent uses **Fast-graph-RAG** for efficient indexing and querying.

#### Optional Agent Activation
The RAG Agent is optional and activates only when:
1. The user has uploaded data to the `PDF_Data_Folder` folder, or
2. A memory graph already exists in the system.

#### File Upload
- Upload your files to the `PDF_Data_Folder` folder to enable data processing by the RAG Agent.
- Remove the `.gitkeep` file from the `graph_data_folder`.

#### Data Indexing
- After your files are indexed, the memory graph will be saved in the `graph_data_folder`.
- Once indexing is complete, you can safely remove the uploaded files from the `PDF_Data_Folder` folder. This prevents unnecessary text extraction during subsequent runs of the Agent.

#### Text Extraction
- The **Llama-Parser** is used for extracting text from the uploaded files.

#### API Key Configuration
- Ensure the `LLAMA_PARSER_API_KEY` is set in your `.env` file.
- Obtain your API key by visiting [LlamaIndex Cloud](https://llamaindex.cloud).

#### Premium Mode Configuration
- By default, `is_premium_mode` is set to `False`.
- Enable `True` only if you are working with very complex documents. However, keep in mind that this consumes all free credits quickly.
- Unless you have highly complex documents or a Pro version of Llama Index, it is recommended to keep this setting as `False`.

#### Customizing Domain, Example Queries, and Entity Types
The RAG Agent relies on **Domain**, **Example Queries**, and **Entity Types** to construct a task-specific knowledge graph:
- **Domain**: Focuses the graph on specific aspects of your data (e.g., finance, healthcare).
- **Example Queries**: Guides the system by specifying likely user questions.
- **Entity Types**: Identifies key entities to extract (e.g., person, place, event).

The current defaults are tuned for financial data like 10-K and 10-Q filings. If your use case differs, update these values in:

`src/utils/initializers/rag_constants.py`

Modify these variables as per your dataset for optimal results.
