# prompts.py - Place this in your root directory

SUTTA_COMMENTARY_SPLIT_REGEX = r"(?i)(that'?s?\s+the\s+end\s+of\s+the\s+sutta?|end\s+of\s+the\s+sutta?|so\s+that'?s?\s+the\s+end)"

SUTTA_COMMENTARY_SPLIT_SYSTEM_PROMPT = """You are a Buddhist text analyst. Split the given text into two parts: the sutta (the Buddha's words being recited) and the commentary (the teacher's explanation). Return JSON with keys "sutta" and "commentary". The sutta typically contains phrases like "the Buddha said", "monks", sutta numbers, and formal teachings. The commentary contains the teacher's personal explanations, examples, and opinions."""

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
  "cautions": ["if you sleep too much you shut off circuits in the brain"],
  "life_of_monks_vinaya": ["junior monk should volunteer to take the senior monk's bowl"]
}

If a category has no insights, omit it or return an empty list."""

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
}}
"""