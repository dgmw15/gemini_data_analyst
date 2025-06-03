# Standard library imports
import json
import os
import time
from datetime import datetime

# Third-party imports
import polars as pl
from tqdm import tqdm

# Local imports
from text_splitter import chunk_polars_dataframe, combine_dataframes_loop
from ai import material_checker, format_elapsed_time
from prompt import material_system_instruction, dimensions_system_instruction, oryx_processing_instruction

"""
Material Checker Process Documentation

This script processes material data using AI to validate material extraction.
Below is the complete step-by-step workflow with inputs, outputs, and processes.
"""

# Initialize environment

# # Configure the API
# client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# File paths and directory setup
material_file = r"C:\Users\pauld\Desktop\Output for Material Check\Material\ConventionalMaterial_individual_result.xlsx"
dimensions_file = r"C:\Users\pauld\Desktop\Output for Dimensions QC\decoded_dimension_export.xlsx"
oryx_file = r"C:\Users\pauld\Desktop\Oryx File.xlsx"
output_dir = r"C:\Users\pauld\Desktop\Output for Material Check"
os.makedirs(output_dir, exist_ok=True)

"""
STEP 2: Material Checker Initialization
Input: 
  - material_file: Path to the Excel file containing material data
  - material_system_instruction: System instructions for the AI model
  - material_file: Path to save the output (same as input in this case)
Output: 
  - material_processer: An instance of material_checker class
Process: 
  - Creates a new material_checker object that will handle all the processing steps
"""
material_processer = material_checker(material_file, material_system_instruction, material_file)

"""
STEP 3: Load Excel Data into DataFrame
Input: 
  - material_file: Path to the Excel file (used through material_processer)
Output: 
  - df: Polars DataFrame containing the material data
Process: 
  - Reads the Excel file and converts it into a Polars DataFrame
"""
df = material_processer.convert_to_dataframe()
print(df)

"""
STEP 4: Convert DataFrame to JSON
Input: 
  - df: The Polars DataFrame from Step 3
Output: 
  - chunk_json: JSON string representation of the DataFrame
Process: 
  - Converts the DataFrame to a JSON string format for AI processing
"""
chunk_json = material_processer.convert_to_json_string(df)
print(chunk_json)

"""
STEP 5: Split Data into Manageable Chunks
Input: 
  - df: The full DataFrame from Step 3
  - chunk_size: 15 rows per chunk
Output: 
  - df_chunks: List of DataFrame chunks, each containing maximum 15 rows
Process: 
  - Splits the large DataFrame into smaller chunks to prevent overwhelming the AI
"""
df_chunks = chunk_polars_dataframe(df, 15)


try:
    print(f"df_chunks type: {type(df_chunks)}, length: {len(df_chunks) if df_chunks is not None else 'None'}")
    
    """
    STEP 6: Initialize Results Storage
    Input: None
    Output: all_processed_dfs - Empty list to store processed DataFrames
    Process: Creates an empty list that will hold all the processed chunk DataFrames
    """
    all_processed_dfs = []  # Create a list to store all processed DataFrames
    
    """
    STEP 7: Process Each Chunk (Main Processing Loop)
    For each chunk of 15 rows, perform the following steps:
    """
    for chunk in tqdm(df_chunks, total=len(df_chunks), desc="Processing Chunks:", leave=True):
        print(f"\nProcessing chunk...")
        
        """
        STEP 7.1: Convert Chunk to JSON
        Input: 
          - chunk: DataFrame chunk with 15 rows
        Output: 
          - chunk_json: JSON string representation of the chunk
        Process: 
          - Converts the small DataFrame chunk to a JSON string
        """
        chunk_json = material_processer.convert_to_json_string(chunk)
        print(f"chunk_json: {'Success' if chunk_json is not None else 'None'}")
        
        """
        STEP 7.2: Get AI Response for Material Validation
        Input: 
          - chunk_json: JSON string of the chunk
          - material_system_instruction: System instructions for the AI
        Output: 
          - material_response: Raw text response from the AI
        Process: 
          - Sends the JSON to the AI model with instructions
          - AI analyzes materials and returns a text response with validation results
        """
        material_response = material_processer.ai_api_response(chunk_json, material_system_instruction)
        print(f"material_response: {'Success' if material_response is not None else 'None'}")
        
        """
        STEP 7.3: Clean AI Response
        Input: 
          - material_response: Raw text from the AI
        Output: 
          - material_response_str: Cleaned JSON string 
        Process: 
          - Extracts just the JSON portion from the AI response
          - Removes any extra text/formatting that isn't valid JSON
        """
        material_response_str = material_processer.material_response_data_cleansed(material_response)
        print(f"material_response_str: {'Success' if material_response_str is not None else 'None'}")

        """
        STEP 7.4: Convert JSON Response to DataFrame
        Input: 
          - material_response_str: Cleaned JSON string
        Output: 
          - df_output: Polars DataFrame with validation results
        Process: 
          - Parses the JSON string back into a DataFrame
          - Each row now contains the original data plus AI validation
        """
        json_output = json.loads(material_response_str)
        df_output = pl.DataFrame(json_output)

        """
        STEP 7.5: Format DataFrame Types
        Input: 
          - df_output: DataFrame with validation results
        Output: 
          - df_output: DataFrame with all columns converted to string type
        Process: 
          - Ensures all column values are string type for consistency
        """
        df_output = material_processer.imposed_string_format(df_output)
        print(df_output)

        """
        STEP 7.6: Store Processed Chunk
        Input: 
          - df_output: Processed DataFrame chunk
        Output: 
          - all_processed_dfs: Updated list with the new DataFrame chunk
        Process: 
          - Adds the processed chunk to the list of all processed DataFrames
        """
        all_processed_dfs.append(df_output)
        print(f"Processed chunk DataFrame shape: {df_output.shape}")

    """
    STEP 8: Combine All Processed DataFrames
    Input: 
      - all_processed_dfs: List of processed DataFrame chunks
    Output: 
      - combined_df: Single DataFrame containing all processed data
    Process: 
      - Vertically concatenates all processed chunks into one final DataFrame
    """
    if all_processed_dfs:
        combined_df = pl.concat(all_processed_dfs, how="vertical")
        print(f"Final combined DataFrame shape: {combined_df.shape}")
        
        """
        STEP 9: Generate Output File Path
        Input: 
          - output_dir: Base directory for output
        Output: 
          - output_path: Full path with versioned filename
        Process: 
          - Creates a unique, timestamped filename
          - Adds version number if filename already exists
        """
        output_path = material_processer.get_versioned_output_path(output_dir)
        
        """
        STEP 10: Write Results to Excel
        Input: 
          - combined_df: Final combined DataFrame
          - output_path: Path to save the Excel file
        Output: 
          - Excel file saved at output_path
        Process: 
          - Writes the final DataFrame to an Excel file
        """
        material_processer.material_response_to_excel(combined_df, output_path)
        print(f"Successfully wrote to Excel: {output_path}")
    else:
        print("No DataFrames to combine")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    print(traceback.format_exc())


