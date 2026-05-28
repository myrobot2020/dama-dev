# AI Inventory & Model Tracking

This table tracks the current models, prompts, and scripts used in the Dama pipeline. It serves as the source of truth for avoiding model drift and ensuring reproducible generation.

| Workflow / Stage | Primary Script | Model | Prompt Version | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Quiz Generation** | `19_generate_quiz.py` | `qwen2.5:14b` | `quiz-v1` (Hardcoded) | Active | Generates MCQs from sutta + commentary. |
| **Transcription** | (External/Manual) | YouTube / Whisper | N/A | Active | Sourced from `JSON3` transcripts. |
| **Segmentation** | `04_segment_split.py` | Regex (LLM soon) | N/A | Legacy | Moving to LLM for longer suttas (Issue #2). |
| **Comm. Segment** | `05_segment_commentary.py` | Regex (LLM soon) | N/A | Legacy | Identifying teacher-aligned commentary. |
| **Translation** | `16_translate_ja.py` | (Drafting) | `trans-ja-v1` | Planning | Japanese translation layer. |
| **Manga Narrative**| `describe_volume.py` | `llava` + `qwen` | `manga-v2.4` (Seed) | **GOLD** | Central: `gs://damaprompts-492316/library/damamangapromptbook.md` |
| **Chat Response** | `an1_app.py` | `gemini-1.5-flash` | `chat-v1.0.0` | **Active** | Central: `gs://damaprompts-492316/library/damachatpromptbook.md` |
| **Embeddings** | (Drafting) | `text-embedding-3-small`| N/A | Planning | Generating vectors for LanceDB. |

## Central Prompt Library (`damaprompts`)
The other repositories have updated the master library in GCS.

### Manga Evolution (`damamanga`)
*   **v1.0**: Literal baseline (Deprecated).
*   **v2.1**: Psychological deep-dive (Deprecated).
*   **v2.3**: Narrative rebel (Retired).
*   **v2.4**: **Seed-Injection** (Current Gold Standard). Uses random "Opening Seeds" to break robot patterns.

### Chat Intelligence (`damachat`)
*   **v1.0.0**: Strict Citation Guard for `(AN ...)` vs `(cAN ...)`.
*   **Grounding**: "No source segment, no sealed generated claim."
