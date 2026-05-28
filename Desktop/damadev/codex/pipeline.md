# Codex Pipeline Map

The fork keeps the stage numbering but separates responsibilities more cleanly.

## Current forked stages

1. `00_normalize.py` - normalize raw corpus rows into the shared JSON shape.
2. `01_ingest.py` - ingest one source URL and create a starter record.
3. `03_identify.py` - mark a record as identified for downstream processing.
4. `10_keys.py` - validate chain readiness.
5. `11_clean.py` - clean text fields.
6. `12_validate.py` - set `valid`.
7. `15_cloud_plan.py` - document the container split.
8. `16_translate_ja.py` - translation handoff placeholder.
9. `18_sync_gcs.py` - cloud sync handoff placeholder.

## Example AN record path

- `validated-json/an/an8/8.2.15.json`
- `validated-json/an/an8/8.2.18.json`

## Suggested cloud routing

- `container_1`: stages `00`, `01`, `03`, `10`, `11`, `12`, `13`, `14`, `15`, `17`, `18`
- `container_2`: stage `16`
- `container_3`: dubbing stage that can be added later as `22_dub.py`

## Store mapping

- Raw URL fetch, transcripts, and retry assets belong in `damabuffer`
- Validated and sealed corpus outputs belong in `damahdb`
- Prompt versions should be referenced from `damaprompts`
- Local retrieval and matching should use `damalance`
- Pipeline events, jobs, and stage status should use `damaevents`
