import polars as pl 
import json
import os
from google import genai
from google.genai import types
import re
import datetime
from dotenv import load_dotenv
import asyncio

# This file contains all the functions used across the project for AI processing

# Load environment variables and setup API clients
load_dotenv()

# 🔑 API KEYS:
# Get API keys from environment variables (set in .env file)
api_key = os.getenv('GEMINI_API_KEY')  # Required: Standard Gemini API key
vertex_api_key = os.getenv('VERTEX_API_KEY')  # Optional: Vertex AI API key (only needed if using Vertex AI)

# 🤖 DEFAULT API CONFIGURATION:
# The system defaults to Standard Gemini API for easier setup and development
# Change USE_VERTEX_AI in your .env file or run_script.py to switch to Vertex AI
USE_VERTEX_AI = os.getenv('USE_VERTEX_AI', 'false').lower() == 'true'  # Default: False (uses Gemini)

# 🔌 CLIENT INITIALIZATION:
# Initialize both clients, but only Vertex AI client if API key is provided
client = genai.Client(api_key=api_key)  # Standard Gemini client (always available)
vertex_client = genai.Client(vertexai=True, api_key=vertex_api_key) if vertex_api_key else None  # Vertex AI client (optional)

# Token counting functionality is now integrated into the material_checker class methods

def get_active_client():
    """
    🔄 Returns the active client based on current configuration.
    
    DEFAULT BEHAVIOR: Returns Standard Gemini client (easier setup)
    
    Output:
        genai.Client: Either the standard Gemini client or Vertex AI client
    """
    if USE_VERTEX_AI and vertex_client:
        print("✅ Using Vertex AI client")
        return vertex_client
    else:
        print("✅ Using Standard Gemini client (default)")
        return client

def set_vertex_ai_mode(use_vertex: bool):
    """
    🔀 Toggle between Vertex AI and standard Gemini API globally.
    
    DEFAULT: Standard Gemini API (use_vertex=False)
    
    Input:
        use_vertex (bool): 
            - False = Use Standard Gemini API (DEFAULT, easier setup)
            - True  = Use Vertex AI (requires Vertex AI API key)
    """
    global USE_VERTEX_AI
    USE_VERTEX_AI = use_vertex
    api_name = "Vertex AI" if USE_VERTEX_AI else "Standard Gemini (default)"
    print(f"🔄 Global API mode set to: {api_name}")

def get_model_name():
    """
    🎯 Returns the appropriate default model name based on the active client.
    
    DEFAULT: gemini-2.0-flash-001 for both APIs
    
    Output:
        str: Model name for the active API
    """
    if USE_VERTEX_AI:
        return 'gemini-2.0-flash-001'  # Vertex AI default model
    else:
        return 'gemini-2.0-flash-001'  # Standard Gemini default model (DEFAULT)

def format_elapsed_time(seconds):
    """
    Format elapsed time in seconds to a readable format showing minutes and seconds.
    
    Input:
        seconds (float): Total elapsed time in seconds
    Output:
        str: Formatted string "Process Time Taken: x mins y s"
    Process:
        Converts total seconds to minutes and remaining seconds,
        then formats as a user-friendly string
    """
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"Process Time Taken: {minutes} mins {remaining_seconds} s"

