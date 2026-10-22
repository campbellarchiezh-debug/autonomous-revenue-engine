# Worker Assignment: Milestone 1 (B2B Lead Sourcing & Conversion Leak Audit Pipeline)
Working Directory: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/worker_m1
Project Root: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine
Original Request: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/ORIGINAL_REQUEST.md
Project Specification: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/orchestrator/PROJECT.md
Survey Handoff Reference: /Users/archiecampbell/.gemini/antigravity/scratch/autonomous_revenue_engine/.agents/teamwork/explorer_survey_1/handoff.md

## Exclusive Write Ownership
You exclusively own:
- `data/b2b_leads/` (all subdirectories: `schema/`, `audits/`, `pitches/`, `leads_dataset.json`, `leads_dataset.csv`)
- `src/b2b_pipeline/` (`__init__.py`, `models.py`, `leak_calculator.py`, `generator.py`)

## Deliverables Required
1. `data/b2b_leads/schema/b2b_leads_schema.json`: Complete Draft-07 JSON Schema validating all 15 lead targets.
2. `data/b2b_leads/leads_dataset.json`: Structured dataset of 15 verified commercial targets across 5 high-AOV verticals (luxury roofing, cosmetic dentistry, commercial HVAC, premium solar, medical aesthetics) with all required fields (domains, decision makers, emails, phones, leaks, lost pipeline calculations).
3. `data/b2b_leads/leads_dataset.csv`: Flattened CRM-ready CSV export with all 15 targets.
4. `data/b2b_leads/audits/`: 15 standalone Markdown audit diagnostic reports (`audit_tgt_001.md` to `audit_tgt_015.md`) detailing the exact technical/UX conversion leaks.
5. `data/b2b_leads/pitches/`: 15 tailored 90-second video/email pitch scripts (`pitch_tgt_001.md` to `pitch_tgt_015.md`) following the 4-part value-first framework with exact word counts (160-260 words, ~90 seconds speaking time).
6. `src/b2b_pipeline/`: Python modules for data models, conversion leak loss calculations, and report generation using Python standard library.
7. Verification: Run Python syntax checks and JSON/CSV validation. Document in handoff.md.
