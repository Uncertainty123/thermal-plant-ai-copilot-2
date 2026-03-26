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

## How the synthetic industrial data is shaped

The `data/` directory includes:

- healthy records
- degraded records
- harmful records
- PLC command events
- SCADA historian-like telemetry rows
- DCS alarm rows


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

# Check the WebApp from below link
---https://thermal-plant-ai-copilot-2-kent3axabpbxapxzr7ivsx.streamlit.app/


Where exact thresholds are not published plant-by-plant, this system uses conservative engineering approximations and explicitly marks them as synthetic demo values.
