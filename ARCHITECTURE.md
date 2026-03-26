# Architecture Overview

## Objective

Deliver a hackathon-ready AI copilot for thermal power plant auxiliary monitoring that stays useful even when no LLM is available.

## High-level flow

```text
Synthetic telemetry / future historian adapter
    -> Monitor Agent
    -> Reasoner Agent
    -> Guardrail Agent
    -> Optional Ollama Summary
    -> Streamlit UI + Audit Log
```

## Components

### 1. Telemetry layer

- Current source: synthetic but industry-shaped telemetry in [backend/simulator.py](C:\Users\mecha\Documents\mech advantage\backend\simulator.py)
- Future sources:
  - OPC UA
  - Modbus TCP adapters
  - historian dumps
  - CSV batch imports
  - SCADA APIs

### 2. Monitor Agent

Purpose:
- detect abnormal states using thresholds and tag relationships

Examples:
- low BFP flow with low SH pressure
- high SH temperature with high furnace temperature
- drum swell/shrink near trip limits
- rich combustion from low furnace oxygen

### 3. Reasoner Agent

Purpose:
- convert process-state evidence into engineering causes and conservative commands

Outputs:
- likely causes
- recommended operator actions
- recommended control moves such as spray-water increase or fuel reduction

### 4. Guardrail Agent

Purpose:
- guarantee the final response stays conservative

Examples:
- if `SH_TEMP >= 545 degC`, block coal feed and assert trip-safe command
- if `DRUM_LEVEL` crosses `+/-250 mm`, clamp commands to safe state
- if combustion is too rich, prevent fuel increase

### 5. Optional Ollama LLM

Purpose:
- summarize the current condition for the operator or jury

Important:
- it is not authoritative
- it is not in the safety path
- if unreachable, the system falls back automatically

## Data model

The app carries:

- telemetry values
- control-state values
- source-health labels
- anomaly evidence
- triggered interlocks
- approved and blocked commands
- audit records

This is enough to support UI demo, logging, future APIs, and future historian ingestion.

## Vendor-style integration stance

The current repository includes synthetic industrial tag profiles for:

- DCS-style tags
- PLC-style tags
- generic SCADA historian style tags

These are representative integration profiles only. They are not official vendor exports.

## Why this scales

### Thermal power

Current equipment modules:
- BFP
- SH
- DRUM
- FURNACE

### Nuclear

Replace the process modules with:
- reactor coolant system
- steam generator
- pressurizer
- condenser and feed systems

Keep:
- agent pipeline
- audit architecture
- UI pattern

Add:
- stronger formal validation
- redundant channel voting
- stricter regulatory evidence trails

### Oil and gas

Replace the modules with:
- compressors
- separators
- fired heaters
- flare/ESD systems
- pumps and tanks

Keep:
- anomaly detection pattern
- reasoner + guardrail split
- historian-ready schema

## Jury explanation

If the jury asks why this is "agentic AI" and not just a dashboard:

1. The monitor agent detects abnormal process states.
2. The reasoner agent maps those states to engineering causes and operator guidance.
3. The guardrail agent validates or overrides commands based on safety logic.
4. The LLM agent is optional and only used for language summarization.

That separation makes the system explainable, safer, and easier to scale across industries.
