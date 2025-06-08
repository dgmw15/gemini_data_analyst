# Gemini Data Analyst

All the basic coding projects I have done for SP3D with Gemini mainly

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

#### 1. Create a Virtual Environment

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv gemini_env

# Activate virtual environment
.\gemini_env\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
# Create virtual environment
python -m venv gemini_env

# Activate virtual environment
gemini_env\Scripts\activate.bat
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv gemini_env

# Activate virtual environment
source gemini_env/bin/activate
```

#### 2. Install Dependencies

Once the virtual environment is activated, install the required packages:

```bash
pip install -r requirements.txt
```

#### 3. Environment Variables

Create a `.env` file in the project root and add any necessary API keys or configuration variables:

```env
# Add your API keys here
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Vertex AI Configuration (optional)
VERTEX_API_KEY=your_vertex_ai_api_key_here
USE_VERTEX_AI=false  # Set to 'true' to use Vertex AI instead of standard Gemini API
```

**API Configuration Options:**
- **Standard Gemini API**: Uses the regular Gemini API (default)
- **Vertex AI**: Uses Google Cloud Vertex AI for enhanced features and enterprise-level capabilities

To use Vertex AI:
1. Set `USE_VERTEX_AI=true` in your `.env` file
2. Add your Vertex AI API key to `VERTEX_API_KEY`
3. You can also toggle this programmatically using the `set_vertex_ai_mode()` function

#### 4. Verify Installation

You can verify the installation by running:

```bash
pip list
```

### Usage

After completing the setup, you can run the various scripts in the project:

- `python ai.py` - Main AI processing script
- `python run_script.py` - General run script
- `python data_cleansing.py` - Data cleaning operations
- `python BOM_run.py` - BOM processing script

### Deactivating the Environment

When you're done working on the project, deactivate the virtual environment:

```bash
deactivate
```

## Project Structure

- `ai.py` - Main AI processing functionality
- `data_cleansing.py` - Data cleaning and preprocessing
- `run_script.py` - Main execution script
- `prompt.py` - Prompt management and templates
- `text_splitter.py` - Text processing utilities
- `pdf_processer.py` - PDF processing functionality
- `base_script.py` - Base script utilities
- `BOM_run.py` - Bill of Materials processing
- `requirements.txt` - Python dependencies
