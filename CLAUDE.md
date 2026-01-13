# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Retrieval-Augmented Generation (RAG) chatbot** for querying course materials. It uses ChromaDB for vector storage, Anthropic's Claude API for AI generation, and provides a web interface for interaction.

**Tech Stack:**
- Backend: FastAPI + Uvicorn (Python 3.13+)
- Frontend: Vanilla JavaScript with marked.js for markdown rendering
- Vector Storage: ChromaDB with sentence-transformers (all-MiniLM-L6-v2)
- AI Model: Claude Sonnet 4 (claude-sonnet-4-20250514)
- Package Manager: uv

## Development Commands

**IMPORTANT: Always use UV for everything—running Python files, managing dependencies, and running the server. Never use PIP or raw Python commands directly.**

This project uses `uv` as the package manager. All Python commands must be prefixed with `uv run` (e.g., `uv run python script.py`) to ensure the correct dependencies and environment are used. All dependency changes must be made through `uv add`, `uv remove`, or `uv sync`—never through pip.

### Environment Setup
```bash
# Install uv package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (never use pip install)
uv sync

# Create .env file with required API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Running the Application
```bash
# Quick start (recommended)
chmod +x run.sh
./run.sh

# Manual start from backend directory
cd backend
uv run uvicorn app:app --reload --port 8000

# The application will be available at:
# - Web Interface: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Development Workflow

**Always prefix Python commands with `uv run` to ensure correct environment and dependencies.**

```bash
# Run specific Python module (always use uv run)
uv run python -m backend.module_name

# Run Python scripts with dependencies (always use uv run)
uv run python script.py

# Run any Python file (always use uv run)
uv run python main.py

# Start with custom port
cd backend
uv run uvicorn app:app --reload --port 9000
```

### Dependency Management

**CRITICAL: Use UV to manage all dependencies. Never use pip directly.**

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade

# Update a specific package
uv add package-name --upgrade

# Remove a dependency
uv remove package-name

# View installed packages
uv pip list

# Lock dependencies (uv.lock is automatically updated)
uv lock
```

Dependencies are specified in `pyproject.toml` and locked in `uv.lock`. Always commit both files after adding or updating dependencies.

**Note:** This project currently has no test suite, linting configuration, or build process.

## Architecture Overview

### System Flow: User Query → AI Response

```
User Query (Frontend)
    ↓
POST /api/query → FastAPI (app.py)
    ↓
RAGSystem.query() orchestrates:
    ├→ SessionManager: Retrieves conversation history
    ├→ AIGenerator: Calls Claude API with tools
    │   └→ If Claude uses search_course_content tool:
    │       ├→ ToolManager executes CourseSearchTool
    │       ├→ VectorStore.search() queries ChromaDB
    │       │   ├→ Resolves course name via semantic search
    │       │   └→ Searches course_content collection with filters
    │       └→ Returns results to Claude for final answer
    ├→ SessionManager: Saves exchange to history
    └→ Returns QueryResponse with answer + sources
    ↓
Frontend renders markdown response + sources
```

**Key Design Pattern:** Claude acts as an intelligent router—it decides whether to search the vector database or answer from its training knowledge based on the query type.

### Component Architecture

**Backend Structure (`/backend`):**
- `app.py` - FastAPI application with 2 endpoints: `/api/query`, `/api/courses`
- `rag_system.py` - Main orchestrator coordinating all components
- `vector_store.py` - ChromaDB wrapper managing two collections
- `ai_generator.py` - Claude API integration with tool-use support
- `document_processor.py` - Parses and chunks course documents
- `search_tools.py` - Tool definitions for Claude's function calling
- `session_manager.py` - In-memory conversation history per session
- `models.py` - Pydantic models: Course, Lesson, CourseChunk, SearchResults
- `config.py` - Centralized configuration (singleton pattern)

**Frontend Structure (`/frontend`):**
- `index.html` - Chat interface with collapsible sidebar
- `script.js` - Vanilla JS handling API calls and UI updates
- `style.css` - Dark theme with CSS custom properties

### ChromaDB Vector Storage Architecture

**Two Separate Collections:**

1. **`course_catalog`** - Course metadata
   - Documents: Course titles
   - Metadata: instructor, course_link, lessons_json (serialized)
   - IDs: Course title (unique identifier)
   - Purpose: Course name resolution via semantic search

2. **`course_content`** - Actual course material
   - Documents: Text chunks (800 chars, 100 overlap)
   - Metadata: course_title, lesson_number, chunk_index
   - IDs: `{course_title}_{chunk_index}`
   - Purpose: Content search with metadata filtering

**Search Flow:**
```python
VectorStore.search(query, course_name?, lesson_number?)
    ├→ If course_name provided: _resolve_course_name() fuzzy matches
    ├→ _build_filter() constructs ChromaDB where clause
    └→ course_content.query() returns up to 5 results
```

### Document Processing Pipeline

**Expected Format in `/docs` directory:**
```
Course Title: MCP: Build Rich-Context AI Apps
Course Link: https://example.com/course
Course Instructor: Instructor Name

Lesson 0: Introduction
Lesson Link: https://example.com/lesson0
[Lesson content here]

