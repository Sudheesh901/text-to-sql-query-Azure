# Beavelo

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-API-009688) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b) ![Azure](https://img.shields.io/badge/Azure-OpenAI%20%2B%20Search-0078D4)

Beavelo is a production-style natural language to SQL assistant for business users. It translates plain-English questions into safe, read-only MySQL queries and returns results through both a Streamlit web app and a FastAPI API.

The system is designed for non-technical users who need answers from an existing sales database without writing SQL manually. It combines Azure OpenAI for query generation, Azure AI Search for schema retrieval, and a database execution layer that enforces safety constraints.

## Table of contents

- [Why this project exists](#why-this-project-exists)
- [Key features](#key-features)
- [Architecture overview](#architecture-overview)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Quick start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the application](#running-the-application)
- [API usage](#api-usage)
- [Safety and validation model](#safety-and-validation-model)
- [Evaluation and testing](#evaluation-and-testing)
- [Contributing](#contributing)
- [License](#license)

## Why this project exists

Many business teams need fast access to operational data, but writing SQL is still a barrier. Beavelo lowers that barrier by allowing users to ask questions such as:

- "Which customers are in Germany?"
- "Show the top 3 products by revenue."
- "What were the highest-selling orders last month?"

The application converts those requests into SQL, validates the output, and returns the query results in a controlled and safe way.

---

## Key features

- Natural language query understanding for business questions
- Safe SQL generation with strict read-only enforcement
- Automatic schema context retrieval from a searchable catalog
- Support for clarification when a request is ambiguous
- Streamlit-based interactive UI for end users
- FastAPI backend for integration into downstream systems
- Evaluation scripts for baseline quality testing
- MySQL-backed execution with validation safeguards

---

## Architecture overview

```mermaid
flowchart LR
    A[User question] --> B[Streamlit UI]
    B --> C[FastAPI API]
    C --> D[Azure AI Search]
    D --> E[Azure OpenAI]
    E --> F[Safety validation]
    F --> G[MySQL execution]
    G --> H[Results returned to user]
```

### Components

- Streamlit frontend: interactive conversational experience for asking questions
- FastAPI service: API endpoint for programmatic access
- text_to_sql.py: orchestrates schema lookup, prompt construction, SQL generation, and validation
- database.py: executes generated SQL against MySQL
- create_and_upload_index.py: builds and populates the Azure AI Search index
- scripts/: evaluation and schema verification utilities

---

## Tech stack

- Python 3.10+
- Streamlit for the frontend experience
- FastAPI for API endpoints
- Azure OpenAI for LLM-based SQL generation
- Azure AI Search for schema and relationship retrieval
- MySQL for the source database
- pandas for tabular processing
- pytest for automated API tests

---

## Project structure

```text
.
├── app.py                      # Streamlit application entry point
├── text_to_sql.py              # SQL generation and safety logic
├── database.py                 # MySQL connection and query execution
├── api/
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # Request and response models
│   └── services/
│       └── query_service.py    # API orchestration logic
├── create_and_upload_index.py  # Upload schema catalog to Azure AI Search
├── data/
│   └── aaitech_vector_schema_info.csv
├── docs/
│   └── phase-1-definition.md
├── evaluation/
│   └── golden_questions.json
├── scripts/
│   ├── run_baseline_eval.py
│   └── verify_schema_catalog.py
├── tests/
│   └── test_api.py
├── requirements.txt
└── .env                        # Local environment variables (not committed)
```

---

## Quick start

If you want to get up and running quickly, the typical flow is:

1. Install dependencies with `pip install -r requirements.txt`
2. Create a `.env` file with your Azure OpenAI, Azure AI Search, and MySQL credentials
3. Run `python create_and_upload_index.py` to populate the search catalog
4. Start the API with `uvicorn api.main:app --reload --port 8000`
5. Launch the UI with `streamlit run app.py`

> For the full setup and environment details, continue to the sections below.

---

## Prerequisites

Before running the project, make sure you have:

- Python 3.10 or newer installed
- Access to a MySQL instance with the relevant business tables available
- An Azure OpenAI deployment
- An Azure AI Search service and index
- A populated schema catalog file in the data folder

---

## Environment configuration

Create a .env file in the project root with the required variables:

```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
DEPLOYMENT_NAME=your-chat-deployment
API_VERSION=2024-02-01

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key
INDEX_NAME=your-index-name
TEXT_EMBEDDING_MODEL=your-embedding-deployment
SEARCH_API_VERSION=2023-11-01

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your-user
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=your-database

# Optional app config
BEAVELO_API_URL=http://127.0.0.1:8000
ALLOWED_ORIGINS=http://localhost:8501
```

> The project expects these values to be present at runtime. A missing configuration can prevent both the UI and the API from functioning correctly.

---

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd text_sql_query
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Prepare the Azure AI Search index:

```bash
python create_and_upload_index.py
```

This step creates the search index and uploads schema metadata from the CSV catalog into Azure AI Search.

---

## Running the application

### 1. Start the backend API

```bash
uvicorn api.main:app --reload --port 8000
```

The API will be available at:

- Health check: http://127.0.0.1:8000/health
- Query endpoint: http://127.0.0.1:8000/v1/query

### 2. Start the Streamlit frontend

In a separate terminal:

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

---

## API usage

### Example request

```bash
curl -X POST "http://127.0.0.1:8000/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"Which customers are located in Germany?"}'
```

### Example response

```json
{
  "status": "success",
  "message": null,
  "sql": "SELECT * FROM customers WHERE country = 'Germany';",
  "columns": ["customer_id", "company_name", "country"],
  "rows": []
}
```

The API returns one of three statuses:

- success: a valid query was generated and executed
- clarification: the question was ambiguous and needs follow-up
- error: the request could not be safely processed

---

## Safety and validation model

One of the most important design principles of this project is that it only generates read-only SQL. The implementation explicitly checks for:

- a single SELECT statement
- no destructive statements such as UPDATE, DELETE, or DROP
- table names that are validated against the known schema catalog
- safe handling of ambiguous requests through clarifying questions

This makes the system appropriate for internal business analytics use cases where data safety and governance matter.

---

## Evaluation and testing

### Run unit and API tests

```bash
pytest
```

### Run baseline evaluation

```bash
python scripts/run_baseline_eval.py
```

Use the live flag if you want to execute generated SQL against the configured MySQL database:

```bash
python scripts/run_baseline_eval.py --live
```

### Verify schema catalog alignment

```bash
python scripts/verify_schema_catalog.py
```

This script checks whether the schema metadata in the catalog matches the actual MySQL schema.

---

## Sample data

The repository includes sample CSV files under the data folder, including business data related to customers, products, orders, suppliers, and order details. These files are used to support the schema catalog and the overall demo experience.

---

## Known limitations

- The system is focused on read-only business analytics queries.
- It depends on the quality of the schema catalog and Azure AI Search index.
- Complex multi-step reasoning or highly ambiguous questions may require clarification.
- The current implementation is optimized for the provided database schema and use case, rather than arbitrary SQL generation across every possible dataset.

---

## Roadmap

Potential next steps for the project include:

- richer query explanation and result summarization
- support for more advanced analytics questions
- improved prompt tuning and evaluation metrics
- authentication and authorization layers
- monitoring, observability, and deployment packaging for production environments

---

## Contributing

Contributions are welcome. If you would like to improve the project, please open an issue or submit a pull request with a clear explanation of the change.

Suggested areas for contribution:

- prompt quality improvements
- better validation logic
- new evaluation cases
- UI/UX enhancements
- API and performance improvements

---

## License

This project is intended for educational and demonstration purposes unless a separate license is provided by the repository owner.
