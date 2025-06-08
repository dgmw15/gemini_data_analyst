import unittest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import polars as pl
import pandas as pd

# Import the modules to test
from ai import data_processing_pipeline, format_elapsed_time, set_vertex_ai_mode, get_active_client
from text_splitter import chunk_polars_dataframe


class TestDataProcessingPipeline(unittest.TestCase):
    """Test suite for the data_processing_pipeline class"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary Excel file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_excel_path = os.path.join(self.temp_dir, "test_data.xlsx")
        
        # Create sample test data
        self.sample_data = {
            'ID': [1, 2, 3, 4, 5],
            'Name': ['Item A', 'Item B', 'Item C', 'Item D', 'Item E'],
            'Description': ['Desc A', 'Desc B', 'Desc C', 'Desc D', 'Desc E'],
            'Category': ['Cat1', 'Cat2', 'Cat1', 'Cat3', 'Cat2']
        }
        
        # Create test Excel file
        df_pandas = pd.DataFrame(self.sample_data)
        df_pandas.to_excel(self.test_excel_path, index=False)
        
        # Initialize test parameters
        self.system_instructions = "Test system instructions"
        self.output_path = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_path, exist_ok=True)
        
        # Create processor instance
        self.processor = data_processing_pipeline(
            df_material_file=self.test_excel_path,
            system_instructions=self.system_instructions,
            path_for_excel=self.output_path,
            use_vertex_ai=False,
            model_name="gemini-2.0-flash-001"
        )
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test that the data_processing_pipeline initializes correctly."""
        self.assertEqual(self.processor.df_material_file, self.test_excel_path)
        self.assertEqual(self.processor.system_instructions, self.system_instructions)
        self.assertEqual(self.processor.path_for_excel, self.output_path)
        self.assertFalse(self.processor.use_vertex_ai)
        self.assertEqual(self.processor.model_name, "gemini-2.0-flash-001")
    
    def test_convert_to_dataframe(self):
        """Test Excel file to DataFrame conversion."""
        df = self.processor.convert_to_dataframe()
        
        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(df.shape, (5, 4))  # 5 rows, 4 columns
        self.assertEqual(list(df.columns), ['ID', 'Name', 'Description', 'Category'])
    
    def test_convert_to_json_string(self):
        """Test DataFrame to JSON string conversion."""
        df = self.processor.convert_to_dataframe()
        json_str = self.processor.convert_to_json_string(df)
        
        self.assertIsInstance(json_str, str)
        # Verify it's valid JSON
        parsed_json = json.loads(json_str)
        self.assertIsInstance(parsed_json, list)
        self.assertEqual(len(parsed_json), 5)  # 5 rows
    
    def test_get_model_token_limit(self):
        """Test token limit retrieval for different models."""
        # Test default model
        limit = self.processor.get_model_token_limit()
        self.assertEqual(limit, 8192)  # gemini-2.0-flash-001 limit
        
        # Test different model
        self.processor.model_name = "gemini-2.5-pro"
        limit = self.processor.get_model_token_limit()
        self.assertEqual(limit, 65536)  # gemini-2.5-pro limit
        
        # Test unknown model (should default to 8192)
        self.processor.model_name = "unknown-model"
        limit = self.processor.get_model_token_limit()
        self.assertEqual(limit, 8192)
    
    def test_calculate_safe_input_limit(self):
        """Test safe input limit calculation."""
        with patch('builtins.print'):  # Suppress print output
            safe_limit = self.processor.calculate_safe_input_limit()
        
        expected_limit = int(8192 * 0.5)  # 50% of 8192
        self.assertEqual(safe_limit, expected_limit)
    
    def test_calculate_optimal_chunk_size(self):
        """Test optimal chunk size calculation."""
        # Test case where token count exceeds safe limit
        optimal_size = self.processor.calculate_optimal_chunk_size(
            current_chunk_size=100,
            token_count=1000,
            safe_limit=500
        )
        
        # Should reduce chunk size (100 * 0.5 * 0.8 = 40)
        expected_size = max(1, int(100 * (500/1000) * 0.8))
        self.assertEqual(optimal_size, expected_size)
        
        # Test case where token count is within safe limit
        optimal_size = self.processor.calculate_optimal_chunk_size(
            current_chunk_size=50,
            token_count=300,
            safe_limit=500
        )
        
        self.assertEqual(optimal_size, 50)  # Should remain unchanged
    
    def test_split_chunk_intelligently(self):
        """Test intelligent chunk splitting."""
        df = self.processor.convert_to_dataframe()  # 5 rows
        
        # Test splitting into chunks of 2
        chunks = self.processor.split_chunk_intelligently(df, target_size=2)
        
        self.assertEqual(len(chunks), 3)  # Should create 3 chunks: [2, 2, 1]
        self.assertEqual(len(chunks[0]), 2)
        self.assertEqual(len(chunks[1]), 2)
        self.assertEqual(len(chunks[2]), 1)
        
        # Test case where target size is larger than chunk
        chunks = self.processor.split_chunk_intelligently(df, target_size=10)
        
        self.assertEqual(len(chunks), 1)  # Should return single chunk
        self.assertEqual(len(chunks[0]), 5)
    
    @patch('ai.data_processing_pipeline.count_tokens_with_gemini')
    def test_validate_content_tokens(self, mock_count_tokens):
        """Test content token validation."""
        # Mock token counting
        mock_count_tokens.return_value = 1000
        
        with patch('builtins.print'):  # Suppress print output
            # Test valid content (within limits)
            with patch.object(self.processor, 'calculate_safe_input_limit', return_value=2000):
                is_valid, token_count, safe_limit = self.processor.validate_content_tokens("test content", 10)
                
                self.assertTrue(is_valid)
                self.assertEqual(token_count, 1000)
                self.assertEqual(safe_limit, 2000)
            
            # Test invalid content (exceeds limits)
            with patch.object(self.processor, 'calculate_safe_input_limit', return_value=500):
                is_valid, token_count, safe_limit = self.processor.validate_content_tokens("test content", 10)
                
                self.assertFalse(is_valid)
                self.assertEqual(token_count, 1000)
                self.assertEqual(safe_limit, 500)
    
    def test_response_data_cleansed(self):
        """Test AI response data cleansing."""
        # Test valid JSON response
        test_response = 'Some text before [{"key": "value"}, {"key2": "value2"}] some text after'
        cleaned = self.processor.response_data_cleansed(test_response)
        
        expected = '[{"key": "value"}, {"key2": "value2"}]'
        self.assertEqual(cleaned, expected)
        
        # Test response with no brackets
        test_response = 'No JSON here'
        cleaned = self.processor.response_data_cleansed(test_response)
        
        self.assertIsNone(cleaned)
    
    def test_response_to_dataframe(self):
        """Test JSON string to DataFrame conversion."""
        json_str = '[{"ID": 1, "Name": "Test"}, {"ID": 2, "Name": "Test2"}]'
        df = self.processor.response_to_dataframe(json_str)
        
        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(df.shape, (2, 2))
        self.assertEqual(list(df.columns), ['ID', 'Name'])
    
    def test_imposed_string_format(self):
        """Test DataFrame string formatting."""
        df = self.processor.convert_to_dataframe()
        formatted_df = self.processor.imposed_string_format(df)
        
        # Check that all columns are string type
        for dtype in formatted_df.dtypes:
            self.assertEqual(dtype, pl.String)
    
    def test_get_versioned_output_path(self):
        """Test versioned output path generation."""
        # Test basic path generation
        path1 = self.processor.get_versioned_output_path(self.output_path, "Test")
        self.assertTrue(path1.endswith('.xlsx'))
        self.assertIn('Test_', path1)
        
        # Create the file to test versioning
        with open(path1, 'w') as f:
            f.write('test')
        
        # Test versioned path generation
        path2 = self.processor.get_versioned_output_path(self.output_path, "Test")
        self.assertNotEqual(path1, path2)
        self.assertIn('_v1.xlsx', path2)
    
    def test_model_name_methods(self):
        """Test model name getter and setter methods."""
        # Test default model name
        model_name = self.processor.get_model_name()
        self.assertEqual(model_name, "gemini-2.0-flash-001")
        
        # Test custom model name
        self.processor.set_model_name("gemini-1.5-pro")
        model_name = self.processor.get_model_name()
        self.assertEqual(model_name, "gemini-1.5-pro")
    
    def test_vertex_ai_mode_methods(self):
        """Test Vertex AI mode setter."""
        # Initially should be False
        self.assertFalse(self.processor.use_vertex_ai)
        
        # Test setting to True
        with patch('builtins.print'):  # Suppress print output
            self.processor.set_vertex_ai_mode(True)
        
        self.assertTrue(self.processor.use_vertex_ai)
    
    @patch('ai.data_processing_pipeline.get_client')
    def test_ai_api_response_sync(self, mock_get_client):
        """Test synchronous AI API response (mocked)."""
        # Mock the client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"result": "success"}'
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # Test the method
        response = self.processor.ai_api_response("test content", "system instructions")
        
        self.assertEqual(response, '{"result": "success"}')
        mock_client.models.generate_content.assert_called_once()
    
    @patch('ai.data_processing_pipeline.get_client')
    async def test_ai_api_response_async(self, mock_get_client):
        """Test asynchronous AI API response (mocked)."""
        # Mock the client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"result": "success"}'
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        # Test the method
        response = await self.processor.ai_api_response_async("test content", "system instructions")
        
        self.assertEqual(response, '{"result": "success"}')
        mock_client.aio.models.generate_content.assert_called_once()


