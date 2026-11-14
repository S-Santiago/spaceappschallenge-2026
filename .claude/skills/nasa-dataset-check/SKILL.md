---
name: nasa-dataset-check
description: Run the official minimum data check on a dataset or API (source, version, license, variables & units, coverage, limits, small test, traceability) and register it in docs/nasa-data.md. Use whenever a new dataset, API or data file is introduced in the project.
---

# NASA dataset check

Argument: dataset name, URL or file path.

1. Identify the official landing page / DOI. Do not rely on memory for versions, URLs or terms — open the official page. Mark anything unverified as `UNVERIFIED`.
2. Answer the six official questions:
   | Check | Question |
   |---|---|
   | Source & version | Where does it come from? Link, version or access date? License? |
   | Variables & units | What does each variable measure, in which units? Missing values / fill values / scale factors? |
   | Coverage | Period, geographic area, spatial & temporal resolution? |
   | Limits | What does it NOT allow us to conclude? |
   | Small test | Can we test a sample before downloading everything? (do it; save to `data/samples/`) |
   | Traceability | What is observation, transformation, inference or synthetic? |
3. State its **role in the solution** and what would break without it.
4. Determine whether it is a **NASA resource listed in the challenge** (check `docs/challenge.md`) — required for Global Awards.
5. Append a `### D-XX` entry to section 1 of `docs/nasa-data.md` using the template in section 3, and update the table at the top. Remove it from the "candidates" table if it was there.
6. Add the dataset to section 3 of `docs/third-party.md` with its terms and citation.
7. If an access script was written, reference its path in the entry.

Report back (in Spanish) a 5-line summary and any open risk.
