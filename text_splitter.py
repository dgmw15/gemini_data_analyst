import polars as pl
import math
from tqdm import tqdm

def chunk_polars_dataframe(df: pl.DataFrame, chunk_size: int = 100) -> list[pl.DataFrame]:
    """
    Splits a Polars DataFrame into chunks without duplication.
    
    Args:
        df (pl.DataFrame): The DataFrame to split into chunks
        chunk_size (int): Number of rows per chunk (default: 100)
    
    Returns:
        list[pl.DataFrame]: List of DataFrame chunks
    """
    if df is None or len(df) == 0:
        print("Warning: Empty or None DataFrame provided")
        return []

    total_rows = len(df)
    num_chunks = math.ceil(total_rows / chunk_size)
    chunks = []

    print(f"Total rows: {total_rows}")
    print(f"Chunk size: {chunk_size}")
    print(f"Expected number of chunks: {num_chunks}")

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_rows)
        
        # Create chunk and ensure columns are preserved
        chunk = df.slice(start_idx, end_idx - start_idx)
        chunk = chunk.select(df.columns)
        
        if len(chunk) > 0:
            chunks.append(chunk)
            print(f"Created chunk {i+1} with {len(chunk)} rows")

    print(f"Actually created {len(chunks)} chunks")
    return chunks

def combine_dataframes_loop(dataframes: list[pl.DataFrame]) -> pl.DataFrame:
    """
    Combines a list of Polars DataFrames into a single DataFrame using a for loop.

    Args:
        dataframes (list[pl.DataFrame]): A list of Polars DataFrames to combine.

    Returns:
        pl.DataFrame: A single Polars DataFrame containing all rows from the input DataFrames.
    """
    if not dataframes:
        return pl.DataFrame()

    combined_df = pl.DataFrame()  # Start with an empty DataFrame

    for df in dataframes:
        if not combined_df.is_empty():
            combined_df = pl.concat([combined_df, df], how="vertical")
        else:
            combined_df = df.clone()  # Avoid modifying the original df

    return combined_df

def process_dataframe_chunks(df: pl.DataFrame, chunk_size: int = 100, process_function=None):
    """
    Utility function to split a DataFrame into chunks and optionally process each chunk.
    
    Args:
        df (pl.DataFrame): The DataFrame to process
        chunk_size (int): Number of rows per chunk (default: 100)
        process_function (callable, optional): Function to apply to each chunk
    
    Returns:
        list[pl.DataFrame]: List of processed DataFrame chunks
    """
    chunks = chunk_polars_dataframe(df, chunk_size)
    
    if process_function is None:
        return chunks
    
    processed_chunks = []
    for i, chunk in tqdm(enumerate(chunks), total=len(chunks), desc="Processing Chunks:"):
        try:
            processed_chunk = process_function(chunk, i)
            if processed_chunk is not None:
                processed_chunks.append(processed_chunk)
        except Exception as e:
            print(f"Error processing chunk {i}: {e}")
    
    return processed_chunks