class TestUtilityFunctions(unittest.TestCase):
    """Test suite for utility functions"""
    
    def test_format_elapsed_time(self):
        """Test elapsed time formatting."""
        # Test less than a minute
        result = format_elapsed_time(45.7)
        self.assertEqual(result, "Process Time Taken: 0 mins 45 s")
        
        # Test more than a minute
        result = format_elapsed_time(125.3)
        self.assertEqual(result, "Process Time Taken: 2 mins 5 s")
        
        # Test exactly one minute
        result = format_elapsed_time(60.0)
        self.assertEqual(result, "Process Time Taken: 1 mins 0 s")
    
    @patch('builtins.print')
    def test_set_vertex_ai_mode(self, mock_print):
        """Test global Vertex AI mode setting."""
        set_vertex_ai_mode(True)
        mock_print.assert_called_with("🔄 Global API mode set to: Vertex AI")
        
        set_vertex_ai_mode(False)
        mock_print.assert_called_with("🔄 Global API mode set to: Standard Gemini (default)")


class TestTextSplitter(unittest.TestCase):
    """Test suite for text splitter functionality"""
    
    def test_chunk_polars_dataframe(self):
        """Test DataFrame chunking functionality."""
        # Create test DataFrame
        data = {
            'col1': list(range(10)),
            'col2': [f'value_{i}' for i in range(10)]
        }
        df = pl.DataFrame(data)
        
        # Test chunking
        chunks = chunk_polars_dataframe(df, chunk_size=3)
        
        self.assertEqual(len(chunks), 4)  # Should create 4 chunks: [3, 3, 3, 1]
        self.assertEqual(len(chunks[0]), 3)
        self.assertEqual(len(chunks[1]), 3)
        self.assertEqual(len(chunks[2]), 3)
        self.assertEqual(len(chunks[3]), 1)
        
        # Test with chunk size larger than DataFrame
        chunks = chunk_polars_dataframe(df, chunk_size=20)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(chunks[0]), 10)


