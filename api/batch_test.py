"""
batch_test.py — 200-call model benchmark
=========================================
Sends 50 identical sensor-reading payloads to every registered model
(4 models × 50 samples = 200 POST /predict calls), then produces a
side-by-side comparison report covering:

  • Per-model prediction / probability statistics
  • Cross-model agreement rate
  • Samples where models disagree
  • Confidence distribution (high / medium / low)

Usage (with API running on localhost:8000):
    python -m api.batch_test
    python -m api.batch_test --url http://127.0.0.1:8000 --timeout 10
    python -m api.batch_test --output results.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Any

# Force UTF-8 output on Windows (avoids UnicodeEncodeError for box-drawing chars)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 50 fixed test payloads
# Spread across 4 categories: healthy, moderate stress, high-risk, borderline
# ─────────────────────────────────────────────────────────────────────────────
TEST_PAYLOADS: list[dict[str, Any]] = [
    # ── healthy / normal operating range ─────────────────────────────────────
    {"machine_type": "CNC",         "vibration_rms": 1.2,  "temperature_motor": 65.0,  "current_phase_avg": 10.1, "pressure_level": 2.8, "rpm": 1450, "operating_mode": "normal", "hours_since_maintenance": 50,  "ambient_temp": 22.0},
    {"machine_type": "CNC",         "vibration_rms": 0.9,  "temperature_motor": 60.0,  "current_phase_avg":  9.5, "pressure_level": 2.5, "rpm": 1500, "operating_mode": "normal", "hours_since_maintenance": 30,  "ambient_temp": 21.0},
    {"machine_type": "Compressor",  "vibration_rms": 1.5,  "temperature_motor": 68.0,  "current_phase_avg": 11.0, "pressure_level": 3.0, "rpm": 1200, "operating_mode": "normal", "hours_since_maintenance": 80,  "ambient_temp": 23.5},
    {"machine_type": "Compressor",  "vibration_rms": 1.1,  "temperature_motor": 62.0,  "current_phase_avg": 10.5, "pressure_level": 2.7, "rpm": 1300, "operating_mode": "normal", "hours_since_maintenance": 60,  "ambient_temp": 20.0},
    {"machine_type": "Pump",        "vibration_rms": 1.3,  "temperature_motor": 66.0,  "current_phase_avg": 10.8, "pressure_level": 2.9, "rpm": 1400, "operating_mode": "normal", "hours_since_maintenance": 45,  "ambient_temp": 22.5},
    {"machine_type": "Pump",        "vibration_rms": 0.8,  "temperature_motor": 58.0,  "current_phase_avg":  9.0, "pressure_level": 2.4, "rpm": 1550, "operating_mode": "normal", "hours_since_maintenance": 20,  "ambient_temp": 19.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 1.0,  "temperature_motor": 63.0,  "current_phase_avg":  9.8, "pressure_level": 2.6, "rpm": 1350, "operating_mode": "normal", "hours_since_maintenance": 70,  "ambient_temp": 21.5},
    {"machine_type": "Robotic Arm", "vibration_rms": 1.4,  "temperature_motor": 67.0,  "current_phase_avg": 10.3, "pressure_level": 2.8, "rpm": 1420, "operating_mode": "normal", "hours_since_maintenance": 55,  "ambient_temp": 23.0},
    {"machine_type": "CNC",         "vibration_rms": 1.6,  "temperature_motor": 70.0,  "current_phase_avg": 11.5, "pressure_level": 3.1, "rpm": 1480, "operating_mode": "idle",   "hours_since_maintenance": 90,  "ambient_temp": 24.0},
    {"machine_type": "Compressor",  "vibration_rms": 1.7,  "temperature_motor": 72.0,  "current_phase_avg": 11.8, "pressure_level": 3.2, "rpm": 1250, "operating_mode": "idle",   "hours_since_maintenance": 100, "ambient_temp": 25.0},

    # ── moderate stress ───────────────────────────────────────────────────────
    {"machine_type": "CNC",         "vibration_rms": 2.3,  "temperature_motor": 78.0,  "current_phase_avg": 13.0, "pressure_level": 3.5, "rpm": 1450, "operating_mode": "normal", "hours_since_maintenance": 150, "ambient_temp": 26.0},
    {"machine_type": "Compressor",  "vibration_rms": 2.5,  "temperature_motor": 80.0,  "current_phase_avg": 13.5, "pressure_level": 3.7, "rpm": 1200, "operating_mode": "normal", "hours_since_maintenance": 170, "ambient_temp": 27.0},
    {"machine_type": "Pump",        "vibration_rms": 2.8,  "temperature_motor": 82.0,  "current_phase_avg": 14.0, "pressure_level": 3.9, "rpm": 1380, "operating_mode": "normal", "hours_since_maintenance": 200, "ambient_temp": 28.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 2.1,  "temperature_motor": 76.0,  "current_phase_avg": 12.5, "pressure_level": 3.4, "rpm": 1320, "operating_mode": "idle",   "hours_since_maintenance": 140, "ambient_temp": 25.5},
    {"machine_type": "CNC",         "vibration_rms": 2.6,  "temperature_motor": 81.0,  "current_phase_avg": 13.8, "pressure_level": 3.8, "rpm": 1460, "operating_mode": "idle",   "hours_since_maintenance": 180, "ambient_temp": 27.5},
    {"machine_type": "Compressor",  "vibration_rms": 2.0,  "temperature_motor": 75.0,  "current_phase_avg": 12.2, "pressure_level": 3.3, "rpm": 1270, "operating_mode": "normal", "hours_since_maintenance": 130, "ambient_temp": 24.5},
    {"machine_type": "Pump",        "vibration_rms": 2.4,  "temperature_motor": 79.0,  "current_phase_avg": 13.2, "pressure_level": 3.6, "rpm": 1395, "operating_mode": "normal", "hours_since_maintenance": 160, "ambient_temp": 26.5},
    {"machine_type": "Robotic Arm", "vibration_rms": 2.9,  "temperature_motor": 83.0,  "current_phase_avg": 14.5, "pressure_level": 4.0, "rpm": 1340, "operating_mode": "idle",   "hours_since_maintenance": 210, "ambient_temp": 28.5},
    {"machine_type": "CNC",         "vibration_rms": 2.2,  "temperature_motor": 77.0,  "current_phase_avg": 12.8, "pressure_level": 3.5, "rpm": 1470, "operating_mode": "normal", "hours_since_maintenance": 145, "ambient_temp": 26.0},
    {"machine_type": "Compressor",  "vibration_rms": 2.7,  "temperature_motor": 81.5,  "current_phase_avg": 14.2, "pressure_level": 3.8, "rpm": 1230, "operating_mode": "idle",   "hours_since_maintenance": 190, "ambient_temp": 27.0},

    # ── high risk / likely failure ────────────────────────────────────────────
    {"machine_type": "CNC",         "vibration_rms": 5.2,  "temperature_motor": 98.0,  "current_phase_avg": 18.5, "pressure_level": 5.5, "rpm": 1600, "operating_mode": "peak",   "hours_since_maintenance": 400, "ambient_temp": 34.0},
    {"machine_type": "Compressor",  "vibration_rms": 6.1,  "temperature_motor": 99.0,  "current_phase_avg": 19.8, "pressure_level": 6.0, "rpm": 1700, "operating_mode": "peak",   "hours_since_maintenance": 450, "ambient_temp": 36.0},
    {"machine_type": "Pump",        "vibration_rms": 5.8,  "temperature_motor": 99.5,  "current_phase_avg": 19.2, "pressure_level": 5.8, "rpm": 1650, "operating_mode": "peak",   "hours_since_maintenance": 420, "ambient_temp": 35.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 4.9,  "temperature_motor": 95.0,  "current_phase_avg": 17.8, "pressure_level": 5.2, "rpm": 1580, "operating_mode": "peak",   "hours_since_maintenance": 380, "ambient_temp": 33.0},
    {"machine_type": "CNC",         "vibration_rms": 6.5,  "temperature_motor": 99.0,  "current_phase_avg": 20.5, "pressure_level": 6.3, "rpm": 1720, "operating_mode": "peak",   "hours_since_maintenance": 500, "ambient_temp": 38.0},
    {"machine_type": "Compressor",  "vibration_rms": 5.5,  "temperature_motor": 99.0,  "current_phase_avg": 18.9, "pressure_level": 5.7, "rpm": 1680, "operating_mode": "peak",   "hours_since_maintenance": 430, "ambient_temp": 35.5},
    {"machine_type": "Pump",        "vibration_rms": 7.0,  "temperature_motor": 99.5,  "current_phase_avg": 21.0, "pressure_level": 6.5, "rpm": 1750, "operating_mode": "peak",   "hours_since_maintenance": 520, "ambient_temp": 39.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 5.0,  "temperature_motor": 97.0,  "current_phase_avg": 18.0, "pressure_level": 5.4, "rpm": 1620, "operating_mode": "peak",   "hours_since_maintenance": 390, "ambient_temp": 33.5},
    {"machine_type": "CNC",         "vibration_rms": 4.5,  "temperature_motor": 93.0,  "current_phase_avg": 17.0, "pressure_level": 5.0, "rpm": 1560, "operating_mode": "peak",   "hours_since_maintenance": 360, "ambient_temp": 32.0},
    {"machine_type": "Compressor",  "vibration_rms": 6.8,  "temperature_motor": 99.5,  "current_phase_avg": 20.8, "pressure_level": 6.4, "rpm": 1740, "operating_mode": "peak",   "hours_since_maintenance": 510, "ambient_temp": 38.5},

    # ── borderline / ambiguous ────────────────────────────────────────────────
    {"machine_type": "CNC",         "vibration_rms": 3.2,  "temperature_motor": 86.0,  "current_phase_avg": 15.0, "pressure_level": 4.2, "rpm": 1490, "operating_mode": "normal", "hours_since_maintenance": 250, "ambient_temp": 29.0},
    {"machine_type": "Compressor",  "vibration_rms": 3.5,  "temperature_motor": 88.0,  "current_phase_avg": 15.8, "pressure_level": 4.5, "rpm": 1260, "operating_mode": "idle",   "hours_since_maintenance": 280, "ambient_temp": 30.0},
    {"machine_type": "Pump",        "vibration_rms": 3.0,  "temperature_motor": 84.0,  "current_phase_avg": 14.8, "pressure_level": 4.1, "rpm": 1410, "operating_mode": "normal", "hours_since_maintenance": 230, "ambient_temp": 28.5},
    {"machine_type": "Robotic Arm", "vibration_rms": 3.8,  "temperature_motor": 90.0,  "current_phase_avg": 16.2, "pressure_level": 4.7, "rpm": 1360, "operating_mode": "idle",   "hours_since_maintenance": 300, "ambient_temp": 31.0},
    {"machine_type": "CNC",         "vibration_rms": 4.0,  "temperature_motor": 92.0,  "current_phase_avg": 16.8, "pressure_level": 4.9, "rpm": 1510, "operating_mode": "normal", "hours_since_maintenance": 320, "ambient_temp": 31.5},
    {"machine_type": "Compressor",  "vibration_rms": 3.3,  "temperature_motor": 87.0,  "current_phase_avg": 15.3, "pressure_level": 4.3, "rpm": 1280, "operating_mode": "normal", "hours_since_maintenance": 260, "ambient_temp": 29.5},
    {"machine_type": "Pump",        "vibration_rms": 4.2,  "temperature_motor": 93.0,  "current_phase_avg": 17.2, "pressure_level": 5.1, "rpm": 1430, "operating_mode": "idle",   "hours_since_maintenance": 340, "ambient_temp": 32.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 3.6,  "temperature_motor": 89.0,  "current_phase_avg": 15.9, "pressure_level": 4.6, "rpm": 1380, "operating_mode": "normal", "hours_since_maintenance": 290, "ambient_temp": 30.5},
    {"machine_type": "CNC",         "vibration_rms": 3.9,  "temperature_motor": 91.0,  "current_phase_avg": 16.5, "pressure_level": 4.8, "rpm": 1500, "operating_mode": "idle",   "hours_since_maintenance": 310, "ambient_temp": 31.0},
    {"machine_type": "Compressor",  "vibration_rms": 4.1,  "temperature_motor": 92.5,  "current_phase_avg": 17.0, "pressure_level": 5.0, "rpm": 1290, "operating_mode": "peak",   "hours_since_maintenance": 330, "ambient_temp": 32.5},

    # ── mixed: idle-mode wear + fresh maintenance ─────────────────────────────
    {"machine_type": "Pump",        "vibration_rms": 1.8,  "temperature_motor": 73.0,  "current_phase_avg": 12.0, "pressure_level": 3.2, "rpm": 1420, "operating_mode": "idle",   "hours_since_maintenance": 10,  "ambient_temp": 22.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 2.0,  "temperature_motor": 74.0,  "current_phase_avg": 12.3, "pressure_level": 3.3, "rpm": 1440, "operating_mode": "idle",   "hours_since_maintenance": 15,  "ambient_temp": 23.0},
    {"machine_type": "CNC",         "vibration_rms": 3.7,  "temperature_motor": 89.5,  "current_phase_avg": 16.0, "pressure_level": 4.5, "rpm": 1480, "operating_mode": "peak",   "hours_since_maintenance": 5,   "ambient_temp": 27.0},
    {"machine_type": "Compressor",  "vibration_rms": 4.4,  "temperature_motor": 94.0,  "current_phase_avg": 17.5, "pressure_level": 5.2, "rpm": 1310, "operating_mode": "peak",   "hours_since_maintenance": 350, "ambient_temp": 30.0},
    {"machine_type": "Pump",        "vibration_rms": 1.9,  "temperature_motor": 71.0,  "current_phase_avg": 11.8, "pressure_level": 3.1, "rpm": 1460, "operating_mode": "normal", "hours_since_maintenance": 25,  "ambient_temp": 21.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 5.3,  "temperature_motor": 97.5,  "current_phase_avg": 18.2, "pressure_level": 5.5, "rpm": 1640, "operating_mode": "peak",   "hours_since_maintenance": 410, "ambient_temp": 34.5},
    {"machine_type": "CNC",         "vibration_rms": 1.0,  "temperature_motor": 61.0,  "current_phase_avg":  9.7, "pressure_level": 2.6, "rpm": 1530, "operating_mode": "normal", "hours_since_maintenance": 5,   "ambient_temp": 20.5},
    {"machine_type": "Compressor",  "vibration_rms": 6.3,  "temperature_motor": 99.0,  "current_phase_avg": 20.0, "pressure_level": 6.1, "rpm": 1710, "operating_mode": "peak",   "hours_since_maintenance": 480, "ambient_temp": 37.0},
    {"machine_type": "Pump",        "vibration_rms": 3.1,  "temperature_motor": 85.0,  "current_phase_avg": 14.9, "pressure_level": 4.2, "rpm": 1400, "operating_mode": "idle",   "hours_since_maintenance": 240, "ambient_temp": 29.0},
    {"machine_type": "Robotic Arm", "vibration_rms": 2.4,  "temperature_motor": 77.0,  "current_phase_avg": 13.0, "pressure_level": 3.5, "rpm": 1370, "operating_mode": "normal", "hours_since_maintenance": 120, "ambient_temp": 25.0},
]


MODELS = ["rf", "lr", "voting_classifier", "dl"]
N_SAMPLES = len(TEST_PAYLOADS)


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CallResult:
    sample_idx: int
    model_alias: str
    canonical_name: str
    prediction: int
    probability: float
    label: str
    latency_ms: float


@dataclass
class ModelStats:
    alias: str
    canonical_name: str
    failure_count: int = 0
    no_failure_count: int = 0
    probabilities: list[float] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)
    errors: int = 0

    @property
    def total(self) -> int:
        return self.failure_count + self.no_failure_count

    @property
    def failure_rate(self) -> float:
        return self.failure_count / self.total if self.total else 0.0

    @property
    def avg_prob(self) -> float:
        return mean(self.probabilities) if self.probabilities else 0.0

    @property
    def std_prob(self) -> float:
        return stdev(self.probabilities) if len(self.probabilities) > 1 else 0.0

    @property
    def avg_latency(self) -> float:
        return mean(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def high_conf(self) -> int:
        """Samples where probability >= 0.75 (failure) or <= 0.25 (no-failure)."""
        return sum(1 for p in self.probabilities if p >= 0.75 or p <= 0.25)

    @property
    def medium_conf(self) -> int:
        return sum(1 for p in self.probabilities if 0.40 <= p < 0.75 and p > 0.25)

    @property
    def low_conf(self) -> int:
        return sum(1 for p in self.probabilities if 0.25 < p < 0.40)


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helper (stdlib only — no requests / httpx needed)
# ─────────────────────────────────────────────────────────────────────────────

def post_json(url: str, body: dict, timeout: float) -> tuple[dict, float]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        latency_ms = (time.perf_counter() - t0) * 1000
        return json.loads(resp.read()), latency_ms


# ─────────────────────────────────────────────────────────────────────────────
# Batch runner
# ─────────────────────────────────────────────────────────────────────────────

def run_batch(base_url: str, timeout: float) -> tuple[list[CallResult], dict[str, ModelStats]]:
    predict_url = f"{base_url.rstrip('/')}/predict"
    results: list[CallResult] = []
    stats: dict[str, ModelStats] = {}

    total_calls = len(MODELS) * N_SAMPLES
    done = 0

    for alias in MODELS:
        stats[alias] = ModelStats(alias=alias, canonical_name="")
        print(f"\n  ── Model: {alias} ──────────────────────────────────────────")
        for idx, payload in enumerate(TEST_PAYLOADS):
            body = {"model": alias, "features": payload}
            done += 1
            progress = f"[{done:>3}/{total_calls}]"
            try:
                resp, latency = post_json(predict_url, body, timeout)
                canonical = resp.get("model", alias)
                prediction = int(resp.get("prediction", -1))
                probability = float(resp.get("probability", 0.0))
                label = resp.get("label", "unknown")

                stats[alias].canonical_name = canonical
                stats[alias].failure_count += prediction
                stats[alias].no_failure_count += 1 - prediction
                stats[alias].probabilities.append(probability)
                stats[alias].latencies_ms.append(latency)

                results.append(
                    CallResult(
                        sample_idx=idx,
                        model_alias=alias,
                        canonical_name=canonical,
                        prediction=prediction,
                        probability=probability,
                        label=label,
                        latency_ms=latency,
                    )
                )
                flag = "[FAIL]" if prediction else "[ok]  "
                print(f"  {progress} sample={idx+1:>2}  {flag}  prob={probability:.3f}  ({latency:.0f} ms)")
            except Exception as exc:
                stats[alias].errors += 1
                print(f"  {progress} sample={idx+1:>2}  [!] ERROR: {exc}")

    return results, stats


# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────

def print_report(results: list[CallResult], stats: dict[str, ModelStats]) -> None:
    SEP = "─" * 82
    DSEP = "═" * 82

    print(f"\n{DSEP}")
    print("  MODEL BENCHMARK REPORT  —  50 samples × 4 models = 200 calls")
    print(DSEP)

    # ── per-model summary ────────────────────────────────────────────────────
    print(f"\n{'MODEL':<12} {'CANONICAL':<26} {'FAILURES':>8} {'FAIL %':>7} "
          f"{'AVG PROB':>9} {'STD PROB':>9} {'AVG MS':>8} {'ERRORS':>7}")
    print(SEP)
    for alias, s in stats.items():
        print(f"{alias:<12} {s.canonical_name:<26} {s.failure_count:>8} "
              f"{s.failure_rate * 100:>6.1f}%  "
              f"{s.avg_prob:>9.4f}  {s.std_prob:>9.4f}  "
              f"{s.avg_latency:>6.0f} ms  {s.errors:>6}")

    # ── confidence distribution ──────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  CONFIDENCE DISTRIBUTION")
    print(f"  High  : prob >= 0.75 (failure) or <= 0.25 (no-failure) — model is decisive")
    print(f"  Medium: 0.40–0.75")
    print(f"  Low   : 0.25–0.40 — model is uncertain")
    print(SEP)
    print(f"{'MODEL':<12} {'HIGH CONF':>10} {'MED CONF':>10} {'LOW CONF':>10}  {'HIGH%':>7}")
    print(SEP)
    for alias, s in stats.items():
        high_pct = s.high_conf / N_SAMPLES * 100
        print(f"{alias:<12} {s.high_conf:>9}  {s.medium_conf:>9}  {s.low_conf:>9}  {high_pct:>6.1f}%")

    # ── cross-model agreement ────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  CROSS-MODEL AGREEMENT PER SAMPLE")
    print(SEP)

    pred_map: dict[int, dict[str, int]] = {i: {} for i in range(N_SAMPLES)}
    for r in results:
        pred_map[r.sample_idx][r.model_alias] = r.prediction

    all_agree = 0
    three_one = 0
    split_50 = 0
    disagree_rows: list[tuple[int, dict[str, int]]] = []

    for idx, preds in pred_map.items():
        if len(preds) < len(MODELS):
            continue
        votes = list(preds.values())
        fail_votes = sum(votes)
        if fail_votes == 0 or fail_votes == len(MODELS):
            all_agree += 1
        elif fail_votes == len(MODELS) - 1 or fail_votes == 1:
            three_one += 1
            disagree_rows.append((idx, preds))
        else:
            split_50 += 1
            disagree_rows.append((idx, preds))

    total_complete = all_agree + three_one + split_50
    print(f"  All 4 agree          : {all_agree:>3} / {total_complete}  ({all_agree/total_complete*100:.1f}%)")
    print(f"  3 vs 1 majority      : {three_one:>3} / {total_complete}  ({three_one/total_complete*100:.1f}%)")
    print(f"  50 / 50 split (2-2)  : {split_50:>3} / {total_complete}  ({split_50/total_complete*100:.1f}%)")

    # ── disagreement detail ──────────────────────────────────────────────────
    if disagree_rows:
        print(f"\n{SEP}")
        print("  SAMPLES WHERE MODELS DISAGREE (first 25 shown)")
        print(SEP)
        header = f"{'#':>4}  " + "  ".join(f"{m:<10}" for m in MODELS) + "  MACHINE   MODE        VIB   TEMP   HRS"
        print(header)
        print(SEP)
        for idx, preds in disagree_rows[:25]:
            p = TEST_PAYLOADS[idx]
            row = f"{idx+1:>4}  "
            row += "  ".join(
                f"{'FAIL' if preds.get(m, -1) == 1 else 'ok  ':<10}"
                for m in MODELS
            )
            row += (f"  {p['machine_type']:<8}  {p['operating_mode']:<10}"
                    f"  {p['vibration_rms']:>4.1f}  {p['temperature_motor']:>5.1f}"
                    f"  {p['hours_since_maintenance']:>4}")
            print(row)
        if len(disagree_rows) > 25:
            print(f"  ... and {len(disagree_rows) - 25} more disagreements")

    # ── recommendation ───────────────────────────────────────────────────────
    print(f"\n{DSEP}")
    print("  RECOMMENDATION")
    print(DSEP)

    all_failure_rates = [s.failure_rate for s in stats.values()]
    rates_sorted = sorted(all_failure_rates)
    median_rate = (rates_sorted[1] + rates_sorted[2]) / 2

    # Score: maximise high-confidence predictions; penalise distance from median failure rate
    ranked = sorted(
        stats.values(),
        key=lambda s: (-s.high_conf, abs(s.failure_rate - median_rate), s.avg_latency),
    )

    print(f"\n  Median failure rate across models: {median_rate*100:.1f}%")
    print(f"  Ranked by: high-confidence count (desc) → alignment with median → latency\n")
    for rank, s in enumerate(ranked, 1):
        badge = " [BEST]" if rank == 1 else ""
        print(f"  {rank}. [{s.alias:<10}]  {s.canonical_name:<26}  "
              f"high_conf={s.high_conf:>2}/50  fail_rate={s.failure_rate*100:>5.1f}%  "
              f"avg_ms={s.avg_latency:>5.0f}{badge}")

    print(f"\n{DSEP}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Batch benchmark — 50 samples × 4 models = 200 calls")
    parser.add_argument("--url",     default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--timeout", default=15.0, type=float,        help="Per-request timeout in seconds")
    parser.add_argument("--output",  default=None,                    help="Save raw results to a JSON file")
    args = parser.parse_args()

    print(f"\n[*] Batch benchmark — {args.url}")
    print(f"    Models  : {', '.join(MODELS)}")
    print(f"    Samples : {N_SAMPLES} per model  ({N_SAMPLES * len(MODELS)} total calls)")

    # Quick health check
    try:
        req = urllib.request.Request(f"{args.url.rstrip('/')}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            health = json.loads(resp.read())
        print(f"    Status  : {health.get('status', '?')}")
        print(f"    Loaded  : {', '.join(health.get('models_loaded', []))}")
    except Exception as exc:
        print(f"\n  [!] Could not reach API at {args.url}: {exc}")
        print("     Start uvicorn first, then retry.\n")
        sys.exit(1)

    results, stats = run_batch(args.url, args.timeout)

    if args.output:
        raw = {
            "meta": {"url": args.url, "models": MODELS, "n_samples": N_SAMPLES},
            "results": [
                {
                    "sample": r.sample_idx + 1,
                    "model": r.model_alias,
                    "canonical": r.canonical_name,
                    "prediction": r.prediction,
                    "probability": r.probability,
                    "label": r.label,
                    "latency_ms": round(r.latency_ms, 2),
                }
                for r in results
            ],
        }
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2)
        print(f"\n  [+] Raw results saved to: {args.output}")

    print_report(results, stats)


if __name__ == "__main__":
    main()
