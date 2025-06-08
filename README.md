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
# 🔑 REQUIRED: Standard Gemini API (DEFAULT)
GEMINI_API_KEY=your_gemini_api_key_here

# 🔑 OPTIONAL: Vertex AI Configuration (only needed if switching from default)
VERTEX_API_KEY=your_vertex_ai_api_key_here  # Only required if using Vertex AI
USE_VERTEX_AI=false  # DEFAULT: false (uses Gemini), set to 'true' for Vertex AI

# 🔑 LEGACY: Other API keys (if needed for other parts of the system)
GOOGLE_API_KEY=your_google_api_key_here
```

**🤖 API Configuration (DEFAULT: Standard Gemini):**
- **Standard Gemini API** (DEFAULT): Easy setup, good for development and most use cases
- **Vertex AI**: Enterprise features, better rate limits, requires Google Cloud setup

**📋 Quick Setup for New Developers:**
1. **Default (Recommended)**: Just add `GEMINI_API_KEY` to your `.env` file - you're done!
2. **Advanced**: To use Vertex AI, also add `VERTEX_API_KEY` and set `USE_VERTEX_AI=true`

#### 4. Verify Installation

You can verify the installation by running:

```bash
pip list
```

### Usage

After completing the setup, you can run the various scripts in the project:

#### Main Scripts:
- `python run_script.py` - Main processing script with AI integration
- `python ai.py` - AI processing functionality  
- `python data_cleansing.py` - Data cleaning operations
- `python BOM_run.py` - BOM processing script

#### Configuration Scripts:
- `python api_config_examples.py` - Examples of different API and model configurations

#### API and Model Configuration:

The system supports both **Standard Gemini API** and **Vertex AI** with flexible model selection:

**1. Configure in `run_script.py`:**
```python
# At the top of run_script.py, modify these settings:
USE_VERTEX_AI = True  # True for Vertex AI, False for Standard Gemini
MODEL_NAME = "gemini-1.5-pro"  # Specify your preferred model
```

**2. Available Models:**
- `gemini-2.0-flash-001` - Latest Gemini 2.0 (recommended)
- `gemini-1.5-pro` - Stable Gemini 1.5 Pro
- `gemini-1.5-flash` - Faster Gemini 1.5 Flash
- `gemini-2.5-flash-preview-05-20` - Preview version

**3. Programmatic Configuration:**
```python
from ai import material_checker, set_vertex_ai_mode

# Global API toggle
set_vertex_ai_mode(True)  # Switch to Vertex AI

# Instance-specific configuration
processor = material_checker(
    df_material_file="data.xlsx",
    system_instructions="instructions",
    path_for_excel="output",
    use_vertex_ai=True,
    model_name="gemini-1.5-pro"
)

# Runtime changes
processor.set_vertex_ai_mode(False)  # Switch to Standard Gemini
processor.set_model_name("gemini-2.0-flash-001")  # Change model
```

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
