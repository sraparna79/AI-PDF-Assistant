# AI PDF Assistant

An intelligent PDF analysis tool powered by AI, designed specifically for working with research papers and academic documents.

 **Live Demo**: [pdf-read-ai.streamlit.app](https://pdf-read-ai.streamlit.app/)

## Overview

AI PDF Assistant is a Streamlit-based application that enables users to upload PDF documents and interact with them through natural language queries. Using advanced AI and vector search technology, it extracts relevant information and provides intelligent responses based on document content.

## Features

- **Easy PDF Upload**: Simple drag-and-drop interface for PDF documents
- **AI-Powered Q&A**: Ask questions and get accurate answers from your documents
- **Semantic Search**: Advanced vector-based search for finding relevant content
- **Persistent Storage**: Vector database integration for efficient retrieval
- **Research-Focused**: Optimized for academic papers and technical documents
- **Web Interface**: Clean, intuitive Streamlit UI

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sraparna79/AI-PDF-Assistant.git
cd AI-PDF-Assistant
```

2. **Install dependencies**

Using `uv` (recommended):
```bash
uv sync
```

Or using `pip`:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file in the root directory and add your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
# Add other required API keys
```

4. **Run the application**
```bash
streamlit run main.py
```

5. **Open your browser**

Navigate to `http://localhost:8501` to access the application.

## Project Structure
```
AI-PDF-Assistant/
│
├── main.py              # Main Streamlit application entry point
├── ask.py               # Question answering and response generation logic
├── data_loader.py       # PDF processing and text extraction
├── vector_db.py         # Vector database operations (Qdrant)
├── custom_types.py      # Custom type definitions and data models
│
├── uploads/             # Directory for uploaded PDF files
├── qdrant_storage/      # Vector database storage directory
├── .idea/               # IDE configuration files
│
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock             # Dependency lock file
├── .python-version      # Python version specification
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## How It Works

1. **Upload**: User uploads a PDF document through the Streamlit interface
2. **Processing**: The system extracts text from the PDF using `data_loader.py`
3. **Vectorization**: Text is chunked and converted to embeddings
4. **Storage**: Embeddings are stored in Qdrant vector database via `vector_db.py`
5. **Query**: User asks questions about the document
6. **Retrieval**: Relevant chunks are retrieved using semantic search
7. **Response**: AI generates contextual answers using `ask.py`

## 🛠️ Technologies Used

- **[Streamlit](https://streamlit.io/)**: Web application framework
- **[Qdrant](https://qdrant.tech/)**: Vector database for semantic search
- **[Python](https://www.python.org/)**: Core programming language
- **[LangChain](https://docs.langchain.com/)**: Framework for LLM applications
- **[OpenAI API](https://platform.openai.com/api-keys)**: Language model for generating responses
- **[PyPDF2/pdfplumber](https://pypi.org/project/PyPDF2/)**: PDF text extraction

## Usage Example

1. Launch the application
2. Upload your research paper (PDF format)
3. Wait for processing to complete
4. Ask questions like:
   - "What is the main hypothesis of this paper?"
   - "Summarize the methodology section."
   - "What are the key findings?"
   - "List the limitations mentioned in the study."

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Author

**Sraparna**
- GitHub: [@sraparna79](https://github.com/sraparna79)

## Acknowledgments

- Thanks to the open-source community for the amazing tools and libraries
- Inspired by the need for better tools to analyze research papers

## Contact

For questions, suggestions, or issues, please open an issue on GitHub or contact through the repository.

---

⭐ If you find this project helpful, please consider giving it a star!
