# Dama Stores Registry
This registry defines the authoritative data stores for the Dama project. Use these identifiers and paths across all repositories.

## Cloud Stores (GCP)
| Name | Type | Bucket / URI | Purpose |
| :--- | :--- | :--- | :--- |
| **damahdb** | GCS | `gs://damahdb-dama-492316` | **The Warehouse**: Final sealed Sutta JSONs, MP3s, and Images. |
| **damabuffer** | GCS | `gs://damabuffer-dama-492316` | **Asset Buffer**: Raw transcripts, full audio, and retry assets. |
| **damaprompts** | GCS | `gs://damaprompts-dama-492316` | **Prompt Library**: Versioned AI prompts (v1, v2, v3). |

## App Backend (Supabase)
- **Project ID**: `dama-492316`
- **URL**: `https://dama-492316.supabase.co`
- **Tables**: `profiles`, `reading_progress`, `quiz_results`, `harness_traces`, `teacher_registry`
- **VDB (Prod)**: `damapgvector` (Table: `public.sutta_embeddings`)

## Local Stores (Factory)
| Name | Type | Path | Purpose |
| :--- | :--- | :--- | :--- |
| **damalance** | LanceDB | `data/mock_db/lancedb/` | **Factory VDB**: Local fast matching of Manga to Suttas. |
| **damaevents** | SQLite | `data/work/streaming/pipeline.sqlite3` | **Operational Brain**: Pipeline job state and event logs. |

## Pipeline Logic & Prompts
| Name | Type | Path / Location | Purpose |
| :--- | :--- | :--- | :--- |
| **Prompt Book** | Python | `codex/prompts.py` | **Central Prompts**: All AI system prompts and segmentation regex rules. |
| **Sutta Mapping** | JSON | `codex/codex2/*.json` | **Mapping State**: Current mapping of teacher IDs to SuttaCentral UIDs. |
| **GCS Prompts** | Cloud | `gs://damaprompts-dama-492316` | **Prompt Backup**: Mirrored and versioned prompts for cloud deployments. |

## Authentication
- **Service Account**: `dama-factory-bot@dama-492316.iam.gserviceaccount.com`
- **Key File**: `factory-bot-key.json` (Required for GCS write access).

## Gold Standard Reference
- **Sutta**: 8.2.18
- **Path**: `gs://damahdb-dama-492316/hdb/nikaya=AN/book=08/sutta=8.2.18/run=001/8.2.18.json`
