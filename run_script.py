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
from ai import data_processing_pipeline, format_elapsed_time, set_vertex_ai_mode
from prompt import material_system_instruction, dimensions_system_instruction, oryx_processing_instruction

"""
Data Processing Pipeline Documentation

This script processes data using AI to validate and analyze content.
The complete workflow processes data in chunks with async rate limiting.
"""

# =====================================================================
# CONFIGURATION SECTION - Modify these settings as needed
# =====================================================================

# 🤖 AI API SELECTION:
# Set USE_VERTEX_AI to control which API to use:
# - False = Use Standard Gemini API (DEFAULT - easier setup, good for development)
# - True  = Use Vertex AI (enterprise features, better rate limits, requires Vertex AI API key)
USE_VERTEX_AI = False  # 👈 CHANGE THIS: False=Gemini, True=Vertex AI

# 🎯 MODEL SELECTION:
# Specify which AI model to use regardless of API choice:
# - "gemini-2.0-flash-001" = Latest Gemini 2.0, best performance (RECOMMENDED)
# - "gemini-1.5-pro"       = Stable Gemini 1.5 Pro, proven reliability  
# - "gemini-1.5-flash"     = Faster Gemini 1.5 Flash, cost-effective
# - "gemini-2.5-flash-preview-05-20" = Preview version (may be unstable)
MODEL_NAME = "gemini-2.0-flash-001"  # 👈 CHANGE THIS: Specify your preferred model

# 📁 FILE PATHS AND DIRECTORIES:
# Update these paths to match your local file structure
material_file = r"C:\Users\pauld\Desktop\Output for Material Check\Material\ConventionalMaterial_individual_result.xlsx"
dimensions_file = r"C:\Users\pauld\Desktop\Oryx Test\Test.xlsx"
oryx_file = r"C:\Users\pauld\Desktop\Oryx Test\Test.xlsx"

# 📂 OUTPUT DIRECTORIES:
# Specify where processed files should be saved
dimensions_output_dir = r"C:\Users\pauld\Desktop\Output for Dimensions QC"
material_output_dir = r"C:\Users\pauld\Desktop\Output for Material Check\Material AI QC"
oryx_output_dir = r"C:\Users\pauld\Desktop\Oryx Test"
default_output_dir = r"C:\Users\pauld\Desktop\Output for AI QC"

# 🎯 PROCESSING SELECTION:
# Choose which prompt and input file to use for processing:
# Import the prompts you want to use
prompt = oryx_processing_instruction  # 👈 CHANGE THIS: Select your prompt
input_file = dimensions_file  # 👈 CHANGE THIS: Select your input file

# ⚡ RATE LIMITING CONFIGURATION:
# Controls how fast API requests are sent (to avoid hitting rate limits)
# Standard Gemini: 4 requests per minute is safe
# Vertex AI: Can usually handle higher rates, but 4/min is conservative
REQUESTS_PER_WINDOW = 4  # Number of requests allowed
TIME_WINDOW = 60  # Time window in seconds (1 minute)
REQUEST_INTERVAL = TIME_WINDOW / REQUESTS_PER_WINDOW

# 📊 DATA PROCESSING CONFIGURATION:
# Controls how data is split into chunks for processing
CHUNK_SIZE = 15  # 👈 CHANGE THIS: Number of rows per chunk (default: 15)
                 # Smaller chunks = more API calls but faster individual processing
                 # Larger chunks = fewer API calls but slower individual processing

# =====================================================================
# END CONFIGURATION SECTION
# ⚠️  DO NOT MODIFY ANYTHING BELOW UNLESS YOU KNOW WHAT YOU'RE DOING
# =====================================================================

# Configure AI API mode
print(f"=== AI CONFIGURATION ===")
print(f"Using API: {'Vertex AI' if USE_VERTEX_AI else 'Standard Gemini'}")
print(f"Model: {MODEL_NAME}")
set_vertex_ai_mode(USE_VERTEX_AI)
print("=" * 25)

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

# Create a rate limiter semaphore to control concurrent requests
rate_limiter = asyncio.Semaphore(REQUESTS_PER_WINDOW)

# Initialize data processor with API configuration
data_processor = data_processing_pipeline(
    df_material_file=input_file, 
    system_instructions=prompt, 
    path_for_excel=output_dir,
    use_vertex_ai=USE_VERTEX_AI,  # Pass the API configuration to the processor
    model_name=MODEL_NAME  # Pass the model name to the processor
)

print(f"\n=== PROCESSOR CONFIGURATION ===")
print(f"API Mode: {'Vertex AI' if data_processor.use_vertex_ai else 'Standard Gemini'}")
print(f"Model: {data_processor.get_model_name()}")
print("=" * 32)

# Load data into DataFrame
df = data_processor.convert_to_dataframe()
print(f"Loaded DataFrame with shape: {df.shape}")
print("\n=== INITIAL DATAFRAME ===")
print(df)
print("=========================\n")

# Convert DataFrame to JSON for verification
chunk_json = data_processor.convert_to_json_string(df)
print("DataFrame converted to JSON format")

# Split data into manageable chunks
df_chunks = chunk_polars_dataframe(df, CHUNK_SIZE)
print(f"Data split into {len(df_chunks)} chunks")

