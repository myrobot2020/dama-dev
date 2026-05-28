# Codex Pipeline Fork

This folder is a numbered, modular pipeline fork that reuses the current repo
logic while keeping the alternate implementation isolated from `scripts/pipeline/`.

## Goals

- Keep the same stage numbering.
- Make the data flow cloud-friendly.
- Preserve compatibility with the existing `validated-json/` shape.
- Give each stage a narrow responsibility so it can be split across containers.

## Suggested container split

- `container_1`: dashboard, ingest, normalization, validation, indexing, and CPU-light stages.
- `container_2`: translation and other medium GPU tasks.
- `container_3`: dubbing and the heaviest GPU tasks.

## Authoritative stores

These names now match the repo registry:

- `damahdb` -> sealed warehouse in GCS
- `damabuffer` -> raw/transient asset buffer in GCS
- `damaprompts` -> prompt library in GCS
- `damalance` -> local LanceDB factory VDB
- `damaevents` -> local SQLite operational brain

## Example record

The AN example you pointed at is represented in the repo as:

- `validated-json/an/an8/8.2.15.json`
- `validated-json/an/an8/8.2.18.json`

Those records already contain the fields this fork expects:

- `sutta_id`
- `sutta_name_en`
- `sutta_name_pali`
- `sutta`
- `commentary`
- `aud_file`
- `aud_start_s`
- `aud_end_s`
- `chain`
- `valid`

## Ingest note

For the current fork, raw URLs and intermediate transcript/audio assets should be treated as `damabuffer` material until the record is validated and sealed into `damahdb`.
