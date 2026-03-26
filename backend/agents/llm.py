"""Optional Ollama-backed LLM wrapper with graceful fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from backend.models import DiagnosisResult, DetectionResult, TelemetrySnapshot


class OptionalLLMAgent:
    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
        self.api_key = os.getenv("OLLAMA_API_KEY", "")

    def summarize(
        self,
        snapshot: TelemetrySnapshot,
        detection: DetectionResult,
        diagnosis: DiagnosisResult,
    ) -> tuple[str, str]:
        prompt = self._build_prompt(snapshot, detection, diagnosis)
        if not self.model:
            return ("LLM disabled: no model configured, deterministic fallback mode active.", "disabled")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a conservative thermal power plant assistant. "
                        "Never recommend bypassing trips, overriding interlocks, or increasing fuel during unsafe states. "
                        "Summarize only the present engineering condition and safe next action in 3 sentences or less."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            request = urllib.request.Request(
                f"{self.base_url}/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                body = json.loads(response.read().decode("utf-8"))
            message = body.get("message", {}).get("content", "").strip()
            if message:
                return (message, f"ollama:{self.model}")
            return ("LLM returned an empty summary, deterministic fallback mode active.", "fallback")
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return (f"LLM unavailable: {exc}. Deterministic fallback mode active.", "fallback")

    def _build_prompt(
        self,
        snapshot: TelemetrySnapshot,
        detection: DetectionResult,
        diagnosis: DiagnosisResult,
    ) -> str:
        return (
            f"Mode: {snapshot.anomaly_mode}\n"
            f"Telemetry: {snapshot.values}\n"
            f"Current control state: {snapshot.control_state}\n"
            f"Severity: {detection.severity}\n"
            f"Anomalies: {detection.anomalies}\n"
            f"Interlocks: {detection.triggered_interlocks}\n"
            f"Diagnosis: {diagnosis.summary}\n"
            f"Likely causes: {diagnosis.likely_causes}\n"
            f"Safe actions: {diagnosis.recommended_actions}\n"
        )
