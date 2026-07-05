# ResearchPilot AI — Implementation Details

This document outlines the recent massive overhaul and implementation phases completed to bring ResearchPilot AI to a production-ready state.

## Phase 1: Stabilization & Bug Fixes

The initial focus was on fixing architectural bugs and stabilizing the core environment.

*   **Database Connection Leaks**: Replaced a flawed generator-based `get_db()` with a robust `@contextmanager` that ensures PostgreSQL sessions are always closed. Added a connection pool (`pool_size=5`, `max_overflow=10`).
*   **Duplicate Imports & Conflicts**: Cleaned up `search.py` by removing conflicting DuckDuckGo libraries, standardizing on `ddgs`.
*   **Model Switching & Reliability**: Fixed the `use_quality` flag in `core/llm.py` so it properly routes complex tasks (like report writing) to the higher-tier Gemini model. Implemented exponential backoff for rate-limit handling (429/quota errors).
*   **State Management**: Hardened `AgentState` by using Pydantic's `Field(default_factory=list)` to prevent mutable default argument bugs across agent runs.
*   **Schema Updates**: Migrated the PostgreSQL schema to include columns for tracking `sources`, `review` scores, and research `depth`.

## Phase 2: Citations & Report Quality

We implemented a robust citation tracking system to ensure the AI's claims are verifiable.

*   **CitationManager**: A new core component (`core/citation_manager.py`) that deduplicates sources by URL, assigns sequential reference numbers (`[1]`, `[2]`), and formats sources for LLM injection.
*   **Inline Citations**: The `WriterAgent` prompt was completely rewritten to force the LLM to use inline citations tied directly to the `CitationManager`'s tracked sources.
*   **Auto-Bibliography**: Reports now automatically append a generated `## References` section mapping the inline numbers to actual URLs and access dates.
*   **Reviewer LLM-as-a-Judge**: The `ReviewerAgent` prompt was updated to output strict JSON, providing quantitative scores (Depth, Accuracy, Clarity) and qualitative feedback (Strengths, Weaknesses, Suggestions).

## Phase 3: Advanced RAG (Retrieval-Augmented Generation)

To ensure the assistant builds on past knowledge, the RAG implementation was significantly upgraded.

*   **Semantic Chunker**: Built a custom `SemanticChunker` (`rag/chunker.py`) that intelligently splits documents first by Markdown headings, then by paragraphs, preserving document structure and section context in the chunk metadata.
*   **Singleton Vectorstore**: Refactored `rag/vectorstore.py` to use a singleton pattern for the HuggingFace embeddings and ChromaDB client, dramatically improving performance across pipeline runs.
*   **Relevance Filtering**: Updated the retrieval logic to use `similarity_search_with_score()`, filtering out irrelevant past research using distance thresholds.

## Phase 4: UI Polish & Human-in-the-Loop

The frontend was completely rewritten to be interactive, transparent, and aesthetically pleasing.

*   **Dark Theme & Glassmorphism**: Added custom CSS (`frontend/styles.py`) utilizing CSS gradients, backdrop filters, and smooth animations to give the app a premium feel.
*   **Human-in-the-Loop (HITL)**: The workflow in `main.py` now pauses after the PlannerAgent runs. The user is presented with the generated research questions and can edit, add, or delete them before approving the plan.
*   **Pipeline Visualization**: Added a visual progress tracker (`Planner → Approve → Researcher → Writer → Complete`) that highlights the active agent.
*   **Componentization**: Split the massive `main.py` into manageable UI components (`frontend/components/`):
    *   `sidebar.py`: Handles history loading and settings.
    *   `progress.py`: Handles findings preview and source lists.
    *   `report_viewer.py`: Renders the final Markdown, the structured review scorecards, and export buttons.
*   **Robust Exporting**: Upgraded `tools/document.py` to properly parse Markdown (bold, italic, links, lists) into both PDF (via ReportLab) and DOCX formats.
