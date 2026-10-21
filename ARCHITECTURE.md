# ResearchPilot AI — System Architecture

> A distributed systems perspective on multi-agent AI research orchestration.

---

## Table of Contents

- [1. Fundamental Architecture](#1-fundamental-architecture)
  - [1.1 Architectural Style](#11-architectural-style)
  - [1.2 Multi-Tier Breakdown](#12-multi-tier-breakdown)
  - [1.3 Middleware Services](#13-middleware-services)
  - [1.4 Scalability Dimensions](#14-scalability-dimensions)
- [2. Communication Mechanisms](#2-communication-mechanisms)
  - [2.1 IPC — Inter-Process Communication](#21-ipc--inter-process-communication)
  - [2.2 RPC — Remote Procedure Calls](#22-rpc--remote-procedure-calls)
  - [2.3 RESTful Communication](#23-restful-communication)
  - [2.4 Message Passing & Callbacks](#24-message-passing--callbacks)
- [3. Synchronization & Coordination](#3-synchronization--coordination)
  - [3.1 Mutual Exclusion](#31-mutual-exclusion)
  - [3.2 Consensus Protocol (HITL)](#32-consensus-protocol-hitl)
  - [3.3 Distributed Transactions](#33-distributed-transactions)
  - [3.4 Deadlock Prevention](#34-deadlock-prevention)
  - [3.5 Barrier Synchronization](#35-barrier-synchronization)
- [4. Resource & Process Management](#4-resource--process-management)
  - [4.1 Process Scheduling](#41-process-scheduling)
  - [4.2 Load Balancing (LLM Router)](#42-load-balancing-llm-router)
  - [4.3 Process Migration](#43-process-migration)
  - [4.4 Resource Pooling & Allocation](#44-resource-pooling--allocation)
  - [4.5 Caching Strategy](#45-caching-strategy)
- [5. Consistency, Replication & Fault Tolerance](#5-consistency-replication--fault-tolerance)
  - [5.1 CAP Theorem Analysis](#51-cap-theorem-analysis)
  - [5.2 Consistency Models](#52-consistency-models)
  - [5.3 Replication Techniques](#53-replication-techniques)
  - [5.4 Fault Tolerance Mechanisms](#54-fault-tolerance-mechanisms)
- [6. Distributed Storage](#6-distributed-storage)
  - [6.1 PostgreSQL (Relational / Structured)](#61-postgresql-relational--structured)
  - [6.2 ChromaDB (Vector / Unstructured)](#62-chromadb-vector--unstructured)
  - [6.3 Comparison with GFS and HDFS](#63-comparison-with-gfs-and-hdfs)
- [7. Component Reference](#7-component-reference)

---

## 1. Fundamental Architecture

### 1.1 Architectural Style

ResearchPilot AI uses a **Pipe-and-Filter** architecture layered on top of a **Client-Server** model.

```
┌──────────────────── Pipe-and-Filter Pipeline ────────────────────┐
│                                                                   │
│  ┌────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐   │
│  │ Filter │     │ Filter  │     │  Filter  │     │  Filter  │   │
│  │   1    │────▶│    2    │────▶│    3     │────▶│    4     │   │
│  │Planner │     │Research │     │  Writer  │     │ Reviewer │   │
│  └────────┘     └─────────┘     └──────────┘     └──────────┘   │
│       │              │               │                │          │
│       ▼              ▼               ▼                ▼          │
│   AgentState     AgentState      AgentState       AgentState     │
│   (Pipe)         (Pipe)          (Pipe)           (Pipe)         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Why Pipe-and-Filter?**
- Each agent (filter) is **independently replaceable** — swap the Writer without touching the Planner.
- The data format (`AgentState`) is **uniform** across all pipes.
- The pipeline is **composable** — add a new FactChecker agent by inserting it between Writer and Reviewer.

**Alternative considered:** Blackboard Architecture (all agents read/write to a shared knowledge base). Rejected because it introduces concurrency control complexity without proportional benefit for a sequential pipeline.

### 1.2 Multi-Tier Breakdown

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Presentation Layer                             │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Streamlit Web UI                                 │  │
│  │  • Renders input forms, progress bars, reports    │  │
│  │  • Handles user interaction (HITL approval)       │  │
│  │  • Delegates ALL computation to Tier 2            │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  TIER 2: Application / Business Logic Layer             │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Agent Pipeline + Core Services                   │  │
│  │  • Planner, Researcher, Writer, Reviewer agents   │  │
│  │  • LLM Router (Gemini/Groq/Mock)                 │  │
│  │  • CitationManager, SemanticChunker               │  │
│  │  • Search & Browsing Tools                        │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  TIER 3: Data / Persistence Layer                       │
│  ┌─────────────────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL (RDBMS)  │  │  ChromaDB (Vector DB)    │  │
│  │  • ACID compliant   │  │  • ANN similarity search │  │
│  │  • Structured data  │  │  • Embedding storage     │  │
│  └─────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Middleware Services

Middleware in ResearchPilot AI provides **transparent services** that the agents use without needing to understand the underlying complexity.

| Middleware | Component | Service Provided |
|---|---|---|
| **ORM Middleware** | SQLAlchemy | Translates Python objects to SQL. Agents call `save_history()` without writing SQL. |
| **Embedding Middleware** | LangChain + HuggingFace | Agents call `store_research()` without knowing about tensor operations or vector math. |
| **Serialization Middleware** | Pydantic (`AgentState`) | Automatically validates, serializes, and deserializes complex nested state between agents. |
| **Retry Middleware** | `core/llm.py` | Transparently retries failed API calls with exponential backoff. The calling agent is unaware of retries. |
| **Connection Pool Middleware** | SQLAlchemy Pool | Manages a pool of reusable DB connections. Agents get a connection without managing lifecycle. |

### 1.4 Scalability Dimensions

```
                    Vertical Scaling (Scale Up)
                    │
                    │  • Bigger machine
                    │  • More RAM for larger context windows
                    │  • Faster GPU for local embeddings
                    │
                    ▼
 ───────────────────┼───────────────────▶ Horizontal Scaling (Scale Out)
                    │
                    │                   • Multiple FastAPI workers
                    │                   • Celery task queue
                    │                   • PostgreSQL read replicas
                    │                   • ChromaDB sharding
                    │
                    │  Functional Scaling (Decomposition)
                    ▼
                       • Each agent as a separate microservice
                       • Independent deployment and scaling
                       • Agent-specific resource allocation
```

**Current State:** Single-node vertical scaling.
**Target State:** Horizontal scaling with functional decomposition (see Scalability section in README).

---

## 2. Communication Mechanisms

### 2.1 IPC — Inter-Process Communication

Agents communicate using **shared-memory IPC** through the `AgentState` object.

```
┌──────────────────────────────────────────────────────────┐
│                    Shared Memory: AgentState              │
│                                                          │
│  {                                                       │
│    topic:    "Kubernetes vs Docker"     ← Set by UI      │
│    plan:     ["Q1", "Q2", "Q3"]         ← Set by Planner │
│    findings: [{question, content}]      ← Set by Research│
│    sources:  [{url, title, ref_num}]    ← Set by Research│
│    draft:    "# Report\n..."            ← Set by Writer  │
│    review:   {score: 8.2, ...}          ← Set by Reviewer│
│  }                                                       │
└──────────────────────────────────────────────────────────┘
        ▲           ▲           ▲            ▲
        │           │           │            │
    Planner    Researcher    Writer      Reviewer
    (write)    (read+write)  (read+write) (read+write)
```

**Key Properties:**
- **Zero-copy**: All agents operate on the same in-memory object (no serialization between stages)
- **Sequential access**: Only one agent writes at a time → no race conditions
- **Implicit ordering**: The pipeline enforces a happens-before relationship

### 2.2 RPC — Remote Procedure Calls

Every LLM API call follows the RPC paradigm:

```
  Client (ResearchPilot)                    Server (Gemini API)
  ┌──────────────────┐                     ┌──────────────────┐
  │                  │   1. Marshal        │                  │
  │  agent.run()     │──────────────────▶  │  /generateContent│
  │                  │   (JSON payload)    │                  │
  │                  │                     │  Process prompt   │
  │                  │   2. Response       │  Generate tokens  │
  │  Parse JSON      │◀──────────────────  │  Return response  │
  │  Update state    │   (JSON response)   │                  │
  └──────────────────┘                     └──────────────────┘
                         HTTPS / TLS
                      (Transport Layer)
```

**RPC characteristics demonstrated:**
- **Synchronous blocking**: The caller blocks until the remote LLM returns
- **Marshalling/Unmarshalling**: Prompt → JSON → HTTP body → JSON → parsed response
- **Transparency**: The `get_llm_client()` abstraction hides whether Gemini, Groq, or Mock is handling the call
- **Failure semantics**: At-most-once with retry (idempotent since LLM calls are stateless)

### 2.3 RESTful Communication

| Endpoint | Method | Component | Description |
|---|---|---|---|
| `googleapis.com/v1beta/models/*:generateContent` | `POST` | LLM Router | Send prompt, receive generation |
| `api.groq.com/openai/v1/chat/completions` | `POST` | LLM Fallback | OpenAI-compatible chat endpoint |
| `duckduckgo.com` (via `ddgs`) | `GET` | Search Tool | Query → search results (title, link, snippet) |
| `*` (any URL) | `GET` | Web Scraper | Fetch page HTML for content extraction |

**REST principles applied:**
- **Stateless**: Each API call contains all necessary context (no server-side session)
- **Uniform interface**: All LLM providers are accessed through a common `generate()` interface
- **Resource-based**: URLs identify resources (models, search results, web pages)

### 2.4 Message Passing & Callbacks

The `progress_callback` mechanism implements **asynchronous message passing**:

```
  Producer (Agent)                    Consumer (Streamlit UI)
  ┌──────────────────┐               ┌──────────────────┐
  │                  │               │                  │
  │  for q in plan:  │   callback()  │  st.progress()   │
  │    search(q)     │──────────────▶│  st.status()     │
  │    browse(url)   │   callback()  │  st.expander()   │
  │                  │──────────────▶│                  │
  │  synthesize()    │   callback()  │                  │
  │                  │──────────────▶│                  │
  └──────────────────┘               └──────────────────┘
```

**Properties:**
- **Loose coupling**: The agent does not import or depend on Streamlit
- **One-directional**: Agent → UI only (no back-pressure from UI to agent)
- **Fire-and-forget**: Callback returns immediately; agent does not wait for UI to render

---

## 3. Synchronization & Coordination

### 3.1 Mutual Exclusion

**Problem:** If two concurrent requests try to initialize the ChromaDB client or load the embedding model simultaneously, they could corrupt shared state.

**Solution:** The **Singleton pattern** acts as a mutual exclusion lock on resource initialization.

```python
# rag/vectorstore.py — Singleton Pattern (Mutex analog)

_embeddings = None    # Shared resource (critical section)
_vectorstore = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:          # Check (like try_lock)
        _embeddings = HuggingFace()  # Initialize (critical section)
    return _embeddings               # Return shared instance
```

**Distributed systems analog:** This is equivalent to a **test-and-set lock** — the first caller initializes the resource, and all subsequent callers reuse it.

### 3.2 Consensus Protocol (HITL)

The Human-in-the-Loop plan approval is a **single-proposer consensus protocol**:

```
  Proposer (Planner Agent)         Acceptor (Human User)
  ┌──────────────────────┐        ┌──────────────────────┐
  │                      │        │                      │
  │  1. Generate plan    │        │                      │
  │     ["Q1","Q2","Q3"] │        │                      │
  │                      │  PROPOSE│                      │
  │  2. Send to UI       │───────▶│  3. Review questions │
  │                      │        │     Edit/Add/Remove  │
  │                      │        │                      │
  │                      │  ACCEPT │  4a. Click "Approve" │
  │  5. Continue pipeline│◀───────│     (Consensus!)     │
  │                      │        │                      │
  │          OR          │  REJECT │  4b. Click "Regen"   │
  │  5. Re-propose       │◀───────│     (No consensus)   │
  │                      │        │                      │
  └──────────────────────┘        └──────────────────────┘
```

**Mapping to Paxos/Raft:**
- **Proposer** = Planner Agent (proposes a plan)
- **Acceptor** = Human User (single-node quorum)
- **Majority** = Trivially satisfied (quorum size = 1)
- **Value** = The final approved list of research questions
- **Guarantee**: No research proceeds without consensus (safety property)

### 3.3 Distributed Transactions

Saving a completed research session involves writing to **two independent data stores**. We use a simplified **Two-Phase Commit (2PC)** pattern:

```
  Coordinator (main.py)
  ┌──────────────────────┐
  │                      │
  │  Phase 1: PREPARE    │
  │  ┌─────────────────┐ │
  │  │ Validate state: │ │
  │  │ • draft exists? │ │
  │  │ • sources valid? │ │
  │  │ • review parsed? │ │
  │  └─────────────────┘ │
  │                      │
  │  Phase 2: COMMIT     │
  │  ┌────────┐ ┌──────┐ │
  │  │Postgres│ │Chroma│ │
  │  │ save() │ │store()│ │
  │  └────────┘ └──────┘ │
  │                      │
  │  If Postgres fails:  │
  │    → Rollback        │
  │    → Skip Chroma     │
  │  If Chroma fails:    │
  │    → Log warning     │
  │    → Postgres stands │
  │    (best-effort)     │
  └──────────────────────┘
```

**Trade-off:** We use a **best-effort 2PC** rather than strict 2PC. PostgreSQL is the source of truth; ChromaDB failure is tolerated (eventual re-indexing on next access).

### 3.4 Deadlock Prevention

The pipeline is structured as a **Directed Acyclic Graph (DAG)**:

```
  Planner ──▶ HITL ──▶ Researcher ──▶ Writer ──▶ Reviewer
                                        │
                                        ▼
                                     ChromaDB
                                    (store only)
```

**Deadlock prevention strategy: Resource Ordering**
- Agents are assigned a strict total order: Planner(1) < Researcher(2) < Writer(3) < Reviewer(4)
- An agent can only request resources from agents with a **higher** order number
- No agent ever waits for one with a lower order → **cycles are impossible** → **deadlock-free by construction**

### 3.5 Barrier Synchronization

Each agent transition acts as a **barrier**:

```
  ──── Planner ────│BARRIER│──── Researcher ────│BARRIER│──── Writer ────
                   │       │                    │       │
                   │ Wait  │                    │ Wait  │
                   │ until │                    │ until │
                   │ plan  │                    │findings│
                   │ ready │                    │ ready │
```

The Writer **cannot begin** until the Researcher has completed and populated `state.findings`. This is enforced by the sequential execution in `main.py` — a structural barrier rather than an explicit synchronization primitive.

---

## 4. Resource & Process Management

### 4.1 Process Scheduling

Research depth acts as a **scheduling policy** that controls resource allocation:

```
┌──────────────┬───────────────┬───────────────┬──────────────────┐
│   Depth      │   Questions   │  Search/Q     │  Browse Pages/Q  │
├──────────────┼───────────────┼───────────────┼──────────────────┤
│ ⚡ Quick      │      3        │      3        │       1          │
│ 📊 Medium    │      5        │      5        │       2          │
│ 🔬 Deep      │      8        │      8        │       3          │
└──────────────┴───────────────┴───────────────┴──────────────────┘
```

**Scheduling analogy:**
- **Quick** = High-priority, short job (Round Robin with small time quantum)
- **Medium** = Standard priority (Fair-share scheduling)
- **Deep** = Low-priority, long job (Batch scheduling, more resources allocated)

### 4.2 Load Balancing (LLM Router)

The LLM Router implements a **weighted failover load balancer** with health checks:

```
                    ┌─────────────────────┐
                    │   LLM Router        │
                    │   (core/llm.py)     │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │  Gemini    │  │   Groq     │  │   Mock     │
       │  Flash     │  │  LLaMA 3   │  │  (Local)   │
       │            │  │            │  │            │
       │ Priority:1 │  │ Priority:2 │  │ Priority:3 │
       │ Weight:70% │  │ Weight:25% │  │ Weight:5%  │
       │            │  │            │  │            │
       │ Health:    │  │ Health:    │  │ Health:    │
       │ HTTP 200?  │  │ HTTP 200?  │  │ Always OK  │
       └────────────┘  └────────────┘  └────────────┘
```

**Load balancing algorithm:**
1. Try Gemini (primary) → if 200 OK, return response
2. If 503/429 (overloaded/rate-limited) → retry with exponential backoff (up to 3 times)
3. If all retries fail → **failover** to Groq (secondary)
4. If Groq fails → **failover** to Mock (guaranteed availability)

**Distributed systems mapping:**
- This is a **Layer 7 (Application) Load Balancer** — it understands HTTP status codes
- Uses **Active-Passive** failover (Gemini active, Groq passive standby)
- Health check = HTTP response status code analysis

### 4.3 Process Migration

When a Gemini API call returns a `503 Service Unavailable`, the system performs **transparent process migration**:

```
  ┌─────────────────────────────────────────────────────┐
  │  Before Migration:                                  │
  │                                                     │
  │  Agent ──▶ Gemini (503 Overloaded!)                │
  │                                                     │
  │  Migration Event:                                   │
  │  1. Catch 503/429 exception                         │
  │  2. Log: "Gemini failed, trying Groq"              │
  │  3. Re-serialize prompt for Groq format             │
  │  4. Send to Groq endpoint                           │
  │                                                     │
  │  After Migration:                                   │
  │                                                     │
  │  Agent ──▶ Groq (200 OK) ✓                         │
  │                                                     │
  │  Key: The calling agent is UNAWARE of the migration │
  └─────────────────────────────────────────────────────┘
```

**Properties:**
- **Transparency**: The agent's `run()` method receives a response without knowing which backend served it
- **Stateless migration**: Since each LLM call is independent (stateless RPC), migration requires no state transfer
- **Non-preemptive**: Migration happens only on failure, not proactively

### 4.4 Resource Pooling & Allocation

```
┌──────────────────────────────────────────┐
│         SQLAlchemy Connection Pool        │
│                                          │
│  Pool Size:      5 connections           │
│  Max Overflow:   10 connections          │
│  Pool Pre-Ping:  True (health check)     │
│  Pool Recycle:   1800s (30 min TTL)      │
│                                          │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐│
│  │Conn1│ │Conn2│ │Conn3│ │Conn4│ │Conn5││
│  │ BUSY│ │ IDLE│ │ IDLE│ │ BUSY│ │ IDLE││
│  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘│
│                                          │
│  Request → Check out idle conn           │
│  Complete → Return conn to pool          │
│  All busy → Create overflow (up to 10)   │
│  Overflow + all busy → Block/wait        │
└──────────────────────────────────────────┘
```

### 4.5 Caching Strategy

```
┌──────────────────────────────────────────────────┐
│               Cache-Aside Pattern                │
│                                                  │
│   1. Agent requests search("kubernetes")         │
│                                                  │
│   2. Check cache:                                │
│      cache_key = hash("kubernetes")              │
│      if key in cache AND age < 10 min:           │
│          return cache[key]   ← CACHE HIT         │
│                                                  │
│   3. Cache miss:                                 │
│      result = duckduckgo_search("kubernetes")    │
│      cache[key] = (result, timestamp)            │
│      return result           ← CACHE MISS        │
│                                                  │
│   Eviction: TTL-based (10 minute expiry)         │
│   Pattern:  Cache-Aside (Lazy Population)        │
└──────────────────────────────────────────────────┘
```

---

## 5. Consistency, Replication & Fault Tolerance

### 5.1 CAP Theorem Analysis

```
                        C (Consistency)
                           ╱╲
                          ╱  ╲
                         ╱    ╲
                        ╱ POST ╲
                       ╱ GRESQL ╲
                      ╱   (CP)   ╲
                     ╱            ╲
                    ╱              ╲
                   ╱    ChromaDB    ╲
                  ╱       (AP)      ╲
                 ╱                   ╲
                ╱                     ╲
               ╱━━━━━━━━━━━━━━━━━━━━━━╲
         A (Availability)        P (Partition Tolerance)
```

| Component | Choice | Sacrifice | Justification |
|---|---|---|---|
| **PostgreSQL** | **CP** | Availability (brief downtime on failover) | Research records must be accurate and durable. A user must never see stale or corrupted history. |
| **ChromaDB** | **AP** | Consistency (slight embedding indexing lag) | RAG should always return results. Slightly stale context is acceptable — missing one past report from retrieval is a minor quality degradation, not a correctness error. |
| **LLM Router** | **AP** | Consistency (different models = different output quality) | The system must always produce a response. A Groq response may differ from a Gemini response, but producing *something* is better than returning an error. |
| **Search Cache** | **AP** | Consistency (results may be up to 10 min stale) | Availability matters. Returning cached results is better than failing because DuckDuckGo rate-limited us. |

### 5.2 Consistency Models

| Model | Where Applied | Behavior |
|---|---|---|
| **Strong Consistency** | PostgreSQL writes | After `save_history()` returns, the record is immediately visible to ALL subsequent `load_history()` calls. Guaranteed by ACID transactions with `SERIALIZABLE` isolation. |
| **Eventual Consistency** | ChromaDB writes | After `store_research()` returns, the new embeddings may NOT be immediately visible in `retrieve_context()`. The indexing process introduces a brief lag. The system will converge to consistency. |
| **Weak Consistency** | LLM Routing | There is no guarantee that the same prompt produces the same response. Different models (Gemini vs Groq) produce different outputs. Even the same model may produce different results due to temperature sampling. |
| **Read-Your-Writes** | PostgreSQL | The session that wrote a record will always see it immediately. Other sessions may experience a brief delay on read replicas (future scaled architecture). |

### 5.3 Replication Techniques

```
┌──────────────────────────────────────────────────────────────┐
│            Heterogeneous Replication                         │
│                                                              │
│  Source of Truth: PostgreSQL                                 │
│  Replica:         ChromaDB (derived, partial)                │
│                                                              │
│  ┌─────────────┐                    ┌─────────────┐          │
│  │ PostgreSQL  │                    │  ChromaDB   │          │
│  │             │                    │             │          │
│  │ Full record:│   ──Replicate──▶   │ Partial:    │          │
│  │ • topic     │   (semantic        │ • chunks    │          │
│  │ • draft     │    chunking +      │ • embeddings│          │
│  │ • sources   │    embedding)      │ • metadata  │          │
│  │ • review    │                    │             │          │
│  │ • metadata  │                    │ (No sources,│          │
│  │             │                    │  no review) │          │
│  └─────────────┘                    └─────────────┘          │
│                                                              │
│  This is NOT traditional leader-follower replication.        │
│  It is a CQRS pattern:                                       │
│  • PostgreSQL = Write model (full, authoritative)            │
│  • ChromaDB   = Read model (derived, optimized for queries)  │
└──────────────────────────────────────────────────────────────┘
```

### 5.4 Fault Tolerance Mechanisms

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fault Tolerance Hierarchy                     │
│                                                                 │
│  Level 1: Retry with Exponential Backoff                        │
│  ┌────────────────────────────────────────────────────┐         │
│  │  Attempt 1 → Wait 1s → Attempt 2 → Wait 2s →     │         │
│  │  Attempt 3 → Wait 4s → Give up on this provider   │         │
│  └────────────────────────────────────────────────────┘         │
│                          │ (All retries failed)                 │
│                          ▼                                      │
│  Level 2: Provider Failover (Process Migration)                 │
│  ┌────────────────────────────────────────────────────┐         │
│  │  Gemini failed → Try Groq                          │         │
│  │  Groq failed   → Try Mock                          │         │
│  └────────────────────────────────────────────────────┘         │
│                          │ (All providers failed)               │
│                          ▼                                      │
│  Level 3: Graceful Degradation                                  │
│  ┌────────────────────────────────────────────────────┐         │
│  │  Mock mode: Return template response                │         │
│  │  System continues with reduced quality               │         │
│  │  User is informed of degraded state                  │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                 │
│  Analogy: Triple Modular Redundancy (TMR)                       │
│  Like airplane flight computers: 3 independent systems,         │
│  output is used from whichever one responds successfully.       │
└─────────────────────────────────────────────────────────────────┘
```

**Failure scenarios handled:**

| Failure | Detection | Recovery | Downtime |
|---|---|---|---|
| Gemini API rate limit (429) | HTTP status code | Exponential backoff retry | 1-7 seconds |
| Gemini API unavailable (503) | HTTP status code | Failover to Groq | ~500ms |
| Groq API failure | Exception catch | Failover to Mock | ~100ms |
| PostgreSQL connection drop | `pool_pre_ping=True` | Auto-reconnect from pool | ~200ms |
| Web search failure | Exception catch | Return empty results, continue | 0ms (degraded) |
| ChromaDB unavailable | Exception catch | Skip RAG context, continue | 0ms (degraded) |

---

## 6. Distributed Storage

### 6.1 PostgreSQL (Relational / Structured)

```
┌────────────────────────────────────────────────┐
│              researches (table)                 │
├──────────────┬──────────┬───────────────────────┤
│  Column      │  Type    │  Purpose              │
├──────────────┼──────────┼───────────────────────┤
│  id          │  SERIAL  │  Primary key          │
│  topic       │  TEXT    │  Research topic        │
│  goals       │  TEXT    │  User goals            │
│  depth       │  VARCHAR │  Quick/Medium/Deep     │
│  plan        │  JSON    │  Research questions    │
│  findings    │  JSON    │  Agent findings        │
│  sources     │  JSON    │  Tracked citations     │
│  draft       │  TEXT    │  Final report          │
│  review      │  JSON    │  Reviewer scores       │
│  created_at  │  TIMESTAMP│ Creation time         │
│  updated_at  │  TIMESTAMP│ Last modification     │
├──────────────┴──────────┴───────────────────────┤
│  Indexes: topic, created_at, depth              │
│  Constraints: topic NOT NULL                    │
│  Transactions: ACID (Read Committed isolation)  │
└─────────────────────────────────────────────────┘
```

### 6.2 ChromaDB (Vector / Unstructured)

```
┌────────────────────────────────────────────────────────┐
│              ChromaDB Collection: research_memory       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Document Storage:                                     │
│  ┌──────────────────────────────────────────────┐      │
│  │  Chunk: "Kubernetes uses etcd for..."        │      │
│  │  Embedding: [0.023, -0.441, 0.891, ...]      │      │
│  │  Metadata: {                                  │      │
│  │    topic: "Kubernetes",                       │      │
│  │    section: "Architecture",                   │      │
│  │    depth: "Deep",                             │      │
│  │    timestamp: "2025-07-27T..."                │      │
│  │  }                                            │      │
│  └──────────────────────────────────────────────┘      │
│                                                        │
│  Query: similarity_search_with_score("container")      │
│  → Returns top-k chunks sorted by cosine distance      │
│  → Filtered by distance threshold (relevance)          │
│                                                        │
│  Embedding Model: all-MiniLM-L6-v2 (384 dimensions)   │
│  Distance Metric: Cosine similarity                    │
│  Persistence: Local filesystem (./chroma_db/)          │
└────────────────────────────────────────────────────────┘
```

### 6.3 Comparison with GFS and HDFS

| Feature | GFS / HDFS | ResearchPilot Storage |
|---|---|---|
| **Chunking** | Fixed-size blocks (64MB GFS, 128MB HDFS) | Semantic chunks (variable-size, split by headings/paragraphs, ~500 chars target) |
| **Master / NameNode** | Central metadata server tracks chunk locations | PostgreSQL acts as the metadata store (topic, timestamp, depth) |
| **ChunkServers / DataNodes** | Distributed nodes storing actual data blocks | ChromaDB stores actual embeddings + text chunks |
| **Replication Factor** | 3x replication across nodes | Heterogeneous: PostgreSQL (full record) + ChromaDB (derived chunks) |
| **Write Pattern** | Append-only (WORM) | Write-once after research completes, then read-many for RAG retrieval |
| **Read Pattern** | Sequential reads of large files | Similarity-based random access (ANN search by embedding distance) |
| **Fault Detection** | Heartbeat between Master and ChunkServers | `pool_pre_ping` for PostgreSQL, exception handling for ChromaDB |
| **Consistency** | GFS: relaxed; HDFS: strong within pipeline | PostgreSQL: strong; ChromaDB: eventual |

---

## 7. Component Reference

| File | Component | Distributed Systems Concept |
|---|---|---|
| `main.py` | Orchestrator | Coordinator in 2PC, Barrier synchronization |
| `agents/planner.py` | Planner Agent | Filter in pipe-and-filter, Proposer in consensus |
| `agents/researcher.py` | Researcher Agent | Filter, RPC client, batched processing |
| `agents/writer.py` | Writer Agent | Filter, CQRS write model, replication trigger |
| `agents/reviewer.py` | Reviewer Agent | Filter, LLM-as-a-Judge (Byzantine fault detector) |
| `core/llm.py` | LLM Router | L7 load balancer, failover, process migration |
| `core/state.py` | AgentState | Shared memory IPC, Pydantic serialization |
| `core/citation_manager.py` | Citation Manager | Reference tracking, deduplication |
| `core/prompts.py` | Prompt Templates | RPC message templates (marshalling) |
| `core/history.py` | History Manager | Transaction coordinator, duplicate detection |
| `rag/vectorstore.py` | Vector Store | AP system, eventual consistency, singleton mutex |
| `rag/chunker.py` | Semantic Chunker | Block allocator (GFS/HDFS analog) |
| `tools/search.py` | Search Tool | REST client, cache-aside pattern |
| `database/connection.py` | DB Connection | Connection pool, resource manager, health checks |
| `database/schema.py` | DB Schema | Data definition, schema migration |
| `config/settings.py` | Settings | Scheduling policy configuration |
