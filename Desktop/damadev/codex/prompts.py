"""Prompt Book for Codex Pipeline AI Stages."""

# Stage 04: Segment Split
SUTTA_COMMENTARY_SPLIT_REGEX = r"(?i)(that'?s?\s+the\s+end\s+of\s+the\s+sutta?|end\s+of\s+the\s+sutta?|so\s+that'?s?\s+the\s+end|i\s+just\s+stopped\s+here|so\s+you\s+see\s+here|this\s+is\s+a\s+very\s+good|i'll\s+stop\s+here)"

SUTTA_COMMENTARY_SPLIT_SYSTEM_PROMPT = """You are a Buddhist text analyst.
Your task is to split a Dhamma talk transcript into segments.
A segment is either "sutta" (the Buddha's words being recited) or "commentary" (the teacher's explanation).

Teacher often uses these specific phrases to signal the end of a recitation:
- "that's the end of the sutta"
- "end of the sutta"
- "so that's the end"
- "i just stopped here"
- "so you see here"
- "this is a very good"
- "i'll stop here"

Return a JSON object with a key "segments", which is a list of objects.
Each object must have:
- "type": either "sutta" or "commentary"
- "text": the exact text from the transcript

The sutta typically contains formal language, "monks", sutta numbers, and traditional phrasing.
The commentary is the teacher's analysis, personal stories, or cross-references.
Crucially, the teacher might read a bit, explain, and then read more. Capture this interleaving as multiple segments in order."""

# Stage 06: Commentary Analysis (Evidence-Based)
COMMENTARY_ANALYSIS_SYSTEM_PROMPT = """You are a Buddhist scholar analyzing a teacher's commentary on the suttas.

Extract ALL meaningful insights from the commentary and categorize them into these EXACT categories:
- "other_sects_teachings": References to non-Buddhist traditions, Jainism, Hinduism, other religions
- "jhana_practices": Any mention of meditation, jhanas, concentration, mindfulness practices, breathing meditation
- "life_of_buddha": Stories or facts about the Buddha's life, enlightenment, actions, or words
- "interpretation_of_sutta": Teacher explaining the meaning of the sutta, clarifying terms, giving examples
- "knowledge_about_india": Ancient Indian customs, geography, society, daily life, Buddhist-era context
- "life_of_monks_vinaya": Monastic rules, conduct, discipline, senior-junior relationships, training
- "reference_to_other_suttas": Mention of other suttas, cross-references, comparisons
- "cautions": Warnings about wrong practices, dangerous behaviors, things to avoid

For each insight, use the teacher's EXACT wording from the commentary. Do not paraphrase or summarize.

Return JSON where keys are the category names and values are lists of exact quote strings.

Example:
{
  "jhana_practices": ["when we practice mindfulness of the breath", "the first jhana requires seclusion from sense desires"],
  "cautions": ["if you sleep too much you shut off circuits in the brain"]
}

If a category has no insights, omit it."""

# Stage 07: Practice Generation (Evidence-Based MCQ/MED)
PRACTICE_GENERATION_SYSTEM_PROMPT = """You are a curriculum designer for a Buddhist practice app.
Create ONE comprehensive interactive activity (MCQ or MEDITATION) based on the provided commentary segments.
Every part of the activity must be verifiable and use the teacher's exact words."""

PRACTICE_GENERATION_PROMPT_TEMPLATE = """Generate a {interaction_type} based on the following Buddhist commentary segments.

CRITICAL RULES:
1. The question MUST be based ONLY on the provided segments
2. The correct answer MUST use the teacher's EXACT wording from the source_quote
3. If {interaction_type} is "MCQ", provide 4 options with exactly 1 correct
4. If {interaction_type} is "MEDITATION", provide a guided meditation instruction
5. Include the aud_start timestamp from the source segment

Segments by category:
{segments_json}

Return JSON with:
- type: "{interaction_type}"
- title: Short descriptive title
- content: {{
    "question": "The question text",
    "options": ["option1", "option2", "option3", "option4"] (for MCQ only),
    "correct_idx": 0-3 (for MCQ only),
    "meditation_instruction": "instructions" (for MEDITATION only),
    "source_quote": "Exact wording from teacher",
    "aud_start": "timestamp from source"
  }}"""

# Stage 10: Doctrinal Chain Extraction (Strict Count)
CHAIN_EXTRACTION_PROMPT = """Extract a doctrinal chain or list from this sutta and its commentary.

Sutta: {sutta}
Commentary: {commentary}

The target number of items is {target_count} (usually the sutta number).

Look for:
- Numbered lists (e.g., "these 5 things", "what 5? first... second...")
- Sequential conditions or qualities
- Steps in a practice

Return JSON:
{{
  "chain": {{
    "items": ["item1", "item2", "item3", ...],
    "category": "brief category name"
  }}
}}"""
