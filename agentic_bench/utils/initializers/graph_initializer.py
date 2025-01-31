from fast_graphrag import GraphRAG
from typing import List
import os
from .text_extractor import extract_text_from_directory_async


class GraphInitializer:
    def __init__(self, working_dir: str, domain: str, example_queries: List[str], entity_types: List[str]):
        """
        Initialize the GraphRAG system.

        Args:
            working_dir (str): Directory to store graph-related data.
            domain (str): Domain of the graph for context.
            example_queries (List[str]): Example queries for better understanding.
            entity_types (List[str]): Types of entities to index.
        """
        self.graph = GraphRAG(
            working_dir=working_dir,
            domain=domain,
            example_queries="\n".join(example_queries),
            entity_types=entity_types,
        )

    async def ingest_data(self, pdf_dir: str) -> str:

        """
         Ingest extracted text into the graph, handling all scenarios.

         Algorithm:
         1. Check if the working directory (memory folder) is empty:
            - If the working directory has no files, set `is_memory_empty` to True.
            - Otherwise, set `is_memory_empty` to False.

         2. Extract text from the provided `pdf_dir` using `TextExtractor`:
            - If the directory is empty or no valid PDF files are found, handle accordingly:
                a. If `is_memory_empty` is True:
                    - Return: "No files uploaded and no existing memory found. Graph memory is empty."
                b. If `is_memory_empty` is False:
                    - Return: "No files uploaded, but existing graph memory is present."

         3. If valid files are found in `pdf_dir`:
            - Combine all extracted text into a single string `whole_text`.
            - Insert `whole_text` into the graph memory using `self.graph.insert`.

         4. Handle any exceptions during the insertion process and return a status message:
            - Success: Return "Data successfully ingested into the graph."
            - Failure: Return an error message indicating the failure reason.

         Args:
             pdf_dir (str): Path to the directory containing PDF files.

         Returns:
             str: Status message indicating the ingestion process result.
         """
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        # Check if the working directory (memory) is empty
        is_memory_empty = not os.listdir(self.graph.working_dir)
        extracted_texts = await extract_text_from_directory_async(pdf_dir)

        if not extracted_texts:  # No valid files in the directory
            if is_memory_empty:
                return "No files uploaded and no existing memory found. Graph memory is empty."
            else:
                return "No files uploaded, but existing graph memory is present."

        # Combine all text and ingest into the graph
        whole_text = "".join(extracted_texts)  # Ensure it's a flat list of strings
        try:
            # Properly await the async_insert method
            await self.graph.async_insert(whole_text)
            return "Data successfully ingested into the graph."
        except Exception as e:
            return f"Failed to ingest data into the graph: {e}"


    def query(self, question:str):
        return self.graph.query(question)