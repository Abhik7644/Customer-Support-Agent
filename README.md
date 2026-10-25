# Customer Support AI Agent

An AI-powered customer support system for e-commerce that combines **LLM-based reasoning, Retrieval-Augmented Generation (RAG), database-backed tools, and a web interface** to help customers resolve order, product, refund, and policy-related queries.

**Repository:** [Abhik7644/Customer-Support-Agent](https://github.com/Abhik7644/Customer-Support-Agent)

## Overview

Traditional customer support often requires customers to navigate multiple pages or wait for a human agent to answer routine questions. This project explores how an AI agent can understand a customer's request, retrieve relevant company policies, access authorized order information, and coordinate support workflows through backend tools.

Instead of relying only on generated text, the agent can use application tools to retrieve information from the knowledge base and database.

**Core principle:** The AI decides which tool is needed; the backend controls what the tool is allowed to do.

## Key Features

- **Conversational AI:** Understands natural-language customer support queries.
- **RAG-based policy assistance:** Retrieves relevant information from company policy and FAQ documents.
- **Order management:** Uses backend tools to retrieve order-related information.
- **Refund workflows:** Supports refund eligibility and status checks through application logic.
- **Database integration:** Uses PostgreSQL for structured application data.
- **Authentication:** JWT-based authentication with password hashing.
- **Customer data isolation:** Restricts customer-specific operations using authenticated identity and backend authorization.
- **Human approval workflow:** Supports human review for high-value refund requests, according to the configured workflow.
- **Evaluation and testing:** Includes retrieval, tool-selection, groundness, and application tests.
- **Web interface:** React-based frontend for customer login and support conversations.

## Technology Stack

| Component | Technologies |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| Agent orchestration | LangGraph |
| LLM integration | Groq; configurable OpenAI provider |
| Retrieval pipeline | LangChain, HuggingFace embeddings |
| Vector database | ChromaDB |
| Relational database | PostgreSQL |
| Authentication | JWT, bcrypt |
| Frontend | React, JavaScript, Vite |
| Testing | Pytest |
| Evaluation | Retrieval, answer-grounding, and tool-selection evaluation |

## System Architecture

```text
Customer
   |
   v
React Frontend
   |
   v
FastAPI + JWT Authentication
   |
   v
LangGraph Agent
   |
   +----> Policy Retrieval Tool
   |           |
   |           v
   |       ChromaDB
   |           ^
   |           |
   |       Policy PDFs
   |
   +----> Order / Product / Refund Tools
   |           |
   |           v
   |       PostgreSQL
   |
   +----> LLM Reasoning and Tool Selection
               |
               v
        Final Support Response
```

The application uses separate components for language-model reasoning, document retrieval, structured data access, and business logic. The backend remains responsible for authorization and executing operations.

## Project Structure

```text
Customer-Support-Agent/
├── backend/
│   └── app/
│       ├── agent_v2.py
│       ├── auth.py
│       ├── config.py
│       ├── database.py
│       ├── dependencies.py
│       ├── main.py
│       ├── rag/
│       │   └── ingest.py
│       └── tools/
│           ├── order_tools.py
│           ├── product_tools.py
│           └── rag_tools.py
├── data/
│   └── documents/
├── database/
│   ├── schema.sql
│   └── seed.sql
├── evaluation/
├── frontend/
├── tests/
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── run_script.py
```

Generated vector-store files are excluded from version control and should be regenerated from the source documents when required.

## Getting Started

### Prerequisites

Install the following before setting up the application:

- Python compatible with the project's dependencies
- Node.js and npm
- PostgreSQL
- A Groq API key, or an OpenAI API key if using that provider

### 1. Clone the repository

```bash
git clone https://github.com/Abhik7644/Customer-Support-Agent.git
cd Customer-Support-Agent
```

### 2. Set up the Python environment

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file from the example:

```bash
copy .env.example .env
```

Edit `.env` with your own configuration. At minimum, configure the LLM provider, the appropriate API key, PostgreSQL connection details, and a securely generated JWT secret.

Never commit `.env` or real credentials to GitHub.

### 4. Initialize PostgreSQL

Create the database specified in your configuration, then execute the SQL files from the project root:

```bash
psql -U postgres -d support_agent_db -f database/schema.sql
psql -U postgres -d support_agent_db -f database/seed.sql
```

Replace the database name and username if your local configuration differs. Review the seed script before running it, and use only synthetic development data.

### 5. Build the knowledge base

The policy documents are located in `data/documents/`.

The ingestion module at `backend/app/rag/ingest.py` prepares the documents for retrieval and stores their embeddings in ChromaDB. Run the ingestion process using the entry point and invocation supported by that module.

The generated vector store can be recreated from the source documents.

### 6. Start the backend

From the repository root, first check the imports and startup configuration in `backend/app/main.py` and `run_script.py`. Use the entry point configured by the project.

For a standard Uvicorn setup where the application is importable as `app.main`, run:

```bash
cd backend
uvicorn app.main:app --reload
```

Once the server starts, open the FastAPI interactive documentation at:

`http://127.0.0.1:8000/docs`

### 7. Start the frontend

Open a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Use the local URL printed by Vite. Ensure the frontend API configuration points to the running backend.

> **Setup note:** Exact startup and ingestion commands may depend on the current imports and entry points in the repository. If a command fails, inspect the corresponding module rather than assuming that the service started successfully.

## Security Design

Security is an important part of the system's design:

- **Authentication:** JWTs identify authenticated customers.
- **Authorization:** Customer-specific database operations must be scoped to the authenticated customer.
- **Parameterized SQL:** Query parameters help prevent SQL injection.
- **Backend-enforced business rules:** Refund eligibility and other sensitive decisions should be validated in application code, not trusted to the LLM.
- **Secret management:** API keys, database credentials, and JWT signing secrets belong in environment configuration.
- **Human oversight:** High-value refund actions can require approval before execution.

These controls should be verified with the test suite and code review before deploying the application in a production environment.

## Testing

Run the backend tests from the repository root:

```bash
pytest
```

The repository includes tests covering database operations, order tools, product tools, and RAG retrieval and tool behavior.

Review test results in your local environment before treating a feature as verified.

## Evaluation

The `evaluation/` directory contains evaluation resources for:

- Retrieval quality
- Answer grounding
- Tool selection

These resources can help assess whether the agent retrieves useful evidence, produces grounded answers, and selects appropriate tools for customer requests.

## Current Scope and Future Improvements

Potential next steps include:

- Add automated CI checks for tests and code quality.
- Expand retrieval and tool-selection evaluation.
- Improve structured logging and error handling.
- Add deployment configuration and operational monitoring.
- Strengthen integration tests for authentication, customer isolation, and refund approval.
- Add screenshots and a demonstration video to document the user experience.

## Contributing

Contributions and suggestions are welcome. For significant changes, open an issue to discuss the proposed improvement before submitting a pull request.

## Author

**Abhinash Kumar**

GitHub: [@Abhik7644](https://github.com/Abhik7644)

---

*This project is intended for learning, experimentation, and demonstration of AI-agent engineering concepts. Production deployment requires appropriate security, reliability, and operational validation.*
