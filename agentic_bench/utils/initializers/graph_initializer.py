from fast_graphrag import GraphRAG
from typing import List
import os
import json
from .text_extractor import extract_text_from_directory_async
from utils.calculate_md5_hash_of_file import calculate_md5

def check_and_read_json(file_path):
    if os.path.exists(file_path):  # Check if the file exists
        with open(file_path, "r") as f:
            data = json.load(f)  # Read the JSON file
        return data
    else:
        write_json({}, file_path)
        return {} 
    
def write_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def check_if_file_has_changed(pdf_dir, graph_working_dir):
    md5_hash_json_path = os.path.join(graph_working_dir, "md5_hash_map.json")
    md5_hash_map = check_and_read_json(md5_hash_json_path)
    all_files = [f for f in os.listdir(pdf_dir) if os.path.isfile(os.path.join(pdf_dir, f))]

    have_files_changed = False
    
    for file in all_files:
        md5_hash = md5_hash_map.get(file, None)

        if(not md5_hash):
            have_files_changed = True

        new_calculated_md5_hash = calculate_md5(os.path.join(pdf_dir, file))

        if md5_hash != new_calculated_md5_hash:
            have_files_changed = True

        md5_hash_map[file] = new_calculated_md5_hash

    write_json(md5_hash_map, md5_hash_json_path)

    return have_files_changed

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

        have_files_changed = check_if_file_has_changed(pdf_dir, self.graph.working_dir)

        if not have_files_changed:
            return "Graph data already populated, no need to reindex."
        else:
            # Extract text from the directory
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