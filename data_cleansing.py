import re
import polars as pl
import os
from datetime import datetime
from ai import material_checker

class DataCleanser:
    def __init__(self, input_file, output_folder, delimiters_to_split, columns_to_clean=None, column_headers=None):
        """
        Initialize the data cleansing tool.
        
        Args:
            input_file (str): Path to the input Excel file
            output_folder (str): Path to the output folder
            delimiters_to_split (list): List of characters or strings to use as delimiters
            columns_to_clean (list): List of column names or indices to clean
            column_headers (list, optional): Column headers to use for the data
        """
        self.input_file = input_file
        self.output_folder = output_folder
        self.delimiters_to_split = delimiters_to_split
        self.columns_to_clean = columns_to_clean
        self.column_headers = column_headers
        self.material_processor = material_checker(input_file, "", output_folder)
        
    def load_data(self):
        """Load data from Excel file into a DataFrame"""
        try:
            # Using the existing function to load Excel
            df = self.material_processor.convert_to_dataframe()
            
            # Convert all columns to string type first
            if df is not None:
                # Replace None/null values with empty strings before converting to string
                for col in df.columns:
                    df = df.with_columns(
                        pl.col(col).fill_null("").alias(col)
                    )
                
                # Convert all columns to string type
                df = df.with_columns(pl.all().cast(pl.String))
            
            # Check if we need to add column headers
            if self.column_headers:
                # Get the first row values to use as column headers if none are provided
                if df is not None:
                    # Create a new DataFrame with proper headers (skip first row)
                    header_row = df.row(0)
                    data_rows = df.slice(1)
                    
                    # If custom headers are provided, use them
                    if self.column_headers:
                        # Make sure we have enough headers
                        if len(self.column_headers) < len(df.columns):
                            # Extend with generic column names
                            self.column_headers.extend([f"Column_{i+1}" for i in range(len(self.column_headers), len(df.columns))])
                        elif len(self.column_headers) > len(df.columns):
                            # Truncate to match dataframe columns
                            self.column_headers = self.column_headers[:len(df.columns)]
                        
                        df = data_rows.rename(dict(zip(data_rows.columns, self.column_headers)))
                    else:
                        # Use first row as headers
                        df = data_rows.rename(dict(zip(data_rows.columns, header_row)))
            
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def remove_leading_spaces(self, df, columns_to_process=None):
        """
        Remove leading spaces from specified columns.
        
        Args:
            df (pl.DataFrame): Input DataFrame
            columns_to_process (list, optional): List of columns to process. 
                                               If None, use self.columns_to_clean
            
        Returns:
            pl.DataFrame: DataFrame with leading spaces removed
        """
        if df is None:
            return None
            
        try:
            # Use columns_to_clean if columns_to_process not provided
            if columns_to_process is None:
                columns_to_process = []
                
                if self.columns_to_clean:
                    # Handle both column names and column indices
                    for col in self.columns_to_clean:
                        if isinstance(col, int) and 0 <= col < len(df.columns):
                            # Handle column by index
                            columns_to_process.append(df.columns[col])
                        elif col in df.columns:
                            # Handle column by name
                            columns_to_process.append(col)
                else:
                    # If no columns specified, process all columns
                    columns_to_process = df.columns
            
            # Apply trim to remove leading spaces in specified columns
            for col in columns_to_process:
                df = df.with_columns(
                    pl.col(col).str.strip_prefix(" ").alias(col)
                )
            
            return df
        except Exception as e:
            print(f"Error removing leading spaces: {e}")
            return None
    
    def split_by_delimiters(self, text, delimiters):
        """
        Split text by multiple delimiters.
        
        Args:
            text (str): Text to split
            delimiters (list): List of delimiter strings
            
        Returns:
            list: List of split strings
        """
        # Handle None or empty values
        if text is None:
            return []
        
        if not isinstance(text, str):
            text = str(text)
            
        if not text.strip():
            return []
            
        # Replace each delimiter with a special marker
        marker = "||SPLIT||"
        result = text
        for delimiter in delimiters:
            result = result.replace(delimiter, marker)
        
        # Split by the marker
        return [item.strip() for item in result.split(marker) if item.strip()]
        
    def clean_data(self, df):
        """
        Clean the data by splitting text by delimiters and recombining with spaces.
        
        Args:
            df (pl.DataFrame): Input DataFrame
            
        Returns:
            pl.DataFrame: Cleaned DataFrame
        """
        if df is None:
            return None
            
        try:
            # Get the columns to clean
            columns_to_process = []
            
            if self.columns_to_clean:
                # Handle both column names and column indices
                for col in self.columns_to_clean:
                    if isinstance(col, int) and 0 <= col < len(df.columns):
                        # Handle column by index
                        columns_to_process.append(df.columns[col])
                    elif col in df.columns:
                        # Handle column by name
                        columns_to_process.append(col)
            else:
                # If no columns specified, process all columns
                columns_to_process = df.columns
            
            # Special handling for space delimiters
            has_space = " " in self.delimiters_to_split
            non_space_delimiters = [d for d in self.delimiters_to_split if d != " "]
            
            # Process each column - using basic Python operations instead of Polars functions
            for col in columns_to_process:
                print(f"Processing column: {col}")
                
                # Convert to Python list to process without Polars functions
                column_values = df[col].to_list()
                cleaned_values = []
                
                for value in column_values:
                    # Handle None or empty values
                    if value is None or not str(value).strip():
                        cleaned_values.append("")
                        continue
                    
                    # First replace multiple spaces with a single space
                    value = re.sub(r'\s+', ' ', str(value))
                    
                    # Split by non-space delimiters
                    split_values = self.split_by_delimiters(value, non_space_delimiters)
                    
                    # Further split by spaces if needed
                    if has_space:
                        words = []
                        for item in split_values:
                            words.extend([word for word in item.split(" ") if word.strip()])
                        split_values = words
                    
                    # Join back with spaces
                    cleaned_value = " ".join(split_values)
                    cleaned_values.append(cleaned_value)
                
                # Replace the column in the DataFrame
                df = df.with_columns(
                    pl.Series(name=col, values=cleaned_values)
                )
            
            return df
        except Exception as e:
            print(f"Error cleaning data: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def save_data(self, df):
        """
        Save the cleaned data to Excel file.
        
        Args:
            df (pl.DataFrame): DataFrame to save
            
        Returns:
            str: Path to the saved file
        """
        if df is None:
            return None
            
        try:
            # Get versioned output path
            output_path = self.material_processor.get_versioned_output_path(
                self.output_folder, 
                prefix="Cleaned_Data"
            )
            
            # Save to Excel
            self.material_processor.material_response_to_excel(df, output_path)
            
            return output_path
        except Exception as e:
            print(f"Error saving data: {e}")
            return None
    
    def process(self):
        """
        Process the data: load, clean, and save.
        
        Returns:
            str: Path to the output file if successful, None otherwise
        """
        # Load data
        print("Loading data...")
        df = self.load_data()
        if df is None:
            print("Failed to load data")
            return None
        
        # Print column names and sample data for debugging
        print(f"Column names: {df.columns}")
        print(f"First row: {df.row(0)}")
        
        # Clean data
        print("Cleaning data...")
        cleaned_df = self.clean_data(df)
        if cleaned_df is None:
            print("Failed to clean data")
            return None
        
        # Save data
        print("Saving data...")
        output_path = self.save_data(cleaned_df)
        if output_path:
            print(f"Data successfully cleaned and saved to: {output_path}")
            return output_path
        else:
            print("Failed to save data")
            return None


# Example usage (these values should be modified as needed)
if __name__ == "__main__":
    # Configuration (these should be variables rather than user inputs)
    input_file = r"G:\Shared drives\SP3D shared drive (all employee)\R_Engineering\Daryl\ORYX\Oryx File (For Data Cleanse).xlsx"
    output_folder = r"C:\Users\pauld\Desktop\Output for Data Cleanse"
    delimiters_to_split = [";", ":", ",", " "]  # Including single space as delimiter
    column_headers = ["Short Desc", "Long Desc", "MM#", "Part Category"]  # Optional, set to None to use first row as headers
    columns_to_clean = ["Part Category"]  # Only clean these columns
    
    # Create and run the data cleanser
    cleanser = DataCleanser(
        input_file, 
        output_folder, 
        delimiters_to_split,
        columns_to_clean=columns_to_clean,
        column_headers=column_headers
    )
    output_file = cleanser.process()
