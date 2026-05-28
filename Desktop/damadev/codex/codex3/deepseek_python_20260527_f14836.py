valid_cats = ["other_sects_teachings", "jhana_practices", "life_of_buddha",
              "interpretation_of_sutta", "knowledge_about_india",
              "life_of_monks_vinaya", "reference_to_other_suttas", "cautions"]

# Fuzzy mapping for common misspellings/variations
fuzzy_map = {
    "jhana": "jhana_practices",
    "jhanas": "jhana_practices",
    "meditation": "jhana_practices",
    "buddha_life": "life_of_buddha",
    "buddhas_life": "life_of_buddha",
    "vinaya": "life_of_monks_vinaya",
    "monastic": "life_of_monks_vinaya",
    "caution": "cautions",
    "warning": "cautions",
    "india": "knowledge_about_india",
    "ancient_india": "knowledge_about_india",
    "other_religions": "other_sects_teachings",
    "external_sects": "other_sects_teachings"
}