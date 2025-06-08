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
api_key = os.getenv('GEMINI_API_KEY')
vertex_api_key = os.getenv('VERTEX_API_KEY')  # Add Vertex AI API key

# Configuration for API selection
USE_VERTEX_AI = os.getenv('USE_VERTEX_AI', 'false').lower() == 'true'  # Default to false

# Initialize clients
client = genai.Client(api_key=api_key)
vertex_client = genai.Client(vertexai=True, api_key=vertex_api_key) if vertex_api_key else None

def get_active_client():
    """
    Returns the active client based on configuration.
    
    Output:
        genai.Client: Either the standard Gemini client or Vertex AI client
    """
    if USE_VERTEX_AI and vertex_client:
        print("Using Vertex AI client")
        return vertex_client
    else:
        print("Using standard Gemini client")
        return client

def set_vertex_ai_mode(use_vertex: bool):
    """
    Toggle between Vertex AI and standard Gemini API.
    
    Input:
        use_vertex (bool): True to use Vertex AI, False for standard Gemini
    """
    global USE_VERTEX_AI
    USE_VERTEX_AI = use_vertex
    print(f"API mode set to: {'Vertex AI' if USE_VERTEX_AI else 'Standard Gemini'}")

def get_model_name():
    """
    Returns the appropriate model name based on the active client.
    
    Output:
        str: Model name for the active API
    """
    if USE_VERTEX_AI:
        return 'gemini-2.0-flash-001'  # Vertex AI model
    else:
        return 'gemini-2.0-flash-001'  # Standard Gemini model

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