async def process_chunk(chunk, data_processor, prompt, chunk_index):
    """
    Process a single chunk asynchronously with rate limiting and automatic token size reduction.
    
    Input:
        chunk: DataFrame chunk with rows
        data_processor: Instance of data_processing_pipeline
        prompt: System instructions for the AI
        chunk_index: Index of the chunk for logging
    Output:
        processed_df: DataFrame with validation results
    Process:
        - Converts the chunk to JSON
        - Validates token count before API call
        - If token limit exceeded, automatically reduces chunk size and processes sub-chunks
        - Sends to AI model asynchronously with rate limiting
        - Cleans response and converts back to DataFrame
    """
    try:
        chunk_start_time = time.time()
        
        # Convert chunk to JSON
        chunk_json = data_processor.convert_to_json_string(chunk)
        api_type = "Vertex AI" if data_processor.use_vertex_ai else "Gemini"
        print(f"Chunk {chunk_index}: JSON prepared, using {api_type}")
        
        # 🔍 CHECK TOKEN LIMITS AND AUTO-REDUCE IF NEEDED
        current_chunk_size = len(chunk)
        is_valid, token_count, safe_limit = data_processor.validate_content_tokens(chunk_json, current_chunk_size)
        
        if not is_valid:
            print(f"🔄 Chunk {chunk_index}: Token limit exceeded, auto-reducing chunk size...")
            
            # Calculate optimal chunk size
            optimal_size = data_processor.calculate_optimal_chunk_size(current_chunk_size, token_count, safe_limit)
            
            # Split chunk into smaller sub-chunks
            sub_chunks = data_processor.split_chunk_intelligently(chunk, optimal_size)
            
            print(f"🔄 Chunk {chunk_index}: Processing {len(sub_chunks)} sub-chunks...")
            
            # Process each sub-chunk
            all_sub_results = []
            for i, sub_chunk in enumerate(sub_chunks):
                print(f"   📦 Processing sub-chunk {chunk_index}.{i+1} ({len(sub_chunk)} rows)...")
                
                # Apply rate limiting for each sub-chunk
                async with rate_limiter:
                    # Convert sub-chunk to JSON
                    sub_chunk_json = data_processor.convert_to_json_string(sub_chunk)
                    
                    print(f"   📦 Sub-chunk {chunk_index}.{i+1}: Sending to {api_type} API...")
                    # Add delay to ensure we don't exceed rate limit
                    await asyncio.sleep(REQUEST_INTERVAL)
                    
                    # Get AI response for sub-chunk (no need to re-validate tokens)
                    ai_response = await data_processor.ai_api_response_async(sub_chunk_json, prompt, None)
                    print(f"   📦 Sub-chunk {chunk_index}.{i+1}: {api_type} API response received")
                
                # Clean AI response
                ai_response_str = data_processor.response_data_cleansed(ai_response)
                
                # Convert JSON response to DataFrame
                json_output = json.loads(ai_response_str)
                df_output = pl.DataFrame(json_output)
                
                # Format DataFrame types
                df_output = data_processor.imposed_string_format(df_output)
                all_sub_results.append(df_output)
                
                print(f"   ✅ Sub-chunk {chunk_index}.{i+1}: Processed ({df_output.shape[0]} rows)")
            
            # Combine all sub-chunk results
            combined_df = pl.concat(all_sub_results, how="vertical") if all_sub_results else pl.DataFrame()
            
            # Calculate and display chunk processing time
            chunk_end_time = time.time()
            chunk_elapsed_time = chunk_end_time - chunk_start_time
            print(f"Chunk {chunk_index}: {format_elapsed_time(chunk_elapsed_time)} (auto-reduced)")
            print(f"Chunk {chunk_index}: Final processed DataFrame shape: {combined_df.shape}")
            
            return combined_df
            
        else:
            # ✅ NORMAL PROCESSING - TOKEN LIMITS OK
            print(f"✅ Chunk {chunk_index}: Token validation passed, proceeding normally...")
            
            # Apply rate limiting
            async with rate_limiter:
                print(f"Chunk {chunk_index}: Sending to {api_type} API...")
                # Add delay to ensure we don't exceed rate limit
                await asyncio.sleep(REQUEST_INTERVAL)
                
                # Get AI response asynchronously (token validation already done)
                ai_response = await data_processor.ai_api_response_async(chunk_json, prompt, None)
                print(f"Chunk {chunk_index}: {api_type} API response received")
            
            # Clean AI response
            ai_response_str = data_processor.response_data_cleansed(ai_response)
            
            # Convert JSON response to DataFrame
            json_output = json.loads(ai_response_str)
            df_output = pl.DataFrame(json_output)

            # Format DataFrame types
            df_output = data_processor.imposed_string_format(df_output)
            
            # Calculate and display chunk processing time
            chunk_end_time = time.time()
            chunk_elapsed_time = chunk_end_time - chunk_start_time
            print(f"Chunk {chunk_index}: {format_elapsed_time(chunk_elapsed_time)}")
            print(f"Chunk {chunk_index}: Processed DataFrame shape: {df_output.shape}")
            
            return df_output
            
    except Exception as e:
        print(f"Error processing chunk {chunk_index}: {e}")
        return None

async def process_all_chunks(df_chunks, data_processor, prompt):
    """
    Process all chunks asynchronously with rate limiting.
    
    Input:
        df_chunks: List of DataFrame chunks
        data_processor: Instance of data_processing_pipeline
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
            process_chunk(chunk, data_processor, prompt, i)
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
        all_processed_dfs = await process_all_chunks(df_chunks, data_processor, prompt)
        
        # Calculate and display total processing time
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\n{format_elapsed_time(elapsed_time)}")
        
        if all_processed_dfs:
            combined_df = pl.concat(all_processed_dfs, how="vertical")
            print(f"Final combined DataFrame shape: {combined_df.shape}")
            
            output_path = data_processor.get_versioned_output_path(output_dir, prefix=output_prefix)
            data_processor.response_to_excel(combined_df, output_path)
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
