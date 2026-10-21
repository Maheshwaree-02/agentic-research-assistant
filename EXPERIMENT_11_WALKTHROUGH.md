# Experiment 11: Distributed File System (ResearchDFS)
**Course:** Distributed Computing Lab (DC Lab)  
**Project Integration:** ResearchPilot AI  
**Topic:** Chunking, Replication, Failover, Integrity Verification, and Auto-Repair

---

## 1. Experiment Overview & Objective

| Parameter | Details |
|---|---|
| **Experiment No.** | 11 |
| **Title** | Distributed File System Storage: Chunking, Replication, Failover, and Repair |
| **Goal** | Build a fault-tolerant distributed file system inspired by Google File System (GFS) and Apache HDFS, tailored for **ResearchPilot AI**. |
| **Core Architecture** | Decoupled Metadata Coordinator (control plane) and Storage Nodes (data plane) with 64 KB block chunking, SHA-256 checksums, Lamport Logical Clocks for file versioning, and auto-repair. |
| **Fault Tolerance** | Reads continue seamlessly even when a storage node abruptly crashes or a disk block gets corrupted; under-replicated chunks are automatically re-replicated to healthy nodes. |

### Why this matters for ResearchPilot AI
In **ResearchPilot AI**, the system continuously downloads academic papers (PDFs), scrapes extensive web datasets, and synthesizes long-form multi-section research dossiers. If these large documents are stored on a single machine or disk:
1. **Single Point of Storage Failure:** A single hard drive crash would permanently destroy research corpus data and user reports.
2. **Bandwidth Bottleneck:** Reading large multi-megabyte papers from one disk saturates network I/O.

**ResearchDFS solves this:**
- Files are divided into fixed-size **64 KB chunks**.
- Each chunk is replicated across **multiple independent storage daemons** (Replication Factor = 2).
- The **Metadata Coordinator** (`dfs_metadata.py`) only manages the namespace, chunk mapping, Lamport clocks, and node health—it **never touches file bytes**.
- Storage nodes (`dfs_storage.py`) store raw chunks with cryptographic **SHA-256 integrity verification**.
- A dedicated **Repair Daemon** (`dfs_repair.py`) heals under-replicated chunks whenever a node dies.

---

## 2. Architecture & Components

```
                +------------------------------------+
                |  ResearchDFS Metadata Coordinator   |
                |         (dfs_metadata.py)          |
                |  - Tracks files, versions, chunks  |
                |  - Monitors node heartbeats (6s)   |
                |  - Lamport Clock for revisions     |
                +-----------------+------------------+
                                  ^
     1. Allocate / Commit / Query | Heartbeats (2s)
                                  v
+-----------------------+   Direct Data Transfer   +------------------------------------+
|  ResearchDFS Client   | =======================> | Research Storage Nodes (3 Nodes)   |
|   (dfs_client.py)     | <======================= | (dfs_storage.py 1, 2, 3)           |
| - Splits into 64KB    |   (PutChunk / GetChunk)  | - Store chunks on local disk       |
| - Verifies SHA-256    |                          | - SHA-256 checksum on write/read   |
+-----------------------+                          +------------------------------------+
```

### Process Roles:
1. **Metadata Server (`dfs_metadata.py` - Port 60501):**
   - Keeps track of all files, versions, file sizes, SHA-256 signatures, and which storage nodes hold each chunk.
   - Assigns new chunk allocations to the **least-loaded live nodes**.
   - Increments file versions using a **Lamport Logical Clock**.
   - Persists state to `dfs_data/metadata.json` so file metadata survives restarts.
2. **Storage Nodes (`dfs_storage.py 1, 2, 3` - Ports 60511, 60512, 60513):**
   - Pure data-plane nodes. Store chunks on disk under `dfs_data/store-X/`.
   - Send heartbeats to the coordinator every **2.0 seconds**.
   - Check SHA-256 before writing and after reading.
