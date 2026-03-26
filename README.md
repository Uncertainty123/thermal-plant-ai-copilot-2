# Mechanical Advantage Thermal Plant AI Copilot

This repository is a working thermal power plant auxiliary-monitoring copilot. It combines deterministic physics checks, an agentic AI workflow, representative PLC/DCS/SCADA-style sample data, and optional Ollama-based open-source LLM summarization. The design is intentionally conservative: the plant-safety logic does not depend on the LLM.

## What it does

- Simulates boiler auxiliary telemetry for `BFP`, `SH`, `DRUM`, and `FURNACE`
- Detects anomalies using plant-style operating limits and cross-tag logic
- Generates diagnosis and safe operating actions through an agent pipeline
- Enforces safety guardrails such as coal-feed block and master fuel trip
- Logs every cycle to `logs/audit_log.jsonl`
- Displays trends, evidence, commands, interlocks, and sample industrial source data in Streamlit
- Uses Ollama locally or through a remote/cloud-compatible Ollama endpoint when available

## Current agent flow

1. `MonitorAgent` checks values and operating relationships such as steam/feedwater imbalance.
2. `ReasonerAgent` turns those signals into engineering causes and conservative commands.
3. `GuardrailAgent` blocks unsafe actions and enforces trip-safe commands.
4. `OptionalLLMAgent` adds a short summary through Ollama, but the app still runs if the model is unavailable.

## Project structure

- [frontend/app.py](C:\Users\mecha\Documents\mech advantage\frontend\app.py): Streamlit UI
- [backend/config.py](C:\Users\mecha\Documents\mech advantage\backend\config.py): limits, tags, and industrial tag profiles
- [backend/simulator.py](C:\Users\mecha\Documents\mech advantage\backend\simulator.py): telemetry and control-state simulator
- [backend/agents/monitor.py](C:\Users\mecha\Documents\mech advantage\backend\agents\monitor.py): anomaly detection
- [backend/agents/reasoner.py](C:\Users\mecha\Documents\mech advantage\backend\agents\reasoner.py): engineering diagnosis
- [backend/agents/guardrail.py](C:\Users\mecha\Documents\mech advantage\backend\agents\guardrail.py): interlocks and safe commands
- [backend/agents/llm.py](C:\Users\mecha\Documents\mech advantage\backend\agents\llm.py): Ollama integration
- [data/sample_scada.csv](C:\Users\mecha\Documents\mech advantage\data\sample_scada.csv): representative SCADA records
- [data/sample_plc_events.csv](C:\Users\mecha\Documents\mech advantage\data\sample_plc_events.csv): representative PLC events
- [data/sample_dcs_alarms.csv](C:\Users\mecha\Documents\mech advantage\data\sample_dcs_alarms.csv): representative DCS alarms
- [ARCHITECTURE.md](C:\Users\mecha\Documents\mech advantage\ARCHITECTURE.md): jury-facing architecture note

## Important data note

The repository does not contain proprietary plant exports. The source files in `data/` are synthetic industrial-style records for safe testing and demonstration. They are meant to resemble real operational tag structures and alarm patterns, not to claim they are actual plant data.

## Plant protection logic

- `SH_TEMP` critical limit: `545 degC`
- `SH_PRESS` normal: `160-180 bar`, trip-oriented concern above `190 bar`
- `DRUM_LEVEL` operating band: `+/-250 mm`
- Superheater overtemperature can drive `COAL_FEED_CMD` to `0` and assert `MASTER_FUEL_TRIP`
- Drum high-high or low-low excursion can assert trip-safe commands
- Rich combustion with low `FURNACE_O2` clamps fuel demand

This should be treated as decision support, not a real protection system.

## Open-source LLM support with Ollama

The app supports Ollama through the HTTP API. This works both for a local Ollama server and for a remote/cloud-compatible endpoint.

### Recommended model choices for low-end hardware

