# ResearchPilot AI — Implementation Details

> How distributed computing principles were applied to build an industrial-grade multi-agent AI system.

---

## Table of Contents

- [Overview](#overview)
- [Phase 1: Stabilization & Core Infrastructure](#phase-1-stabilization--core-infrastructure)
- [Phase 2: Citation Pipeline & Report Quality](#phase-2-citation-pipeline--report-quality)
- [Phase 3: Advanced RAG (Distributed Storage)](#phase-3-advanced-rag-distributed-storage)
- [Phase 4: UI, HITL Consensus & Pipeline Visualization](#phase-4-ui-hitl-consensus--pipeline-visualization)
- [Phase 5: API Call Optimization (Batched RPC)](#phase-5-api-call-optimization-batched-rpc)
- [Distributed Computing Mapping Summary](#distributed-computing-mapping-summary)
- [Files Changed](#files-changed)

---

## Overview

ResearchPilot AI was built across 5 phases, each addressing a specific distributed systems challenge:

| Phase | Focus Area | Key Distributed Concept |
|---|---|---|
| **1** | Stabilization | Resource pooling, connection management, middleware |
| **2** | Citations | Data integrity, transaction management, serialization |
| **3** | RAG | Distributed storage, chunking (GFS/HDFS analog), replication |
| **4** | UI + HITL | Consensus protocol, barrier synchronization, message passing |
| **5** | Optimization | Batched RPC, reducing network round-trips |

---

## Phase 1: Stabilization & Core Infrastructure

### Problem
The initial codebase had resource leaks, race conditions on configuration, and no fault tolerance.

### Solutions Implemented

#### 1.1 Connection Pool (Resource Management)

**Before:** Each database call opened and leaked a new connection.

**After:** Implemented a **connection pool** using SQLAlchemy — a core distributed systems pattern for managing expensive shared resources.

```
┌─────────────────────────────────────────────────┐
│  Connection Pool (database/connection.py)       │
│                                                 │
│  pool_size=5       Pre-allocated connections     │
│  max_overflow=10   Burst capacity               │
│  pool_pre_ping=True Health check before use     │
│  pool_recycle=1800  Refresh stale connections    │
│                                                 │
│  Pattern: Resource Pooling                      │
│  Analog:  Thread pool in a distributed server   │
└─────────────────────────────────────────────────┘
```

**Files:** `database/connection.py` — `@contextmanager` ensures sessions are always returned to the pool.

#### 1.2 LLM Router with Failover (Fault Tolerance)

**Before:** Single LLM provider. If Gemini was down, the entire app crashed.

**After:** Triple-redundant LLM routing with automatic failover and exponential backoff.

```
  Request ──▶ Gemini (try 3x with backoff)
                 │ fail
                 ▼
              Groq (try 1x)
                 │ fail
                 ▼
              Mock (always succeeds)
```

**Distributed concept:** This is exactly how **Active-Passive failover** works in production systems. The primary (Gemini) handles all traffic. On failure, a passive standby (Groq) takes over transparently.

**Files:** `core/llm.py` — `get_llm_response()` with retry decorator and provider cascade.

#### 1.3 State Management (IPC via Shared Memory)

**Before:** Agents passed strings around with no structure.

**After:** Created `AgentState` — a Pydantic model that acts as the **shared memory segment** between all agents.

**Distributed concept:** In multi-process systems, processes communicate via shared memory segments. `AgentState` is our in-memory IPC channel. Pydantic handles **marshalling/unmarshalling** (serialization) of complex nested data structures.

**Files:** `core/state.py` — Replaced mutable default args with `Field(default_factory=list)` to prevent cross-request state contamination.

#### 1.4 Search Caching (Cache-Aside Pattern)

**Before:** Identical search queries were sent repeatedly to DuckDuckGo, wasting bandwidth and triggering rate limits.

**After:** Implemented TTL-based in-memory caching with the **Cache-Aside** pattern.

**Distributed concept:** This is equivalent to placing a **Redis cache** in front of a database. On cache hit, we avoid the expensive network call entirely. The 10-minute TTL ensures data freshness.

**Files:** `tools/search.py` — `@lru_cache`-style dictionary with timestamp checking.

---

## Phase 2: Citation Pipeline & Report Quality

### Problem
Reports contained claims with no attribution. Sources were lost between agents.

### Solutions Implemented

#### 2.1 CitationManager (Distributed State Tracking)

A new component that tracks, deduplicates, and serializes source references across the entire agent pipeline.

```
  Researcher ──register──▶ CitationManager ──format──▶ Writer
                           │
                           │  • Dedup by URL (idempotent)
                           │  • Assign ref numbers [1],[2]
                           │  • Serialize for DB storage
                           │  • Reconstruct from DB load
                           │
                           ▼
                     Consistent Reference State
```

**Distributed concept:** The CitationManager maintains a **single source of truth** for reference data, ensuring that the Writer's citations are consistent with what the Researcher discovered. This is analogous to a **naming service** in distributed systems — it provides a canonical mapping from URL to reference number.

**Files:** `core/citation_manager.py`

#### 2.2 Atomic History Saves (Distributed Transactions)

Research results are saved atomically: if saving the review fails, the entire transaction rolls back.

**Distributed concept:** This follows the **ACID transaction** model. The `@contextmanager` on the database session acts as the transaction boundary. `session.commit()` is the commit point; any exception triggers `session.rollback()`.

**Files:** `core/history.py` — `save_history()` with duplicate detection and atomic commits.

#### 2.3 Prompt Engineering as RPC Contracts

Each agent's prompt template is essentially an **RPC interface contract** — it defines:
- The **input schema** (what data to send: `{topic}`, `{findings_text}`, `{sources_text}`)
- The **output schema** (what format to expect: JSON with specific keys)
- The **error handling** (what to do if the LLM returns malformed output)

**Files:** `core/prompts.py` — All four prompts rewritten with strict JSON output schemas.

---

## Phase 3: Advanced RAG (Distributed Storage)

### Problem
Raw text was stored in ChromaDB without structure, leading to poor retrieval quality.

### Solutions Implemented

#### 3.1 Semantic Chunker (Block Allocation)

Inspired by how **HDFS splits files into blocks**, the SemanticChunker splits research reports into meaningful chunks:

```
  Full Report (e.g., 5000 chars)
        │
        ▼
  ┌─────────────────────────┐
  │   Split by Headings     │  (like HDFS splitting by block boundaries)
  │   # Section 1           │
  │   ## Subsection 1.1     │
  │   # Section 2           │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │  Split by Paragraphs    │  (within each heading block)
  │  Merge small paragraphs │
  │  Target: ~500 chars     │  (like HDFS 128MB block target)
  │  Overlap: 50 chars      │  (for context continuity)
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │  Store with Metadata    │
  │  • section_title        │  (like GFS chunk metadata at Master)
  │  • topic                │
  │  • timestamp            │
  │  • depth                │
  └─────────────────────────┘
```

**Key difference from HDFS:** HDFS uses fixed-size blocks; we use **semantic boundaries** (headings, paragraphs) because our read pattern is similarity-based, not sequential.

**Files:** `rag/chunker.py`

#### 3.2 Singleton Vectorstore (Mutual Exclusion)

**Before:** Every pipeline run created a new ChromaDB client and loaded a new embedding model (~2GB).

**After:** Singleton pattern ensures exactly one instance exists.

**Distributed concept:** The singleton acts as a **mutex-protected critical section**. The first caller initializes the expensive resource; all subsequent callers reuse it. In a multi-threaded server, this prevents concurrent initialization from corrupting shared state.

**Files:** `rag/vectorstore.py` — Global `_embeddings` and `_vectorstore` with null-check initialization.

#### 3.3 Relevance Filtering (Quality of Service)

**Before:** All retrieved chunks were included, regardless of relevance.

**After:** `similarity_search_with_score()` with a distance threshold filters out irrelevant results.

**Distributed concept:** This is analogous to **QoS (Quality of Service)** in network communication — we drop low-quality packets (irrelevant chunks) rather than forwarding everything.

**Files:** `rag/vectorstore.py` — `retrieve_context()` with threshold filtering.

---

## Phase 4: UI, HITL Consensus & Pipeline Visualization

### Problem
The UI was minimal, there was no way for users to approve research plans, and the pipeline was opaque.

### Solutions Implemented

#### 4.1 Human-in-the-Loop Consensus (HITL)

Implemented a **propose-approve consensus protocol** where the Planner proposes a research plan and the user must explicitly approve it.

```
  Planner proposes → UI renders editable questions →
  User edits → User clicks "Approve" → Pipeline continues
                                  OR
              User clicks "Regenerate" → Planner re-proposes
```

**Distributed concept:** This maps directly to the **Paxos prepare/accept** phases:
1. **Prepare (Propose):** Planner generates questions
2. **Promise:** UI renders the proposal for review
3. **Accept:** User approves (quorum of 1 satisfied)
4. **Learn:** Pipeline proceeds with the accepted value

**Files:** `main.py` — `st.session_state` manages the proposal/acceptance state machine.

#### 4.2 Pipeline Visualization (Process Monitoring)

A 5-step visual pipeline shows which agent is currently active:

```
  [✓ Planner] → [✓ Approve] → [● Researching] → [○ Writer] → [○ Complete]
                                  ↑ active (glowing)
```

**Distributed concept:** This is equivalent to a **process monitor** or **task scheduler dashboard** in distributed systems. It shows:
- Which "processes" (agents) have completed
- Which is currently running
- Which are waiting in the queue

**Files:** `frontend/components/progress.py`

#### 4.3 Progress Callbacks (Async Message Passing)

Agents report progress to the UI via callback functions — a form of **fire-and-forget message passing**.

**Distributed concept:** The callback is a **one-way message channel** from producer (agent) to consumer (UI). The agent never blocks waiting for the UI to render. This decouples computation from presentation.

**Files:** `agents/researcher.py`, `agents/planner.py` — `progress_callback()` invocations.

---

## Phase 5: API Call Optimization (Batched RPC)

### Problem
The Researcher Agent made one LLM API call per research question (3-8 calls depending on depth), frequently hitting Gemini's rate limits.

### Solution: Batched RPC

Instead of N individual RPC calls, we batch all questions into a single RPC call.

```
  BEFORE (N RPC calls):                AFTER (1 RPC call):
  ┌─────────┐                          ┌─────────┐
  │ Q1 ──▶ LLM ──▶ A1  │              │ [Q1,Q2,Q3] ──▶ LLM ──▶ [A1,A2,A3] │
  │ Q2 ──▶ LLM ──▶ A2  │              │ (1 call, batched)                   │
  │ Q3 ──▶ LLM ──▶ A3  │              └─────────┘
  │ (3 separate calls)  │
  └─────────┘

  Quick:  5 calls → 3 calls  (40% reduction)
  Deep:  10 calls → 3 calls  (70% reduction)
```

**Distributed concept:** This is exactly how **batched RPC** works in distributed systems — instead of incurring N network round-trips (each with latency overhead), we amortize the cost into a single round-trip. This is the same principle behind:
- **Database batch inserts** (1 INSERT with 100 rows vs 100 separate INSERTs)
- **gRPC streaming** (batch requests into a single stream)
- **MapReduce combine phase** (reduce intermediate data before network transfer)

**Trade-off:** The single batched prompt is larger (more tokens), but the total token count is similar because we avoid repeating the system prompt N times. The key saving is in **network round-trips and rate-limit slots**.

**Files:** `agents/researcher.py` — Two-phase approach: (1) gather all web data in a loop (HTTP only), (2) synthesize everything in one LLM call.

---

## Distributed Computing Mapping Summary

| Syllabus Topic | Concept | ResearchPilot Component |
|---|---|---|
| **Architecture** | Client-Server | Streamlit ↔ PostgreSQL/ChromaDB |
| | Multi-Tier | 3-tier: Presentation → Logic → Data |
| | Pipe-and-Filter | Agent Pipeline (Planner → Researcher → Writer → Reviewer) |
| | Middleware | SQLAlchemy ORM, LangChain embeddings, Pydantic serialization |
| | Microservices | Each agent as an independent unit with single responsibility |
| **Communication** | IPC (Shared Memory) | `AgentState` object passed between agents |
| | RPC | LLM API calls (prompt → HTTP → response) |
| | RESTful | Gemini REST API, DuckDuckGo HTTP, web scraping |
| | Message Passing | `progress_callback` from agents to UI |
| | Serialization | Pydantic models, JSON marshalling for LLM I/O |
| **Synchronization** | Mutual Exclusion | Singleton pattern on ChromaDB/embeddings |
| | Consensus | HITL plan approval (propose-accept protocol) |
| | Distributed Transactions | Atomic save to PostgreSQL + ChromaDB (best-effort 2PC) |
| | Deadlock Prevention | DAG pipeline (acyclic → no circular waits) |
| | Barrier Sync | Sequential pipeline (Writer waits for Researcher) |
| **Resource Mgmt** | Load Balancing | LLM Router (Gemini → Groq → Mock failover) |
| | Process Scheduling | Depth config (Quick/Medium/Deep = priority levels) |
| | Process Migration | Transparent failover from Gemini to Groq on 503 |
| | Resource Pooling | SQLAlchemy connection pool (size=5, overflow=10) |
| | Caching | TTL-based search cache (10 min, cache-aside pattern) |
| **Consistency** | Strong Consistency | PostgreSQL ACID transactions |
| | Eventual Consistency | ChromaDB embedding index lag |
| | Weak Consistency | LLM routing (different models = different outputs) |
| | CAP Theorem | PostgreSQL=CP, ChromaDB=AP, LLM Router=AP |
| | Replication | Heterogeneous: PostgreSQL (full) + ChromaDB (derived) |
| | Fault Tolerance | Triple failover, exponential backoff, graceful degradation |
| **Distributed Storage** | Block/Chunk Allocation | SemanticChunker (heading → paragraph splitting) |
| | Metadata Management | Chunk metadata (topic, section, timestamp, depth) |
| | GFS/HDFS Analog | ChromaDB chunks with metadata ≈ DataNode blocks with NameNode |
| | Data Access Patterns | Write-once, read-many (WORM) for research reports |
| | Similarity Search | ANN (Approximate Nearest Neighbor) via cosine distance |

---

## Files Changed

### New Files (9)
| File | Purpose | Distributed Concept |
|---|---|---|
| `core/citation_manager.py` | Source tracking, dedup, bibliography | Naming service, idempotent operations |
| `rag/chunker.py` | Semantic text chunking for RAG | Block allocation (GFS/HDFS) |
| `frontend/styles.py` | Dark theme CSS | — |
| `frontend/components/progress.py` | Pipeline visualization | Process monitoring |
| `frontend/components/sidebar.py` | History, settings | — |
| `frontend/components/report_viewer.py` | Report display, review, exports | — |
| `frontend/__init__.py` | Package init | — |
| `frontend/components/__init__.py` | Package init | — |

### Modified Files (13)
| File | Changes | Distributed Concept |
|---|---|---|
| `config/settings.py` | Cleaned config, added depth config | Scheduling policy |
| `database/connection.py` | Fixed connection leak, added pool | Resource pooling, health checks |
| `database/schema.py` | Added columns, indexes | Schema migration |
| `core/state.py` | New fields, Pydantic models | Shared memory IPC, serialization |
| `core/llm.py` | Model switching, rate limiting, failover | Load balancing, process migration |
| `core/prompts.py` | Rewritten for citations & batching | RPC interface contracts |
| `core/history.py` | Dedup, sources, update support | Distributed transactions, idempotency |
| `tools/search.py` | Fixed imports, caching, retry | Cache-aside pattern, fault tolerance |
| `tools/document.py` | Markdown parsing, XML escaping | — |
| `agents/base_agent.py` | Progress callback support | Message passing interface |
| `agents/planner.py` | Depth-aware, progress updates | Consensus proposer |
| `agents/researcher.py` | Batched synthesis, citation integration | Batched RPC, resource optimization |
| `agents/writer.py` | Citations, bibliography, RAG context | CQRS write model, replication |
| `agents/reviewer.py` | JSON scoring, structured output | Byzantine fault detection |
| `agents/langgraph_workflow.py` | TypedDict, error handling | DAG workflow orchestration |
| `main.py` | Complete rewrite with HITL | Coordinator, barrier sync, consensus |
| `requirements.txt` | Cleaned, added langchain-chroma | Dependency management |