class data_processing_pipeline:
    # 🎯 MODEL TOKEN LIMITS - Class-level constants
    MODEL_TOKEN_LIMITS = {
        'gemini-2.0-flash-001': 8192,          # Gemini 2.0 Flash
        'gemini-2.0-flash': 8192,              # Gemini 2.0 Flash (alias)
        'gemini-2.0-flash-exp': 8192,          # Gemini 2.0 Flash Experimental  
        'gemini-2.5-pro': 65536,               # Gemini 2.5 Pro (64K tokens)
        'gemini-2.5-pro-preview-06-05': 65536, # Gemini 2.5 Pro Preview
        'gemini-2.5-flash': 65536,             # Gemini 2.5 Flash (64K tokens)
        'gemini-2.5-flash-preview-05-20': 65536, # Gemini 2.5 Flash Preview
        'gemini-1.5-pro': 8192,                # Gemini 1.5 Pro
        'gemini-1.5-pro-001': 8192,            # Gemini 1.5 Pro specific version
        'gemini-1.5-pro-002': 8192,            # Gemini 1.5 Pro specific version
        'gemini-1.5-flash': 8192,              # Gemini 1.5 Flash
        'gemini-1.5-flash-001': 8192,          # Gemini 1.5 Flash specific version
        'gemini-1.5-flash-002': 8192,          # Gemini 1.5 Flash specific version
        'gemini-1.5-flash-8b': 8192,           # Gemini 1.5 Flash 8B
    }
    
    def __init__(self, df_material_file, system_instructions, path_for_excel, use_vertex_ai=None, model_name=None):
        """
        🏗️ Initializes the data_processing_pipeline class.

        A comprehensive data processing pipeline with AI integration, token validation, 
        and automatic rate limiting for scalable data analysis workflows.

        DEFAULT BEHAVIOR: Uses Standard Gemini API with gemini-2.0-flash-001 model

        Input:
            df_material_file (str): Path to the input data file (Excel).
            system_instructions (str): System instructions for the AI model.
            path_for_excel (str): Path to save the output Excel file.
            use_vertex_ai (bool, optional): 
                - None = Use global setting (DEFAULT)
                - False = Force Standard Gemini API (easier setup)
                - True = Force Vertex AI (requires Vertex AI API key)
            model_name (str, optional): 
                - None = Use default model (gemini-2.0-flash-001)
                - Specify custom model (e.g., 'gemini-1.5-pro')
        """
        self.system_instructions = system_instructions
        self.path_for_excel = path_for_excel
        self.df_material_file = df_material_file
        # Default to global setting (which defaults to Standard Gemini)
        self.use_vertex_ai = use_vertex_ai if use_vertex_ai is not None else USE_VERTEX_AI
        self.model_name = model_name  # Store custom model name (None = use default)
        pass

    def get_model_token_limit(self) -> int:
        """
        🎯 Get the output token limit for the current model.
        
        Output:
            int: Maximum output tokens for the model (defaults to 8192 if unknown)
        """
        model_name = self.get_model_name()
        return self.MODEL_TOKEN_LIMITS.get(model_name, 8192)

    def calculate_safe_input_limit(self) -> int:
        """
        🛡️ Calculate the safe input token limit (50% of model's output limit).
        
        Output:
            int: Safe input token limit (50% of output tokens)
        """
        output_limit = self.get_model_token_limit()
        safe_limit = int(output_limit * 0.5)
        model_name = self.get_model_name()
        print(f"🎯 Model: {model_name}")
        print(f"📊 Output token limit: {output_limit:,}")
        print(f"🛡️ Safe input limit (50%): {safe_limit:,}")
        return safe_limit

    def count_tokens_with_gemini(self, content: str) -> int:
        """
        🔢 Count tokens in content using Gemini's SDK.
        
        Input:
            content (str): Text content to count tokens for
        Output:
            int: Number of tokens in the content
            Returns 0 if an error occurs
        """
        try:
            active_client = self.get_client()
            model_name = self.get_model_name()
            
            response = active_client.models.count_tokens(
                model=model_name,
                contents=[{
                    "role": "user",
                    "parts": [{"text": content}]
                }]
            )
            token_count = response.total_tokens
            print(f"🔢 Token count: {token_count:,}")
            return token_count
        except Exception as e:
            print(f"❌ Error counting tokens: {e}")
            return 0

    def validate_token_limit(self, content: str) -> tuple[bool, int, int]:
        """
        ✅ Validate that content doesn't exceed safe token limits.
        
        Input:
            content (str): Text content to validate
        Output:
            tuple[bool, int, int]: (is_valid, token_count, safe_limit)
                - is_valid: True if content is within safe limits
                - token_count: Actual token count of content
                - safe_limit: Maximum safe token limit
        """
        token_count = self.count_tokens_with_gemini(content)
        safe_limit = self.calculate_safe_input_limit()
        
        is_valid = token_count <= safe_limit
        
        if is_valid:
            print(f"✅ Content is within safe limits ({token_count:,}/{safe_limit:,} tokens)")
        else:
            print(f"❌ Content exceeds safe limits ({token_count:,}/{safe_limit:,} tokens)")
            print(f"🚨 Exceeded by: {token_count - safe_limit:,} tokens")
        
        return is_valid, token_count, safe_limit

    def validate_content_tokens(self, content: str, current_chunk_size: int) -> tuple[bool, int, int]:
        """
        🔍 Validate that content doesn't exceed safe token limits before API call.
        
        Input:
            content (str): The content to validate
            current_chunk_size (int): Current chunk size for error reporting
        Output:
            tuple[bool, int, int]: (is_valid, token_count, safe_limit)
                - is_valid: True if content is safe to send
                - token_count: Actual token count of content
                - safe_limit: Maximum safe token limit
        Process:
            - Counts tokens using Gemini's SDK
            - Validates against 50% of model's output token limit
            - Returns validation result instead of stopping
        """
        try:
            print(f"🔍 Validating token count for content...")
            is_valid, token_count, safe_limit = self.validate_token_limit(content)
            
            if not is_valid:
                print(f"⚠️ Content exceeds token limit, will attempt automatic reduction")
                return False, token_count, safe_limit
            
            return True, token_count, safe_limit
        except Exception as e:
            print(f"⚠️ Warning: Could not validate token count: {e}")
            print("🔄 Proceeding with API call (token validation failed)")
            return True, 0, 0

    def calculate_optimal_chunk_size(self, current_chunk_size: int, token_count: int, safe_limit: int) -> int:
        """
        🧮 Calculate optimal chunk size based on token count exceeded.
        
        Input:
            current_chunk_size (int): Current chunk size that exceeded limits
            token_count (int): Current token count
            safe_limit (int): Maximum safe token limit
        Output:
            int: Suggested new chunk size (minimum 1)
        """
        if token_count <= safe_limit:
            return current_chunk_size
        
        # Calculate reduction factor with safety margin
        reduction_factor = safe_limit / token_count
        suggested_size = max(1, int(current_chunk_size * reduction_factor * 0.8))  # 80% for safety
        
        print(f"📊 Token reduction calculation:")
        print(f"   Current chunk size: {current_chunk_size}")
        print(f"   Token count: {token_count:,}")
        print(f"   Safe limit: {safe_limit:,}")
        print(f"   Reduction factor: {reduction_factor:.2f}")
        print(f"   Suggested chunk size: {suggested_size}")
        
        return suggested_size

    def split_chunk_intelligently(self, chunk_df, target_size: int):
        """
        🔪 Split a DataFrame chunk into smaller chunks of target size.
        
        Input:
            chunk_df (polars.DataFrame): The chunk to split
            target_size (int): Target number of rows per sub-chunk
        Output:
            list[polars.DataFrame]: List of smaller chunks
        """
        if len(chunk_df) <= target_size:
            return [chunk_df]
        
        chunks = []
        for i in range(0, len(chunk_df), target_size):
            sub_chunk = chunk_df[i:i + target_size]
            chunks.append(sub_chunk)
        
        print(f"🔪 Split chunk of {len(chunk_df)} rows into {len(chunks)} sub-chunks of ~{target_size} rows each")
        return chunks

    def ai_api_response(self, contents, system_instructions, current_chunk_size=None):
        """
        Sends content to the AI model and retrieves the response.

        Input:
            contents (str): The input text/data to send to the AI model.
            system_instructions (str): System instructions for the AI model.
            current_chunk_size (int, optional): Current chunk size for token validation (deprecated - handled externally)
        Output:
            str: The text response from the AI model.
                 Returns None if an error occurs.
        Process:
            Uses the active client (Gemini or Vertex AI) to generate content based on the provided
            contents and system instructions.
        """
        try:
            active_client = self.get_client()
            model_name = self.get_model_name()
            
            response = active_client.models.generate_content(
                model=model_name,
                contents=[
                types.Content(
                    role='user',
                    parts=[{ "text": contents }]  #need to indicate that this is a text for the part. 
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=[{ "text": system_instructions }],  # Note: changed from list to string
                max_output_tokens=100000,
                temperature=1,
                response_mime_type="application/json",  # Force JSON output format
            ),
            )
            ai_response = response.text
            return ai_response
        except Exception as e:
            print(f"Error: {e}")
            return None

    async def ai_api_response_async(self, contents, system_instructions, current_chunk_size=None):
        """
        Sends content to the AI model and retrieves the response asynchronously.

        Input:
            contents (str): The input text/data to send to the AI model.
            system_instructions (str): System instructions for the AI model.
            current_chunk_size (int, optional): Current chunk size for token validation (deprecated - handled externally)
        Output:
            str: The text response from the AI model.
                 Returns None if an error occurs.
        Process:
            Uses the active client's (Gemini or Vertex AI) async interface to generate content based on the provided
            contents and system instructions.
        """
        try:
            active_client = self.get_client()
            model_name = self.get_model_name()
            
            response = await active_client.aio.models.generate_content(
                model=model_name,
                contents=[
                types.Content(
                    role='user',
                    parts=[{ "text": contents }]  #need to indicate that this is a text for the part. 
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=[{ "text": system_instructions }],  # Note: changed from list to string
                max_output_tokens=100000,
                temperature=1,
                response_mime_type="application/json",  # Force JSON output format
            ),
            )
            ai_response = response.text
            return ai_response
        except Exception as e:
            print(f"Error: {e}")
            return None
            
    def remove_brackets(self, data_df, Column):
        """
        Removes specific bracket patterns from a specified column in a DataFrame.

        Input:
            data_df (polars.DataFrame): The DataFrame to process.
            Column (str): The name of the column to clean.
        Output:
            polars.DataFrame: DataFrame with the specified column cleaned.
                              Returns None if an error occurs.
        Process:
            Replaces "[]" with None.
            Removes "['" from the start and "']" from the end of strings in the specified column.
        """
        try:
            data_df = data_df.with_columns(
                pl.when(pl.col(Column).str.strip() == "[]")
                .then(pl.lit(None))
                .when(
                    (pl.col(Column).str.starts_with("['")) & (pl.col(Column).str.ends_with("']"))
                )
                .then(
                    pl.col(Column).str.slice(2, pl.col(Column).str.len() - 3)  # Extract content
                )
                .otherwise(pl.col(Column))
                .alias(Column)
            )
            return data_df
        except Exception as e:
            print(f"Error: {e}")
            return None

    def response_data_cleansed(self, ai_response):
        """
        Cleans the AI model's response string to extract a valid JSON array.

        Input:
            ai_response (str): The raw string response from the AI model.
        Output:
            str: A string representing a JSON array, extracted from the input.
                 Returns None if no match is found or an error occurs.
        Process:
            Uses regular expressions to find the first '[' and the last ']'
            to extract the JSON array portion of the string.
        """
        try:
            match_start = re.search(r'\[', ai_response)
            match_end = re.search(r'\]', ai_response[::-1])

            if match_start and match_end:
                json_start = match_start.start()
                json_end = len(ai_response) - match_end.start()
                ai_response = ai_response[json_start:json_end]
                ai_response_str = str(ai_response)
                return ai_response_str
            else:
                print("No match found")
        except Exception as e:
            print(f"Error: {e}")
            return None
        
    def response_to_dataframe(self, ai_response_str):
        """
        Converts a JSON string (presumably a list of objects) to a Polars DataFrame.

        Input:
            ai_response_str (str): The JSON string to convert.
        Output:
            polars.DataFrame: DataFrame created from the JSON string.
                              Returns None if an error occurs.
        Process:
            Loads the JSON string into a Python list of dictionaries,
            then creates a Polars DataFrame from it.
        """
        try:
            ai_response_formatted_for_dataframe = json.loads(ai_response_str)
            df_output = pl.DataFrame(ai_response_formatted_for_dataframe)
            return df_output
        except Exception as e:
            print(f"Error: {e}")
            return None

    def response_to_excel(self, df_output_with_processed_data, path_for_excel):
        """
        Writes a Polars DataFrame to an Excel file.

        Input:
            df_output_with_processed_data (polars.DataFrame): The DataFrame to write.
            path_for_excel (str): The file path to save the Excel file.
        Output:
            None
        Process:
            Writes the given DataFrame to an Excel file at the specified path.
        """
        try:
            df_output_with_processed_data.write_excel(path_for_excel)
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_versioned_output_path(self, base_dir: str, prefix: str = "Data_Response") -> str:
        """
        Generates a versioned file path for output, creating date-based subfolders.

        Input:
            base_dir (str): The base directory where the output will be stored.
            prefix (str, optional): Prefix for the output file name.
                                    Defaults to "Data_Response".
        Output:
            str: A unique, versioned file path (e.g., "base_dir/Results_YYYYMMDD/Prefix_YYYYMMDD_HHMM_vN.xlsx").
        Process:
            1. Creates a subfolder named "Results_YYYYMMDD" inside `base_dir` if it doesn't exist.
            2. Constructs an initial file name using the prefix and current timestamp (YYYYMMDD_HHMM).
            3. If the file already exists, appends a version number (e.g., "_v1", "_v2")
               until a unique file name is found.
        """
        # Create a subfolder with current date
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        
        # Create subfolder
        subfolder = os.path.join(base_dir, f"Results_{current_date}")
        os.makedirs(subfolder, exist_ok=True)
        
        # Create initial base path
        base_path = os.path.join(subfolder, f"{prefix}_{current_time}.xlsx")
        
        # If base path doesn't exist, return it
        if not os.path.exists(base_path):
            return base_path
        
        # If base path exists, create versioned name
        version = 1
        versioned_path = os.path.join(subfolder, f"{prefix}_{current_time}_v{version}.xlsx")
        
        while os.path.exists(versioned_path):
            version += 1
            versioned_path = os.path.join(subfolder, f"{prefix}_{current_time}_v{version}.xlsx")
        
        return versioned_path
    
    def imposed_string_format(self, df_output):
        """
        Casts all columns in a Polars DataFrame to string type.

        Input:
            df_output (polars.DataFrame): The DataFrame to process.
        Output:
            polars.DataFrame: DataFrame with all columns cast to string type.
                              Returns None if an error occurs.
        Process:
            Uses Polars' `with_columns` and `cast(pl.String)` to convert
            every column in the DataFrame to the string data type.
        """
        try:
            df_output = df_output.with_columns(pl.all().cast(pl.String))
            return df_output
        except Exception as e:
            print(f"Error: {e}")
            return None

    def convert_to_dataframe(self):
        """
        Converts the input Excel file to a Polars DataFrame.

        Input:
            None (uses self.df_material_file initialized in __init__)
        Output:
            polars.DataFrame: DataFrame representation of the input file.
                              Returns None if an error occurs.
        Process:
            Reads the Excel file specified by self.df_material_file into a Polars DataFrame.
        """
        try:
            data_df = pl.read_excel(self.df_material_file)
            return data_df
        except Exception as e:
            print(f"Error: {e}")
            return None

    def convert_to_json_string(self, data_df):
        """
        Converts a Polars DataFrame to a JSON string.

        Input:
            data_df (polars.DataFrame): The DataFrame to convert.
        Output:
            str: JSON string representation of the DataFrame.
                 Returns None if an error occurs.
        Process:
            Writes the DataFrame to a JSON string, then loads and dumps it
            to ensure correct formatting. Stores the result in self.data_content.
        """
        try:
            data_df_json = data_df.write_json()
            data_content = json.loads(data_df_json)
            data_content = json.dumps(data_content)
            self.data_content = data_content
            return self.data_content
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_client(self):
        """
        🔌 Returns the appropriate client for this instance.
        
        DEFAULT: Returns Standard Gemini client (easier setup)
        
        Output:
            genai.Client: Either the standard Gemini client or Vertex AI client
        """
        if self.use_vertex_ai and vertex_client:
            return vertex_client  # Use Vertex AI if configured and available
        else:
            return client  # Use Standard Gemini client (DEFAULT)

    def get_model_name(self):
        """
        🎯 Returns the appropriate model name for this instance.
        
        DEFAULT: gemini-2.0-flash-001 (recommended for best performance)
        
        Output:
            str: Model name for the active API
        """
        # If a custom model name is set, use it
        if self.model_name:
            return self.model_name
        
        # Otherwise use default based on API type (both use same default)
        if self.use_vertex_ai:
            return 'gemini-2.0-flash-001'  # Vertex AI default model
        else:
            return 'gemini-2.0-flash-001'  # Standard Gemini default model (DEFAULT)

    def set_vertex_ai_mode(self, use_vertex: bool):
        """
        🔀 Toggle between Vertex AI and standard Gemini API for this instance.
        
        DEFAULT: Standard Gemini API (easier setup)
        
        Input:
            use_vertex (bool): 
                - False = Use Standard Gemini API (DEFAULT, easier setup)
                - True = Use Vertex AI (requires Vertex AI API key)
        """
        self.use_vertex_ai = use_vertex
        api_name = "Vertex AI" if self.use_vertex_ai else "Standard Gemini (default)"
        print(f"🔄 Instance API mode set to: {api_name}")

    def set_model_name(self, model_name: str):
        """
        🎯 Set a custom model name for this instance.
        
        Available models:
        - 'gemini-2.0-flash-001' (DEFAULT, recommended)
        - 'gemini-1.5-pro' (stable)
        - 'gemini-1.5-flash' (faster)
        
        Input:
            model_name (str): The model name to use
        """
        self.model_name = model_name
        print(f"🎯 Model set to: {model_name}")