Your machine has only about `4 GB RAM` and `512 MB VRAM`, so do not plan on running a serious reasoning model locally. Use one of these approaches instead:

1. Remote Ollama server on a stronger machine or VPS
2. Ollama cloud-compatible endpoint if you have access
3. Keep LLM disabled and rely on deterministic plant logic for the demo

### Environment variables

```powershell
$env:OLLAMA_BASE_URL="http://localhost:11434/api"
$env:OLLAMA_MODEL="gpt-oss:20b"
```

If your endpoint requires auth:

```powershell
$env:OLLAMA_API_KEY="your-token"
```

### Run with a remote Ollama host

```powershell
$env:OLLAMA_BASE_URL="https://your-remote-host.example/api"
$env:OLLAMA_MODEL="gpt-oss:20b"
python -m streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8502
```

## Installation and run

1. Open PowerShell.
2. Move into the project folder:
   ```powershell
   cd "C:\Users\mecha\Documents\mech advantage"
   ```
3. Install packages:
   ```powershell
   python -m pip install --user -r requirements.txt
   ```
4. Start the app:
   ```powershell
   python -m streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8502
   ```
5. Open [http://localhost:8502](http://localhost:8502).

If port `8501` is free on your machine, you can use `8501` instead. During verification in this environment, `8501` was already occupied, so `8502` was used.

## Backend smoke test

Run this before Streamlit if you want a quick pipeline check:

```powershell
python -c "from backend.services.pipeline import PlantMonitoringSystem; s=PlantMonitoringSystem(); r=s.run_cycle(); print(r.detection.severity); print(r.snapshot.values); print(r.guardrail.enforced_commands); print(r.llm_status)"
```

## How the synthetic industrial data is shaped

The `data/` directory includes:

- healthy records
- degraded records
- harmful records
- PLC command events
- SCADA historian-like telemetry rows
- DCS alarm rows

This gives you both normal and upset scenarios for demo, testing, and future ingestion into SQLite, Postgres, or a historian adapter.

## How to explain this to a jury

1. The protection logic is deterministic and does not rely on LLM output.
2. The agent layer is used to structure diagnosis, reasoning, and safe recommendation generation.
3. The data model is already shaped for industrial integration through generic tags plus industrial tag profiles.
4. The same pattern can be extended to nuclear and oil-and-gas by swapping equipment modules, thresholds, and interlocks.

## Scalability to nuclear and oil & gas

Yes, the same architecture can scale to those sectors with domain-specific changes.

### For nuclear

- Replace boiler/furnace modules with reactor coolant, steam generators, pressurizer, and containment modules
- Add stricter validation, deterministic state machines, and formal trip logic
- Keep the LLM outside safety-critical control paths

### For oil & gas

- Replace auxiliary logic with compressor, separator, furnace, flare, and pump modules
- Add process-safety tags such as pressure relief, ESD, gas detection, and compressor surge limits

The agent pattern remains the same. The process models, alarm priorities, and safety envelopes change by industry.

## Public grounding and references

The operating envelopes and design choices are informed by public references and engineering conventions, not private plant exports. Relevant references include:

- Ollama API and structured chat examples: [docs.ollama.com](https://docs.ollama.com/capabilities/structured-outputs)
- Ollama FAQ on cloud behavior and hosted models: [docs.ollama.com](https://docs.ollama.com/faq)
- Representative industrial tag naming pattern example: [Kepware tag naming convention](https://support.ptc.com/help/kepware/drivers/en/kepware/drivers/WAGOETHERNET/tag-naming-convention.html)
- Public news reference for CSTPS 500 MW unit context: [Times of India, January 12 2015](https://timesofindia.indiatimes.com/city/nagpur/cstps-new-500mw-unit-synchronized/articleshow/45846419.cms)

Where exact thresholds are not published plant-by-plant, this system uses conservative engineering approximations and explicitly marks them as synthetic demo values.