Lesson 1: Foundations
Lesson Link: https://example.com/lesson1
[Lesson content here]
```

**Processing Steps:**
1. Extract metadata via regex (title, link, instructor)
2. Parse lessons by "Lesson {number}: {title}" markers
3. Chunk text on sentence boundaries (respects CHUNK_SIZE)
4. Prepend course/lesson context to each chunk
5. Store in ChromaDB: catalog (metadata) + content (chunks)

**Documents are loaded on FastAPI startup** from `/docs` folder. Processing is idempotent—courses are only added if they don't already exist in ChromaDB.

### Configuration System

All settings are centralized in `backend/config.py` as a singleton:

```python
config = Config()  # Used throughout codebase

# Key settings:
ANTHROPIC_API_KEY: str      # From .env (required)
ANTHROPIC_MODEL: str        # claude-sonnet-4-20250514
EMBEDDING_MODEL: str        # all-MiniLM-L6-v2
CHUNK_SIZE: int            # 800 characters
CHUNK_OVERLAP: int         # 100 characters
MAX_RESULTS: int           # 5 documents max
MAX_HISTORY: int           # 2 message pairs remembered
CHROMA_PATH: str           # ./chroma_db
```

### Session & Conversation Management

**SessionManager Design:**
- In-memory storage: `sessions = {session_id: [Message, ...]}`
- Max history: 2 exchanges (4 messages total)
- Automatically trims older messages when limit exceeded
- Sessions are not persisted—restart clears all history

**History Format Sent to Claude:**
```
User: What is RAG?
Assistant: RAG stands for...
User: How does it work?
Assistant: The process involves...
```

### AI Tool Use System

**Claude is provided with one tool: `search_course_content`**

```python
{
    "name": "search_course_content",
    "input_schema": {
        "query": str,              # Required - semantic search query
        "course_name": str,        # Optional - filter by course
        "lesson_number": int       # Optional - filter by lesson
    }
}
```

**System Prompt Strategy:**
- Instructs Claude to search ONLY for course-specific questions
- Allows ONE search per query maximum
- General knowledge questions answered without searching
- No meta-commentary about searches in responses

**Tool Execution Flow:**
1. Claude returns `stop_reason="tool_use"` with tool_use block
2. Extract tool parameters (query, course_name, lesson_number)
3. Execute CourseSearchTool via ToolManager
4. Format results as tool_result messages
5. Send back to Claude for final synthesis
6. Return final text response to user

## File Locations and Patterns

### Adding New Course Materials
Place `.txt` files in `/docs` directory following the expected format above. Files are automatically processed on server restart.

### Modifying Vector Store Logic
- `backend/vector_store.py` - Search logic, filtering, course name resolution
- Note: Two collections with different purposes (catalog vs content)

### Changing AI Behavior
- `backend/ai_generator.py` - System prompt, model selection, tool handling
- `backend/search_tools.py` - Tool definitions and descriptions

### Adding New Tools
1. Define tool schema in `search_tools.py` (BaseTool subclass)
2. Register in ToolManager
3. Update system prompt in `ai_generator.py`
4. No frontend changes needed—tool use is transparent

### Frontend Modifications
- `frontend/script.js` - API client, message rendering, session management
- `frontend/style.css` - CSS custom properties for theming: `--primary-color`, `--bg-color`, etc.
- `frontend/index.html` - Layout structure (sidebar + chat area)

### Configuration Changes
Edit `backend/config.py` or set environment variables in `.env`. Config is loaded once at startup.

## API Endpoints

### POST /api/query
Query the RAG system.

**Request:**
```json
{
  "query": "What topics are covered in lesson 2?",
  "session_id": "session_1"  // optional
}
```

**Response:**
```json
{
  "answer": "Claude's response with markdown formatting...",
  "sources": ["Course Name - Lesson 2", "Course Name - Lesson 3"],
  "session_id": "session_1"
}
```

### GET /api/courses
Get course statistics.

**Response:**
```json
{
  "total_courses": 4,
  "course_titles": ["MCP: Build Rich-Context AI Apps", "RAG", ...]
}
```

## Critical Design Decisions

1. **Two ChromaDB collections**: Separate catalog for fast name resolution, content for actual search
2. **Sentence-based chunking**: Preserves semantic boundaries better than fixed-size chunks
3. **Tool-use over RAG pipeline**: Claude decides when to search—more flexible than always searching
4. **Server-side sessions**: In-memory storage, no client-side secrets required
5. **No build process**: Vanilla JS, no transpilation or bundling needed
6. **Course title as unique ID**: Simple, human-readable identifier for all operations

## Common Pitfalls

- **Running Python without uv**: NEVER run `python script.py` directly. Always use `uv run python script.py` to ensure correct environment and dependencies
- **Using pip for dependency management**: NEVER use `pip install`, `pip uninstall`, or `pip freeze`. Always use `uv add`, `uv remove`, or `uv sync`. This ensures dependencies are properly tracked in `pyproject.toml` and `uv.lock`
- **Modifying pyproject.toml manually**: Use `uv add` to add dependencies instead of manually editing `pyproject.toml`—this ensures the lock file stays in sync
- **Empty `/docs` folder**: Server starts but no courses available to query
- **Missing ANTHROPIC_API_KEY**: App starts but fails on first query
- **ChromaDB port conflicts**: If port 8000 in use, specify different port in uvicorn command
- **Session memory limits**: MAX_HISTORY=2 means only last 2 exchanges remembered; older context is lost
- **Course name matching**: Uses semantic search—exact match not required, but very different names may not resolve correctly