class TestAsyncProcessing(unittest.TestCase):
    """Test suite for async processing functionality"""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_excel_path = os.path.join(self.temp_dir, "test_data.xlsx")
        
        # Create sample test data
        sample_data = {
            'ID': [1, 2, 3],
            'Name': ['Item A', 'Item B', 'Item C'],
            'Description': ['Desc A', 'Desc B', 'Desc C']
        }
        
        df_pandas = pd.DataFrame(sample_data)
        df_pandas.to_excel(self.test_excel_path, index=False)
        
        self.processor = data_processing_pipeline(
            df_material_file=self.test_excel_path,
            system_instructions="Test instructions",
            path_for_excel=self.temp_dir,
            use_vertex_ai=False
        )
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('ai.data_processing_pipeline.ai_api_response_async')
    async def test_process_chunk_mock(self, mock_api_response):
        """Test chunk processing with mocked API response."""
        # Mock API response
        mock_api_response.return_value = '[{"ID": 1, "Name": "Test", "Result": "Valid"}]'
        
        # Create test chunk
        df = self.processor.convert_to_dataframe()
        chunk = df.head(1)  # Single row chunk
        
        # Import the process_chunk function from run_script
        from run_script import process_chunk
        
        # Test processing
        result = await process_chunk(chunk, self.processor, "test prompt", 0)
        
        self.assertIsInstance(result, pl.DataFrame)
        self.assertEqual(result.shape[0], 1)  # Should have 1 row
        mock_api_response.assert_called_once()


if __name__ == '__main__':
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataProcessingPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestTextSplitter))
    suite.addTests(loader.loadTestsFromTestCase(TestAsyncProcessing))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}") 