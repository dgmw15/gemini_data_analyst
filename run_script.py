# Standard library imports
import json
import os
import time
import asyncio
from datetime import datetime

# Third-party imports
import polars as pl
from tqdm import tqdm

# Local imports
from text_splitter import chunk_polars_dataframe
from ai import material_checker, format_elapsed_time
from prompt import material_system_instruction, dimensions_system_instruction, oryx_processing_instruction

"""
Material Checker Process Documentation

This script processes material data using AI to validate material extraction.
The complete workflow processes data in chunks with async rate limiting.
"""

# File paths and directory setup
material_file = r"C:\Users\pauld\Desktop\Output for Material Check\Material\ConventionalMaterial_individual_result.xlsx"
dimensions_file = r"C:\Users\pauld\Desktop\Oryx Test\Test.xlsx"
oryx_file = r"C:\Users\pauld\Desktop\Oryx Test\Test.xlsx"

# Output directories
dimensions_output_dir = r"C:\Users\pauld\Desktop\Output for Dimensions QC"
material_output_dir = r"C:\Users\pauld\Desktop\Output for Material Check\Material AI QC"
oryx_output_dir = r"C:\Users\pauld\Desktop\Oryx Test"
default_output_dir = r"C:\Users\pauld\Desktop\Output for AI QC"

# Define which prompt to use
prompt = oryx_processing_instruction
# Define which file to process
input_file = dimensions_file

# Select output directory based on input file
if input_file == dimensions_file:
    output_dir = dimensions_output_dir
    output_prefix = "Dimensions_Response"
elif input_file == material_file:
    output_dir = material_output_dir
    output_prefix = "Material_Response"
elif input_file == oryx_file:
    output_dir = oryx_output_dir
    output_prefix = "Oryx_Response"
else:
    output_dir = default_output_dir
    output_prefix = "AI_Response"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Define rate limit for API requests (4 requests per minute)
REQUESTS_PER_WINDOW = 4  # requests
TIME_WINDOW = 60  # seconds (1 minute)
REQUEST_INTERVAL = TIME_WINDOW / REQUESTS_PER_WINDOW  # 15 seconds between requests

# Create a rate limiter semaphore to control concurrent requests
rate_limiter = asyncio.Semaphore(REQUESTS_PER_WINDOW)

# Initialize material processor
material_processer = material_checker(input_file, prompt, output_dir)

# Load data into DataFrame
df = material_processer.convert_to_dataframe()
print(f"Loaded DataFrame with shape: {df.shape}")
print("\n=== INITIAL DATAFRAME ===")
print(df)
print("=========================\n")

# Convert DataFrame to JSON for verification
chunk_json = material_processer.convert_to_json_string(df)
print("DataFrame converted to JSON format")

# Split data into manageable chunks
df_chunks = chunk_polars_dataframe(df, 15)
print(f"Data split into {len(df_chunks)} chunks")

async def process_chunk(chunk, material_processer, prompt, chunk_index):
    """
    Process a single chunk asynchronously with rate limiting.
    
    Input:
        chunk: DataFrame chunk with rows
        material_processer: Instance of material_checker
        prompt: System instructions for the AI
        chunk_index: Index of the chunk for logging
    Output:
        processed_df: DataFrame with validation results
    Process:
        - Converts the chunk to JSON
        - Sends to AI model asynchronously with rate limiting
        - Cleans response and converts back to DataFrame
    """
    try:
        chunk_start_time = time.time()
        
        # Convert chunk to JSON
        chunk_json = material_processer.convert_to_json_string(chunk)
        print(f"Chunk {chunk_index}: JSON prepared")
        
        # Apply rate limiting
        async with rate_limiter:
            print(f"Chunk {chunk_index}: Sending to AI API...")
            # Add delay to ensure we don't exceed rate limit
            await asyncio.sleep(REQUEST_INTERVAL)
            
            # Get AI response asynchronously
            material_response = await material_processer.ai_api_response_async(chunk_json, prompt)
            print(f"Chunk {chunk_index}: API response received")
        
        # Clean AI response
        material_response_str = material_processer.material_response_data_cleansed(material_response)
        
        # Convert JSON response to DataFrame
        json_output = json.loads(material_response_str)
        df_output = pl.DataFrame(json_output)

        # Format DataFrame types
        df_output = material_processer.imposed_string_format(df_output)
        
        # Calculate and display chunk processing time
        chunk_end_time = time.time()
        chunk_elapsed_time = chunk_end_time - chunk_start_time
        print(f"Chunk {chunk_index}: {format_elapsed_time(chunk_elapsed_time)}")
        print(f"Chunk {chunk_index}: Processed DataFrame shape: {df_output.shape}")
        
        return df_output
    except Exception as e:
        print(f"Error processing chunk {chunk_index}: {e}")
        return None

async def process_all_chunks(df_chunks, material_processer, prompt):
    """
    Process all chunks asynchronously with rate limiting.
    
    Input:
        df_chunks: List of DataFrame chunks
        material_processer: Instance of material_checker
        prompt: System instructions for the AI
    Output:
        all_processed_dfs: List of processed DataFrames
    Process:
        - Creates tasks for processing each chunk with rate limiting
        - Awaits all tasks to complete
        - Returns list of processed DataFrames
    """
    # Create a task for each chunk
    tasks = []
    for i, chunk in enumerate(df_chunks):
        task = asyncio.create_task(
            process_chunk(chunk, material_processer, prompt, i)
        )
        tasks.append(task)
    
    # Use tqdm to show progress
    all_processed_dfs = []
    for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing Chunks:"):
        df_output = await task
        if df_output is not None:
            all_processed_dfs.append(df_output)
    
    return all_processed_dfs

async def main():
    """
    Main function to run the entire async processing workflow.
    
    Process:
        - Runs the async processing with rate limiting
        - Combines results
        - Saves to Excel
    """
    try:
        print(f"Processing {len(df_chunks)} chunks in parallel")
        print(f"Rate limited to {REQUESTS_PER_WINDOW} requests every {TIME_WINDOW} seconds")
        print(f"Each request spaced {REQUEST_INTERVAL:.1f} seconds apart")
        
        # Start overall timing
        start_time = time.time()
        
        # Process all chunks
        all_processed_dfs = await process_all_chunks(df_chunks, material_processer, prompt)
        
        # Calculate and display total processing time
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\n{format_elapsed_time(elapsed_time)}")
        
        if all_processed_dfs:
            combined_df = pl.concat(all_processed_dfs, how="vertical")
            print(f"Final combined DataFrame shape: {combined_df.shape}")
            
            output_path = material_processer.get_versioned_output_path(output_dir, prefix=output_prefix)
            material_processer.material_response_to_excel(combined_df, output_path)
            print(f"Successfully wrote to Excel: {output_path}")
        else:
            print("No DataFrames to combine")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())

# Run the main function
if __name__ == "__main__":
    # Start total script timing
    total_script_start = time.time()
    
    # Run the main async function
    asyncio.run(main())
    
    # Calculate and display total script time
    total_script_end = time.time()
    total_elapsed = total_script_end - total_script_start
    print(f"\nTotal Script {format_elapsed_time(total_elapsed)}")
