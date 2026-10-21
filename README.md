# ResearchPilot AI

<p align="center">
  <b>A Distributed Multi-Agent AI Research Assistant</b>
  <br/>
  <i>Engineered with Multi-Agent Orchestration • Distributed Computing Patterns • RAG • LLM-as-a-Judge</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/gRPC-v1.83-244c5a.svg?logo=grpc&logoColor=white" alt="gRPC"/>
  <img src="https://img.shields.io/badge/Kubernetes-Minikube-326CE5.svg?logo=kubernetes&logoColor=white" alt="Kubernetes"/>
  <img src="https://img.shields.io/badge/Redis-Cache--Aside-DC382D.svg?logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Gemini_2.5-Flash-4285F4.svg?logo=google&logoColor=white" alt="Gemini"/>
</p>

---

## 📑 Table of Contents

- [Overview & Motivation](#overview--motivation)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
  - [High-Level Architectural Workflow](#high-level-architectural-workflow)
  - [Multi-Agent Pipeline & Batched Synthesis](#multi-agent-pipeline--batched-synthesis)
  - [Data Flow & Semantic RAG](#data-flow--semantic-rag)
- [Distributed Systems Infrastructure (`grpc_experiment`)](#distributed-systems-infrastructure-grpc_experiment)
  - [1. Communication: gRPC & Protocol Buffers](#1-communication-grpc--protocol-buffers)
  - [2. Synchronization: Lamport Logical Clocks](#2-synchronization-lamport-logical-clocks)
  - [3. Concurrency: Ricart-Agrawala Mutual Exclusion](#3-concurrency-ricart-agrawala-mutual-exclusion)
  - [4. Deadlock Detection: Centralized Wait-For Graph (WFG)](#4-deadlock-detection-centralized-wait-for-graph-wfg)
  - [5. Load Balancing: Least-Connections Dispatcher](#5-load-balancing-least-connections-dispatcher)
  - [6. Replication & Consistency: Gossip Protocol + Last-Write-Wins (LWW)](#6-replication--consistency-gossip-protocol--last-write-wins-lww)
  - [7. Caching & Resiliency: Redis Cache-Aside with Stale Fallback](#7-caching--resiliency-redis-cache-aside-with-stale-fallback)
  - [8. Consensus: Raft Leader Election & Heartbeats](#8-consensus-raft-leader-election--heartbeats)
  - [9. Orchestration: Kubernetes (Minikube) & Headless gRPC Balancing](#9-orchestration-kubernetes-minikube--headless-grpc-balancing)
  - [10. Storage: ResearchDFS (Chunking, Cryptographic Integrity & Auto-Repair)](#10-storage-researchdfs-chunking-cryptographic-integrity--auto-repair)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Installation & Getting Started](#installation--getting-started)
- [Running Distributed Computing Modules](#running-distributed-computing-modules)
- [Scalability & CAP Theorem Analysis](#scalability--cap-theorem-analysis)
- [Walkthrough Guides & Documentation](#walkthrough-guides--documentation)
- [License](#license)

---

## 💡 Overview & Motivation

Modern generative AI applications and research platforms require compute-intensive pipelines: automated web crawling, multi-source scraping, LLM-based reasoning, dense vector retrieval (RAG), and artifact generation. 

Traditional research tools are monolithic, synchronous, and vulnerable to single-point-of-failure (SPOF) outages, rate-limit starvation, and uncoordinated state corruption.

**ResearchPilot AI** addresses these challenges by merging an **intelligent multi-agent research workflow** with **resilient distributed computing engineering**. Beyond acting as an autonomous research assistant, it serves as a production-grade testbed implementing core distributed systems paradigms:
- **Resilient Microservices:** Replacing slow HTTP/REST calls with binary **gRPC** interfaces and **HTTP/2 multiplexing**.
- **Edge Caching & Graceful Degradation:** Shielding third-party LLM APIs with a **Redis Cache-Aside Gateway** that serves stale snapshots during backend downtime.
- **Consensus & Self-Healing:** Utilizing **Raft consensus** for automatic leader election and **Kubernetes** headless deployments for container-level failover.
- **Chunked Distributed Storage:** Managing research papers and synthesized dossiers through **ResearchDFS**—a GFS/HDFS-inspired distributed file store with 64 KB block chunking, dual replication ($RF=2$), SHA-256 validation, and auto-repair.

---

## ✨ Key Features

- 🤖 **Autonomous Multi-Agent Collaboration:** Dedicated agents for Planning, Web Researching, Report Writing, and Reviewing.
- ⚡ **Batched LLM Synthesis (60–70% API Call Reduction):** Gathers all research findings concurrently over HTTP before executing batched LLM synthesis in a single unified prompt.
- 🛡️ **Human-in-the-Loop (HITL) Consensus:** Interactive review interface allowing users to adjust or approve research plans prior to execution.
- 📚 **RAG Long-Term Memory:** ChromaDB vector database with semantic chunking to recall past research context across sessions.
- 🎯 **LLM-as-a-Judge Evaluation:** Automated Reviewer agent assessing generated reports on depth, accuracy, clarity, and structural rigor.
- 🌐 **Polyglot Fallback Routing:** Automatic failover across Google Gemini 2.5 Flash, Groq LLaMA 3.3 70B, and offline Mock modes.
- 📦 **Enterprise Distributed Infrastructure:** 10 fully verified distributed computing modules covering gRPC, Lamport Clocks, Mutual Exclusion, Deadlocks, Load Balancing, Gossip Replication, Redis Caching, Raft Consensus, Kubernetes, and Distributed File Systems.

---

## 🏗️ System Architecture

### High-Level Architectural Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                               │
│                                                                          │
│   ┌──────────────────────────────┐        ┌──────────────────────────┐   │
│   │     Streamlit Web UI         │        │    gRPC CLI Clients      │   │
│   │   (Interactive Research)     │        │  (dfs_client / load_test)│   │
│   └──────────────┬───────────────┘        └────────────┬─────────────┘   │
└──────────────────┼─────────────────────────────────────┼─────────────────┘
                   │ HTTP / REST                         │ gRPC (HTTP/2)
                   ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   EDGE RESILIENCY & LOAD BALANCING                       │
│                                                                          │
│   ┌──────────────────────────────┐        ┌──────────────────────────┐   │
│   │     Redis Cache Gateway      │        │ Least-Connections Router │   │
│   │  (Fresh TTL / Stale Backup)  │        │ (Active Conns Dispatch)  │   │
│   └──────────────┬───────────────┘        └────────────┬─────────────┘   │
└──────────────────┼─────────────────────────────────────┼─────────────────┘
                   │ RPC Routing                         │ gRPC Dispatches
                   ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│               DISTRIBUTED COMPUTE CLUSTER (Kubernetes / Minikube)        │
│                                                                          │
│   Headless Service: worker-svc (clusterIP: None | DNS Round-Robin)       │
│   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐ │
│   │  Worker Pod 1      │  │  Worker Pod 2      │  │  Worker Pod 3      │ │
│   │  (Planner/Worker)  │  │  (Planner/Worker)  │  │  (Planner/Worker)  │ │
│   └────────────────────┘  └────────────────────┘  └────────────────────┘ │
└──────────────────┬─────────────────────────────────────┬─────────────────┘
                   │ State & Coordination                │ Block I/O (64 KB)
                   ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                 COORDINATION & DISTRIBUTED STORAGE (ResearchDFS)         │
│                                                                          │
│   ┌──────────────────────────────┐        ┌──────────────────────────┐   │
│   │   Metadata Coordinator       │        │   3x Storage Nodes       │   │
│   │   - Lamport Clock Versioning │        │   - Dual Replicas (RF=2) │   │
│   │   - Raft Consensus Election  │        │   - SHA-256 Verification │   │
│   │   - WFG Deadlock Detection   │        │   - Auto-Repair Daemon   │   │
│   └──────────────────────────────┘        └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Multi-Agent Pipeline & Batched Synthesis

```
User Topic ──▶ [Planner Agent] ──▶ [HITL Approval] ──▶ [Researcher Agent]
               (Gemini Flash-Lite) (User Edits/OK)    (Web Search & Scrape)
                                                                │
                                                                ▼
Final Report ◀── [Reviewer Agent] ◀── [Writer Agent] ◀── Batched Synthesis
(Scored 1-10)     (LLM-as-a-Judge)     (RAG + Citations) (Single LLM Call)
```

1. **Planner Agent:** Deconstructs the research topic into 3–5 targeted research questions.
2. **Human-in-the-Loop (HITL):** Allows user inspection, editing, and approval before network calls occur.
3. **Researcher Agent:** Performs web searches and page browsing via HTTP; aggregates all findings into a structured prompt for a single batched synthesis LLM call.
4. **Writer Agent:** Ingests previous research context from ChromaDB (RAG), maps findings with strict academic citations `[1]`, and produces Markdown, PDF, and DOCX reports.
5. **Reviewer Agent:** Acts as an LLM judge, grading the draft on technical depth, factual precision, clarity, and bibliography adherence.

### Data Flow & Semantic RAG

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌───────────────┐
│ Search Results │────▶│  CitationMgr   │────▶│  Writer Agent  │────▶│ Report Output │
│  (DuckDuckGo)  │     │ (Dedup / Refs) │     │ (Inline Citns) │     │  (+ Sources)  │
└────────────────┘     └────────────────┘     └────────┬───────┘     └───────────────┘
                                                       │
                                            ┌──────────▼──────────┐
                                            │   SemanticChunker   │
                                            │  (Header/Paragraph) │
                                            └──────────┬──────────┘
                                                       │
                                            ┌──────────▼──────────┐
                                            │      ChromaDB       │
                                            │ (Vector Embeddings) │
                                            └─────────────────────┘
```

---

## 🔬 Distributed Systems Infrastructure (`grpc_experiment`)

The `grpc_experiment/` directory houses standalone distributed computing implementations tested and verified for fault tolerance, consistency, and scalability:

| # | Module / Concept | Primary File(s) | Key Theoretical Concept |
|:---:|---|---|---|
| **1** | **gRPC & Protobuf** | `proto/research.proto`, `planner_server.py`, `planner_client.py` | Binary IPC, IDL interface contract, HTTP/2 multiplexing |
| **2** | **Lamport Clocks** | `lamport_clock.py`, `lamport_server.py`, `lamport_client.py` | Causal event ordering, logical timestamps ($L = \max(L, L_{recv}) + 1$) |
| **3** | **Mutual Exclusion** | `node.py`, `proto/research.proto` (`MutexService`) | Ricart-Agrawala peer-to-peer distributed lock coordination |
| **4** | **Deadlock Detection** | `lock_manager.py`, `worker.py` | Centralized Wait-For Graph (WFG), cycle detection, victim preemption |
| **5** | **Load Balancing** | `load_balancer.py`, `worker_server.py` | Layer 7 Least-Connections dynamic request forwarding |
| **6** | **Consistency (Gossip)**| `replica_node.py`, `replica_client.py` | Eventual consistency, asynchronous gossip, Last-Write-Wins (LWW) |
| **7** | **Redis Caching** | `cache_gateway.py` | Cache-Aside pattern, TTL eviction, stale-cache fallback during outages |
| **8** | **Raft Consensus** | `raft_node.py` | Leader Election, Candidate voting quorums ($N/2 + 1$), Heartbeats |
| **9** | **Kubernetes** | `Dockerfile`, `k8s/app.yaml`, `load_test.py` | Containerization, Headless Services (`clusterIP: None`), Self-healing |
| **10**| **Distributed Storage** | `dfs_metadata.py`, `dfs_storage.py`, `dfs_client.py`, `dfs_repair.py` | GFS chunking (64 KB), dual replication ($RF=2$), SHA-256 checks, auto-repair |

### 1. Communication: gRPC & Protocol Buffers
- Replaces high-overhead JSON APIs with compact, binary Protocol Buffers (`proto3`).
- Generates strongly typed client stubs and server servicers. Reduces inter-service serialization overhead by >60%.

### 2. Synchronization: Lamport Logical Clocks
- Assigns monotonically increasing integer counters to distributed planning requests and document revisions.
- Resolves causal precedence across asynchronous nodes without physical NTP clock synchronization.

### 3. Concurrency: Ricart-Agrawala Mutual Exclusion
- Fully decentralized peer-to-peer coordination algorithm requiring $2(N-1)$ messages per critical section entry.
- Prevents concurrent write collisions when multiple worker nodes update shared vector indexes.

### 4. Deadlock Detection: Centralized Wait-For Graph (WFG)
- Monitors resource allocations and pending lock requests.
- Executes cycle detection via Depth-First Search (DFS). When a deadlock cycle occurs, it automatically aborts the youngest transaction to release held locks.

### 5. Load Balancing: Least-Connections Dispatcher
- Real-time connection tracker maintaining an active task registry across worker nodes.
- Dispatches intensive research tasks to the worker with the lowest active load, avoiding thread starvation.

### 6. Replication & Consistency: Gossip Protocol + Last-Write-Wins (LWW)
- Employs an AP (Availability + Partition Tolerance) strategy under the CAP theorem.
- Accepts local writes instantly and propagates updates via peer-to-peer gossip. Conflicts are resolved deterministically using Lamport timestamps.

### 7. Caching & Resiliency: Redis Cache-Aside with Stale Fallback
- Dual-key strategy: `fresh:plan:<topic>` (10s TTL) for hot queries and `stale:plan:<topic>` as permanent backup.
- **Fault-Tolerant Paths:** If Redis is down, calls pass through to the backend; if the backend is down, stale cache data is served to preserve uptime.

### 8. Consensus: Raft Leader Election & Heartbeats
- Implements Candidate, Follower, and Leader states with randomized election timeouts (150ms–300ms).
- When a leader node crashes, followers detect heartbeat loss and elect a new leader through quorum voting ($2/3$ votes).

### 9. Orchestration: Kubernetes (Minikube) & Headless gRPC Balancing
- Solves the **gRPC Load Balancing Trap** where standard L4 Kubernetes proxies pin persistent HTTP/2 TCP streams to a single pod.
- Uses `clusterIP: None` (Headless Service) so client-side DNS (`dns:///worker-svc:60201`) balances requests round-robin across all pod IPs. Automatically restarts crashed pods within seconds.

### 10. Storage: ResearchDFS (Chunking, Cryptographic Integrity & Auto-Repair)
- Decouples metadata coordination (`dfs_metadata.py`) from chunk storage (`dfs_storage.py`).
- Files are split into **64 KB blocks**, stored with dual replication ($RF=2$).
- **Cryptographic Guard:** Validates SHA-256 hashes on write and read. Detects corrupted blocks and transparently retrieves healthy replicas.
- **Self-Healing:** Background daemon (`dfs_repair.py`) restores degraded chunks to available nodes upon storage worker crashes.

---

## 🛠️ Technology Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | Streamlit | Responsive reactive research dashboard & visualizations |
| **Agent Orchestration** | Sequential Pipeline / LangGraph | State management and agent lifecycle routing |
| **Primary LLM** | Google Gemini 2.5 Flash | High-speed planning, synthesis, and review |
| **Fallback LLM** | Groq LLaMA 3.3 70B | Automated failover during Gemini rate limits |
| **Relational Database** | PostgreSQL 15+ / SQLAlchemy | ACID transactions, research history, and user metadata |
| **Vector Database** | ChromaDB / HuggingFace `all-MiniLM-L6-v2` | Dense vector indexing, semantic search, and RAG |
| **Distributed RPC** | gRPC / Protocol Buffers (`proto3`) | Strongly typed, binary microservice communication |
| **Caching & In-Memory**| Redis | Low-latency Cache-Aside gateway with stale fallback |
| **Orchestration** | Docker, Kubernetes (Minikube) | Multi-replica container management & headless balancing |
| **Distributed Storage**| ResearchDFS (Python) | Block-chunked (64 KB) replicated storage with auto-repair |

---

## 📂 Repository Structure

```
researchpilot-ai/
├── agents/                      # AI Agent Implementations
│   ├── base.py                  # Base agent abstraction
│   ├── planner.py               # Planning agent (deconstructs topic)
│   ├── researcher.py            # Researcher agent (web search + batched synthesis)
│   ├── writer.py                # Writer agent (citations + RAG report generation)
│   └── reviewer.py              # Reviewer agent (LLM-as-a-Judge scoring)
├── core/                        # Core Engine Utilities
│   ├── llm.py                   # Multi-provider LLM router (Gemini -> Groq -> Mock)
│   ├── prompts.py               # Prompt templates & JSON schemas
│   └── state.py                 # Pydantic agent pipeline state
├── database/                    # Persistence Layer
│   ├── connection.py            # PostgreSQL SQLAlchemy session manager
│   └── models.py                # Database schemas (Research, Sources, Reviews)
├── frontend/                    # Streamlit User Interface
│   ├── app.py                   # UI entry point & routing
│   └── components/              # UI widgets, pipeline renderers & export buttons
├── grpc_experiment/             # Distributed Computing Infrastructure Lab
│   ├── proto/                   # Protocol Buffer IDL definitions
│   │   ├── research.proto       # gRPC service contracts (Planner, Raft, Lock, Worker)
│   │   └── dfs.proto            # ResearchDFS contracts (Metadata & Storage services)
│   ├── k8s/                     # Kubernetes Manifests
│   │   ├── app.yaml             # Deployment (3 replicas) + Headless Service
│   │   └── load-test-job.yaml   # Distributed client load test job
│   ├── cache_gateway.py         # Redis Cache-Aside gateway with stale fallback
│   ├── dfs_client.py            # ResearchDFS client (put, get, status)
│   ├── dfs_metadata.py          # ResearchDFS metadata coordinator with Lamport clocks
│   ├── dfs_repair.py            # ResearchDFS auto-repair daemon for under-replicated chunks
│   ├── dfs_storage.py           # ResearchDFS chunk storage node daemon
│   ├── lamport_clock.py         # Lamport logical clock synchronization logic
│   ├── load_balancer.py         # Least-Connections Layer 7 Load Balancer
│   ├── lock_manager.py          # Wait-For Graph (WFG) deadlock manager
│   ├── node.py                  # Ricart-Agrawala distributed mutual exclusion node
│   ├── raft_node.py             # Raft consensus leader election engine
│   └── replica_node.py          # Gossip replication node with Last-Write-Wins (LWW)
├── rag/                         # Retrieval-Augmented Generation
│   ├── chunker.py               # Semantic document chunker (headers/paragraphs)
│   └── vectorstore.py           # ChromaDB embeddings manager
├── tools/                       # Tool Integrations (DuckDuckGo, Scraping, Citations)
├── EXPERIMENT_5_WALKTHROUGH.md  # Detailed report: Distributed Deadlock Detection
├── EXPERIMENT_6_WALKTHROUGH.md  # Detailed report: Least-Connections Load Balancing
├── EXPERIMENT_7_WALKTHROUGH.md  # Detailed report: Eventual Consistency (Gossip + LWW)
├── EXPERIMENT_8_WALKTHROUGH.md  # Detailed report: Redis Cache-Aside Resiliency
├── EXPERIMENT_9_WALKTHROUGH.md  # Detailed report: Raft Consensus Leader Election
├── EXPERIMENT_10_WALKTHROUGH.md # Detailed report: Kubernetes Deployment & Load Balancing
├── EXPERIMENT_11_WALKTHROUGH.md # Detailed report: ResearchDFS Chunked Storage & Repair
├── ARCHITECTURE.md              # Deep-dive system architecture specification
├── IMPLEMENTATION.md            # Detailed implementation log
└── README.md                    # Project documentation
```

---

## 🚀 Installation & Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL (running locally or remotely)
- API Keys: Google AI Studio (`GEMINI_API_KEY`) and optionally Groq (`GROQ_API_KEY`)
- Docker Desktop & Minikube (for Kubernetes modules)

### 1. Clone the Repository
```bash
git clone https://github.com/Maheshwaree-02/agentic-research-assistant.git
cd agentic-research-assistant
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/researchpilot
```

### 3. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Launch the Streamlit Web Application
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to interact with ResearchPilot AI.

---

## ⚡ Running Distributed Computing Modules

Navigate to the experiment directory:
```bash
cd grpc_experiment
```

### 1. Recompile Protocol Buffers
```bash
python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/research.proto
python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/dfs.proto
```

### 2. Redis Caching & Outage Fallback
```bash
# Terminal 1: Start Planner Service
python -u planner_server.py

# Terminal 2: Query via Cache Gateway (Demonstrates Cache Miss -> Cache Hit -> Stale Fallback)
python cache_gateway.py "Docker vs Kubernetes"
```

### 3. Raft Leader Election & Heartbeats
```bash
# Open 3 terminals and run:
python -u raft_node.py A
python -u raft_node.py B
python -u raft_node.py C
# Kill Leader with Ctrl+C to observe automatic failover and term re-election!
```

### 4. Kubernetes Deployment & Headless gRPC Balancing
```bash
# Start Minikube & deploy manifests
minikube start --driver=docker
docker build -t myapp-backend:latest .
minikube image load myapp-backend:latest
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/load-test-job.yaml

# Check distributed execution logs
kubectl logs job/load-test
```

### 5. ResearchDFS Distributed File System (Chunking & Repair)
```bash
# Start 4 server terminals:
python -u dfs_metadata.py    # Terminal 1: Coordinator
python -u dfs_storage.py 1   # Terminal 2: Storage Node 1
python -u dfs_storage.py 2   # Terminal 3: Storage Node 2
python -u dfs_storage.py 3   # Terminal 4: Storage Node 3

# Terminal 5: Client operations
python -c "import os; open('paper.bin', 'wb').write(os.urandom(300000))"
python dfs_client.py put paper.bin
python dfs_client.py status
python dfs_client.py get paper.bin out.bin

# Test failover: kill storage node 2, then run:
python dfs_repair.py
python dfs_client.py status
```

---

## 📊 Scalability & CAP Theorem Analysis

### CAP Theorem Strategy

```
                    Consistency (C)
                         /\
                        /  \
                       /    \
                      / POST \
                     / GRESQL \
                    /   (CP)   \
                   /            \
  Availability ── ChromaDB / ───── Partition
      (A)       ResearchDFS (AP)  Tolerance (P)
```

- **PostgreSQL (CP):** Strong consistency via ACID transactions. Enforces strict schema integrity for user research records and audit history.
- **ChromaDB & ResearchDFS (AP):** High availability with eventual consistency. Vector searches and block downloads remain available during network degradation; replica convergence is handled asynchronously.
- **LLM Router (AP):** Gracefully falls back across models (Gemini $\to$ Groq $\to$ Mock) to guarantee uptime rather than returning 503 errors.

---

## 📖 Walkthrough Guides & Documentation

For step-by-step instructions, logs, and screenshots for each distributed experiment, refer to the dedicated guides:
- 📄 [EXPERIMENT_5_WALKTHROUGH.md](EXPERIMENT_5_WALKTHROUGH.md) — Centralized Deadlock Detection & Resolution
- 📄 [EXPERIMENT_6_WALKTHROUGH.md](EXPERIMENT_6_WALKTHROUGH.md) — Least-Connections Load Balancing
- 📄 [EXPERIMENT_7_WALKTHROUGH.md](EXPERIMENT_7_WALKTHROUGH.md) — Eventual Consistency (Gossip + Last-Write-Wins)
- 📄 [EXPERIMENT_8_WALKTHROUGH.md](EXPERIMENT_8_WALKTHROUGH.md) — Redis Cache-Aside & Stale Fallback
- 📄 [EXPERIMENT_9_WALKTHROUGH.md](EXPERIMENT_9_WALKTHROUGH.md) — Raft Consensus Protocol & Leader Election
- 📄 [EXPERIMENT_10_WALKTHROUGH.md](EXPERIMENT_10_WALKTHROUGH.md) — Kubernetes Orchestration & Headless Load Balancing
- 📄 [EXPERIMENT_11_WALKTHROUGH.md](EXPERIMENT_11_WALKTHROUGH.md) — ResearchDFS Chunked Storage, Integrity & Auto-Repair
- 📄 [ARCHITECTURE.md](ARCHITECTURE.md) — Full System Architecture Blueprint

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