class material_checker:
    def __init__(self, df_material_file, system_instructions, path_for_excel, use_vertex_ai=None):
        """
        Initializes the material_checker class.

        Input:
            df_material_file (str): Path to the material file (Excel).
            system_instructions (str): System instructions for the AI model.
            path_for_excel (str): Path to save the output Excel file.
            use_vertex_ai (bool, optional): Override global setting for this instance.
        Output:
            None
        Process:
            Sets the initial attributes for the class instance.
        """
        self.system_instructions = system_instructions
        self.path_for_excel = path_for_excel
        self.df_material_file = df_material_file
        self.use_vertex_ai = use_vertex_ai if use_vertex_ai is not None else USE_VERTEX_AI
        pass

    def convert_to_dataframe(self):
        """
        Converts the material Excel file to a Polars DataFrame.

        Input:
            None (uses self.df_material_file initialized in __init__)
        Output:
            polars.DataFrame: DataFrame representation of the material file.
                              Returns None if an error occurs.
        Process:
            Reads the Excel file specified by self.df_material_file into a Polars DataFrame.
        """
        try:
            material_df = pl.read_excel(self.df_material_file)
            return material_df
        except Exception as e:
            print(f"Error: {e}")
            return None

    def convert_to_json_string(self, material_df):
        """
        Converts a Polars DataFrame to a JSON string.

        Input:
            material_df (polars.DataFrame): The DataFrame to convert.
        Output:
            str: JSON string representation of the DataFrame.
                 Returns None if an error occurs.
        Process:
            Writes the DataFrame to a JSON string, then loads and dumps it
            to ensure correct formatting. Stores the result in self.material_data.
        """
        try:
            material_df_json = material_df.write_json()
            material_data = json.loads(material_df_json)
            material_data = json.dumps(material_data)
            self.material_data = material_data
            return self.material_data
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_client(self):
        """
        Returns the appropriate client for this instance.
        
        Output:
            genai.Client: Either the standard Gemini client or Vertex AI client
        """
        if self.use_vertex_ai and vertex_client:
            return vertex_client
        else:
            return client

    def get_model_name(self):
        """
        Returns the appropriate model name for this instance.
        
        Output:
            str: Model name for the active API
        """
        if self.use_vertex_ai:
            return 'gemini-2.0-flash-001'  # Vertex AI model
        else:
            return 'gemini-2.0-flash-001'  # Standard Gemini model

    def set_vertex_ai_mode(self, use_vertex: bool):
        """
        Toggle between Vertex AI and standard Gemini API for this instance.
        
        Input:
            use_vertex (bool): True to use Vertex AI, False for standard Gemini
        """
        self.use_vertex_ai = use_vertex
        print(f"Instance API mode set to: {'Vertex AI' if self.use_vertex_ai else 'Standard Gemini'}")

    def ai_api_response(self, contents, system_instructions):
        """
        Sends content to the AI model and retrieves the response.

        Input:
            contents (str): The input text/data to send to the AI model.
            system_instructions (str): System instructions for the AI model.
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
            material_response = response.text
            return material_response
        except Exception as e:
            print(f"Error: {e}")
            return None

    async def ai_api_response_async(self, contents, system_instructions):
        """
        Sends content to the AI model and retrieves the response asynchronously.

        Input:
            contents (str): The input text/data to send to the AI model.
            system_instructions (str): System instructions for the AI model.
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
            material_response = response.text
            return material_response
        except Exception as e:
            print(f"Error: {e}")
            return None
            
    def material_remove_brackets(self, material_df, Column):
        """
        Removes specific bracket patterns from a specified column in a DataFrame.

        Input:
            material_df (polars.DataFrame): The DataFrame to process.
            Column (str): The name of the column to clean.
        Output:
            polars.DataFrame: DataFrame with the specified column cleaned.
                              Returns None if an error occurs.
        Process:
            Replaces "[]" with None.
            Removes "['" from the start and "']" from the end of strings in the specified column.
        """
        try:
            material_df = material_df.with_columns(
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
            return material_df
        except Exception as e:
            print(f"Error: {e}")
            return None

    def material_response_data_cleansed(self, material_response):
        """
        Cleans the AI model's response string to extract a valid JSON array.

        Input:
            material_response (str): The raw string response from the AI model.
        Output:
            str: A string representing a JSON array, extracted from the input.
                 Returns None if no match is found or an error occurs.
        Process:
            Uses regular expressions to find the first '[' and the last ']'
            to extract the JSON array portion of the string.
        """
        try:
            match_start = re.search(r'\[', material_response)
            match_end = re.search(r'\]', material_response[::-1])

            if match_start and match_end:
                json_start = match_start.start()
                json_end = len(material_response) - match_end.start()
                material_response = material_response[json_start:json_end]
                material_response_str = str(material_response)
                return material_response_str
            else:
                print("No match found")
        except Exception as e:
            print(f"Error: {e}")
            return None
        
    def material_response_to_dataframe(self, material_response_str):
        """
        Converts a JSON string (presumably a list of objects) to a Polars DataFrame.

        Input:
            material_response_str (str): The JSON string to convert.
        Output:
            polars.DataFrame: DataFrame created from the JSON string.
                              Returns None if an error occurs.
        Process:
            Loads the JSON string into a Python list of dictionaries,
            then creates a Polars DataFrame from it.
        """
        try:
            material_response_formatted_for_dataframe = json.loads(material_response_str)
            df_output = pl.DataFrame(material_response_formatted_for_dataframe)
            return df_output
        except Exception as e:
            print(f"Error: {e}")
            return None

    def material_response_to_excel(self, df_output_with_int_part_number, path_for_excel):
        """
        Writes a Polars DataFrame to an Excel file.

        Input:
            df_output_with_int_part_number (polars.DataFrame): The DataFrame to write.
            path_for_excel (str): The file path to save the Excel file.
        Output:
            None
        Process:
            Writes the given DataFrame to an Excel file at the specified path.
        """
        try:
            df_output_with_int_part_number.write_excel(path_for_excel)
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_versioned_output_path(self, base_dir: str, prefix: str = "Material_Response") -> str:
        """
        Generates a versioned file path for output, creating date-based subfolders.

        Input:
            base_dir (str): The base directory where the output will be stored.
            prefix (str, optional): Prefix for the output file name.
                                    Defaults to "Material_Response".
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







