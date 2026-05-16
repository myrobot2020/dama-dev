# AI Inventory & Model Tracking

This table tracks the current models, prompts, and scripts used in the Dama pipeline. It serves as the source of truth for avoiding model drift and ensuring reproducible generation.

| Workflow / Stage | Primary Script | Model | Prompt Version | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Quiz Generation** | `19_generate_quiz.py` | `qwen2.5:14b` | `quiz-v1` (Hardcoded) | Active | Generates MCQs from sutta + commentary. |
| **Transcription** | (External/Manual) | YouTube / Whisper | N/A | Active | Sourced from `JSON3` transcripts. |
| **Segmentation** | `04_segment_split.py` | Regex (LLM soon) | N/A | Legacy | Moving to LLM for longer suttas (Issue #2). |
| **Comm. Segment** | `05_segment_commentary.py` | Regex (LLM soon) | N/A | Legacy | Identifying teacher-aligned commentary. |
| **Translation** | `16_translate_ja.py` | (Drafting) | `trans-ja-v1` | Planning | Japanese translation layer. |
| **Image Match** | (Drafting) | `gpt-4o-mini` | `img-match-v1` | Research | Mapping manga panels to sutta segments. |
| **Embeddings** | (Drafting) | `text-embedding-3-small`| N/A | Planning | Generating vectors for LanceDB. |

## Version History & Changes

*   **2024-05-20**: Initial inventory created.
*   **Next Action**: Extract hardcoded prompts from `19_generate_quiz.py` into a versioned library.
*   **Next Action**: Update `04_segment_split.py` to use `qwen2.5` or `gpt-4o` for structural parsing.
