import os
import asyncio
from llama_parse import LlamaParse
from typing import List


async def extract_text_from_directory_async(pdf_dir: str) -> List[str]:
    """
    Extract text asynchronously from all PDF files in the specified directory.

    Args:
        pdf_dir (str): Path to the directory containing PDF files.

    Returns:
        List[str]: A list of extracted text, one entry per PDF file.
    """
    if not os.path.exists(pdf_dir) or not os.path.isdir(pdf_dir):
        raise ValueError(f"The directory '{pdf_dir}' does not exist or is not a valid directory.")

    input_files = [
        os.path.join(pdf_dir, file_name)
        for file_name in os.listdir(pdf_dir)
        if file_name.lower().endswith('.pdf')
    ]

    if not input_files:
        print("No files uploaded by the user.")
        return []

    parser = LlamaParse(
        api_key=os.getenv("LLAMA_API_KEY"),
        result_type="text",
        premium_mode=False
    )

    tasks = [parser.aload_data(file) for file in input_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Ensure compatibility with the original return structure
    extracted_texts = []
    for result in results:
        if isinstance(result, Exception):
            print(f"Error processing file: {result}")
        elif isinstance(result, list):
            # Flatten the list of text objects into plain text
            extracted_texts.extend([doc.text for doc in result])
        else:
            extracted_texts.append(result.text)  # Single document case

    return extracted_texts