3. **Client (`dfs_client.py`):**
   - `put`: Splits files into 64 KB chunks, requests allocation plan, writes chunks directly to assigned nodes, and commits.
   - `get`: Queries chunk locations, downloads each chunk from the first healthy replica, verifies chunk checksums, reassembles the file, and validates the whole-file checksum.
   - `status`: Displays real-time cluster health, node status (UP/DOWN), file versions, and chunk replication layout.
4. **Repair Daemon (`dfs_repair.py`):**
   - Queries cluster status for under-replicated chunks (replicas < 2).
   - Reads an intact copy from a surviving node and copies it to another healthy node.
   - Registers the newly established replica with the metadata coordinator.

---

## 3. Step-by-Step Execution Guide

All code is pre-configured and compiled in:
`C:\Users\bharg\researchpilot-ai\grpc_experiment`

> **Note on Windows / Git Bash:** Always run python scripts with the `-u` flag (e.g. `python -u dfs_metadata.py`) to prevent terminal output buffering.

---

### Phase 1: Launch the Cluster (4 Server Terminals)

Open **4 separate Git Bash / PowerShell terminals** and navigate to your experiment folder:
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
```

#### Terminal 1: Metadata Coordinator
```bash
python -u dfs_metadata.py
```
*Expected Output:*
```text
DFS metadata server listening on localhost:60501 (replication factor 2)
```

#### Terminal 2: Storage Node 1
```bash
python -u dfs_storage.py 1
```
*Expected Output:*
```text
DFS storage node store-1 listening on localhost:60511, keeping chunks in dfs_data/store-1/
[store-1] connected to metadata server at localhost:60501
```

#### Terminal 3: Storage Node 2
```bash
python -u dfs_storage.py 2
```
*Expected Output:*
```text
DFS storage node store-2 listening on localhost:60512, keeping chunks in dfs_data/store-2/
[store-2] connected to metadata server at localhost:60501
```

#### Terminal 4: Storage Node 3
```bash
python -u dfs_storage.py 3
```
*Expected Output:*
```text
DFS storage node store-3 listening on localhost:60513, keeping chunks in dfs_data/store-3/
[store-3] connected to metadata server at localhost:60501
```

*(Terminal 1 will log registration events for `store-1`, `store-2`, and `store-3`)*.

---

### Phase 2: Client Upload & Download (Terminal 5)

Open a **5th terminal** for all client operations:
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
```

#### Step 1: Check Initial Cluster Status
```bash
python dfs_client.py status
```
> 📸 **SCREENSHOT 1:** Shows all 3 storage nodes `UP` with 0 chunks held, and `Files: (none)`.

#### Step 2: Create a Sample Research Paper File
Generate a 300,000-byte test file (representing a research document). At 64 KB per chunk, this yields exactly **5 chunks**:
```bash
python -c "import os; open('research_paper.bin', 'wb').write(os.urandom(300000))"
```

#### Step 3: Upload the Research Document (`put`)
```bash
python dfs_client.py put research_paper.bin
```
*Expected Output:*
- Metadata coordinator allocates 5 chunks across the least-loaded nodes.
- Each chunk is written to 2 storage nodes.
- File is committed with Lamport timestamp versioning and whole-file SHA-256.

#### Step 4: Verify Cluster Placement
```bash
python dfs_client.py status
```
> 📸 **SCREENSHOT 2:** Shows 5 chunks evenly distributed across `store-1`, `store-2`, and `store-3` (each holding 3–4 chunks, replication factor = 2).

#### Step 5: Download & Verify Integrity (`get`)
```bash
python dfs_client.py get research_paper.bin out1.bin
```
Verify the downloaded file matches the original byte-for-byte:
```bash
python -c "import sys; f1=open('research_paper.bin','rb').read(); f2=open('out1.bin','rb').read(); print('FILES ARE IDENTICAL!' if f1==f2 else 'DIFFER!')"
```
> 📸 **SCREENSHOT 3:** Shows successful retrieval with message `OK: wrote 300000 bytes to out1.bin, checksum verified.` and `FILES ARE IDENTICAL!`.

---

### Phase 3: Fault Tolerance & Break Tests (Terminal 5)

#### Test 1: Immediate Read Failover (Node Crashes)
In **Terminal 3** (`store-2`), press `Ctrl + C` to simulate an immediate node crash.

Immediately in **Terminal 5**, download the document:
```bash
python dfs_client.py get research_paper.bin out2.bin
```
*Expected Output:*
The client detects that `store-2` is unavailable on chunks that were assigned to it, logs:
`chunk X: store-2 unavailable (UNAVAILABLE), trying next replica`
and seamlessly downloads the chunk from the alternative replica (`store-1` or `store-3`). The entire file is verified and saved successfully!

#### Test 2: Coordinator Heartbeat Expiry Detection
Wait **8 seconds** (heartbeat timeout is 6.0 seconds).
In **Terminal 1** (Metadata Coordinator), observe:
```text
Node store-2 is DOWN (no heartbeat)
```
In **Terminal 5**, run:
```bash
python dfs_client.py status
```
> 📸 **SCREENSHOT 4:** Shows `store-2 DOWN` and its assigned chunks marked as `(down)`. Some chunks now have only 1 live copy remaining!

#### Test 3: Auto-Repair Missing Replicas
Run the self-healing repair daemon to restore the replication factor:
```bash
python dfs_repair.py
```
*Expected Output:*
The repair script identifies under-replicated chunks, copies them from healthy nodes to available nodes (`store-1` or `store-3`), and updates the metadata coordinator.

Check cluster status again:
```bash
python dfs_client.py status
```
> 📸 **SCREENSHOT 5:** Shows all chunks have 2 live replicas again (distributed across `store-1` and `store-3`) while `store-2` remains DOWN!

Download to verify repaired state:
```bash
python dfs_client.py get research_paper.bin out3.bin
```

#### Test 4: Cryptographic Block Corruption Detection
Simulate bit rot or hard drive sector corruption by overwriting one stored chunk on `store-1`:
```bash
python -c "import os; chunk=os.listdir('dfs_data/store-1')[0]; open(f'dfs_data/store-1/{chunk}','wb').write(b'CORRUPTED GARBAGE DATA'); print(f'Corrupted {chunk}')"
```

Now try to download the file:
```bash
python dfs_client.py get research_paper.bin out4.bin
```
*Expected Output:*
```text
chunk 0: store-1 returned CORRUPT data, trying next replica
chunk 0: read from store-3
OK: wrote 300000 bytes to out4.bin, checksum verified.
```
> 📸 **SCREENSHOT 6:** Proves cryptographic protection. The client automatically catches the SHA-256 hash mismatch, rejects the corrupted block, falls back to the intact replica, and delivers an uncorrupted file!

#### Test 5: Reconnecting the Dead Node
In **Terminal 3**, restart Storage Node 2:
```bash
python -u dfs_storage.py 2
```
In **Terminal 1**, observe:
```text
Node store-2 is BACK UP
```
Check status:
```bash
python dfs_client.py status
```
`store-2` rejoins the cluster cleanly with its previously saved chunks intact.

#### Test 6: Load Balancing a Second File
Upload a second research document:
```bash
python -c "import os; open('summary_report.bin', 'wb').write(os.urandom(70000))"
python dfs_client.py put summary_report.bin
python dfs_client.py status
```
Notice:
1. New chunks are assigned preferentially to the least-loaded nodes.
2. The Lamport Logical Clock version increments cleanly.

---

## 4. Key Learnings & Evaluation Summary

1. **Separation of Control and Data Planes:** Keeping metadata apart from chunk bytes ensures high throughput and simple, disposable storage nodes.
2. **Cryptographic Integrity:** Every chunk is verified using SHA-256. Silent data corruption (bit rot) is caught immediately at read time.
3. **Client-Side Failover:** The client handles transport failures and corruptions transparently by falling back to alternative replicas.
4. **Auto-Healing:** The repair tool restores the required replication factor (RF=2) without administrator intervention.
5. **Lamport Clocks:** Used to order document revisions consistently across distributed nodes without synchronizing physical wall clocks.
