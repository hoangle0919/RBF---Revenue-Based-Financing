"""Simulation Lab — serves registered research artifacts to the UI.

RULES THIS MODULE ENFORCES, because the UI cannot be trusted to:

  * Every number originates in a committed, checksummed artifact under
    `research/results/`. Nothing here computes a research finding, and nothing
    is transcribed by hand.
  * Every artifact ships with its checksum and spec version.
  * Every conclusion carries a CLAIM CLASSIFICATION. A proof and a simulation
    output are different kinds of evidence and must not be displayed alike.
  * Every rate carries its BASIS — reference-path or mean-across-simulated-paths.
    They are different quantities and the design audit found the page conflating
    them (D-033).
  * Every recovery figure carries its DENOMINATOR. The amortizing loan has no
    contractual cap; its denominator is scheduled total repayment.
  * Contractual money is integer đồng via `money.py`. The frontend receives
    formatted values and performs no financial arithmetic.
  * RBF-G is absent from every public surface (D-018).
  * Colour is CATEGORICAL, never valenced. The API emits a palette key; it does
    not emit "good" or "bad".

FOUR ARTIFACTS, TWO PRICE TRACKS. Ten ordinary scenarios and three closure
scenarios, each priced at the illustrative f = 1.20 and at the reference-path
cost-matched f* = 1.0945. A scenario is resolved against whichever artifact in
its track contains it.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from money import to_vnd

RESEARCH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "research", "results")

# ── claim taxonomy ──────────────────────────────────────────────────────────

CLAIM_TAXONOMY = {
    "mathematical_property": {
        "label": "Mathematical property",
        "meaning": "Holds for any revenue path, by proof. Independent of the "
                   "simulation, the parameters, and any distributional "
                   "assumption. See research/DERIVATIONS.md.",
        "strength": "strongest",
    },
    "simulation_result": {
        "label": "Simulation result",
        "meaning": "Measured on simulated revenue paths under the frozen "
                   "methodology, FOR THE SELECTED SCENARIO. Describes the model, "
                   "not observed sellers, and does not generalise to other "
                   "scenarios.",
        "strength": "conditional on the scenario and the generative assumptions",
    },
    "sensitivity_result": {
        "label": "Sensitivity result",
        "meaning": "How an output moves when a parameter is swept. Shows what "
                   "the conclusion depends on, not that the parameter is right.",
        "strength": "conditional on the swept range",
    },
    "product_implication": {
        "label": "Product implication",
        "meaning": "A design consequence the author draws from the above. A "
                   "judgement, not a measurement.",
        "strength": "author's inference",
    },
    "open_real_world_question": {
        "label": "Open real-world question",
        "meaning": "Cannot be settled by this project. Requires observed seller "
                   "revenue and adjudicated repayment outcomes, which do not "
                   "exist here.",
        "strength": "unresolved",
    },
}

# ── glossary (D-033: specialist labels were unexplained in place) ───────────

GLOSSARY = {
    "cap factor": "The multiple of the advance that the seller repays in total. "
                  "A cap factor of 1.20 on a 100M advance means 120M repaid.",
    "contractual cap": "The total amount repayable — advance × cap factor. "
                       "Collection stops when it is reached.",
    "remittance": "The share of each month's revenue that goes to the financier. "
                  "Fixed as a percentage; the amount moves with revenue.",
    "effective APR": "The annualised internal rate of return of the payment "
                     "stream against the advance. It puts a revenue share and a "
                     "fixed instalment on one axis.",
    "payment burden": "Payment ÷ GMV in a given month — the share of that "
                      "month's gross takings that leaves as a payment. The "
                      "contract charges its share on NET sales, so this equals "
                      "r·(1 − return rate) and varies when returns vary.",
    "90th percentile": "The value exceeded in only 10% of active months. It "
                       "describes a bad month, not a typical one.",
    "Monte Carlo interval": "A range showing whether enough simulated paths were "
                            "run for a number to be stable. It is NOT a "
                            "confidence interval and says nothing about real "
                            "sellers.",
    "canonical artifact": "A committed, checksummed result file. Identical code, "
                          "configuration and seeds reproduce it byte-for-byte "
                          "within a fixed runtime, and numerically at published "
                          "precision on every platform tested — so any figure "
                          "here can be traced to a verifiable file.",
    "reference path": "A flat, shock-free revenue path used once to price the "
                      "fixed benchmark. Contracts are priced at origination, so "
                      "a later shock cannot retro-price them.",
}

# ── scenarios (prose, not research numbers) ─────────────────────────────────

SCENARIOS: Dict[str, dict] = {
    "stable":            {"label": "Stable revenue", "family": "baseline", "order": 1,
                          "description": "Flat seasonality, no growth, no shock. The reference case."},
    "seasonal":          {"label": "Moderate seasonality", "family": "baseline", "order": 2,
                          "description": "Ordinary seasonal swing around a flat trend."},
    "seasonal_strong":   {"label": "Strong seasonality", "family": "baseline", "order": 3,
                          "description": "Pronounced peaks and troughs. The shape is a "
                                         "specified input, not an observed category "
                                         "pattern; no category data informs it."},
    "growth":            {"label": "Growth", "family": "favourable", "order": 4,
                          "description": "3% month-on-month growth with moderate seasonality."},
    "gradual_decline":   {"label": "Gradual decline", "family": "stress", "order": 5,
                          "description": "Revenue steps down toward −40% over six months, then holds."},
    "sustained_decline": {"label": "Sustained decline", "family": "stress", "order": 6,
                          "description": "An immediate, permanent drop to 60% of prior revenue."},
    "severe_downturn":   {"label": "Severe downturn", "family": "stress", "order": 7,
                          "description": "−60% for six months, then a six-month recovery."},
    "disruption_1m":     {"label": "One-month disruption", "family": "stress", "order": 8,
                          "description": "A single month at half revenue, then full recovery."},
    "platform_outage":   {"label": "Platform outage", "family": "stress", "order": 9,
                          "description": "A single month at 30% of revenue — a marketplace suspension."},
    "returns_spike":     {"label": "Returns spike", "family": "stress", "order": 10,
                          "description": "Elevated returns reduce net sales without reducing gross orders."},
    "closure_m7":        {"label": "Closure, month 7", "family": "closure", "order": 11,
                          "description": "The business closes permanently in month 7. Revenue is zero "
                                         "from then on and never recovers."},
    "closure_m13":       {"label": "Closure, month 13", "family": "closure", "order": 12,
                          "description": "Permanent closure in month 13, after most of the term has "
                                         "already been repaid."},
    "temp_closure":      {"label": "Temporary closure", "family": "closure", "order": 13,
                          "description": "Three months at zero revenue, then partial recovery to 50%."},
}

#: A scenario is looked up in its track, first artifact that has it.
TRACKS = {
    "illustrative": ["baseline_v3", "baseline_closure_v2"],
    "cost_matched": ["baseline_equalcost_v2", "baseline_closure_equalcost_v2"],
}

ARMS = [
    {"id": "FIX-A", "track": "illustrative", "arm": "FIX-A", "palette": "fixed-a",
     "name": "Fixed payment — cost-matched",
     "short": "Fixed payment",
     "chart_label": "Fixed payment",
     "kind": "fixed",
     "note": "Same principal, same total repayment and same term as the "
             "illustrative revenue-based contract on the reference path. Only "
             "the TIMING of payments differs, which is what isolates the "
             "comparison."},
    {"id": "FIX-B", "track": "illustrative", "arm": "FIX-B", "palette": "fixed-b",
     "name": "Amortizing loan — 18% nominal",
     "short": "Amortizing loan",
     "chart_label": "Amortizing loan",
     "kind": "fixed",
     "note": "An illustrative 12-month amortizing loan at 18% nominal annual "
             "rate. The 18% is an assumption chosen for this study — not a "
             "market rate, and not observed or externally sourced anywhere in "
             "this project. Not cost-matched; it is the external price "
             "reference."},
    {"id": "RBF-EQ", "track": "cost_matched", "arm": "RBF", "palette": "rbf-ref",
     "name": "Reference-path cost-matched RBF",
     "short": "Revenue-based, cost-matched",
     # Built from the artifact's own cap factor. It used to read "1.0945×",
     # hand-typed, which would have gone stale silently if a sweep ever moved.
     "chart_label_fmt": "Revenue-based {f}×",
     "kind": "rbf",
     # Prefixed at request time with the grid-residual sentence, so the exactness
     # of the match is stated from the artifact rather than asserted.
     "note_grid": True,
     "note": "The cap factor was chosen on THE REFERENCE PATH — a flat, "
             "shock-free path used once at pricing time. On simulated paths the "
             "realised rate differs again, because duration moves with revenue. "
             "The name describes how the price was set, not an outcome "
             "guaranteed on any path."},
    {"id": "RBF-ILL", "track": "illustrative", "arm": "RBF", "palette": "rbf-ill",
     "name": "Illustrative RBF (cap factor 1.20)",
     "short": "Revenue-based, illustrative",
     "chart_label_fmt": "Revenue-based {f}×",
     "kind": "rbf",
     "note": "An ILLUSTRATIVE cap factor, not a recommended or market price. "
             "Its higher cost is a property of choosing 1.20, not of "
             "revenue-based repayment."},
]

# Short reader-facing references used inside composed sentences. FIX-A and
# RBF-ILL are internal identifiers; a sentence that compares two of four arms
# has to name which two in words a first-time reader can follow, with the id
# kept as a secondary reference.
def _target_vnd(arm: dict):
    """The arm's repayment target in VND, or None if it has no structured one."""
    t = arm.get("repayment_target")
    if isinstance(t, dict) and isinstance(t.get("amount"), dict):
        return t["amount"].get("vnd")
    return None


FIX_A_REF = "the cost-matched fixed payment (FIX-A)"
RBF_ILL_REF = "the illustrative revenue-based contract (RBF-ILL)"

_CACHE: Dict[str, dict] = {}


# ── Presentation localization (F7) ───────────────────────────────────────────
# Additive only. Every existing English field keeps its exact value and meaning;
# a sibling `<field>_key` names the catalogue entry a localized client should
# prefer, and `<field>_params` / `<field>_param_keys` carry the interpolation
# values for prose that contains scenario-dependent numbers. Numbers are NEVER
# frozen into a catalogue string -- they travel as parameters, so a translated
# finding cannot drift from the artifact it describes.
#
# Identifiers, source paths, checksums, spec versions and money `display`
# strings are deliberately NOT keyed: they are data, not prose.

def _k(obj: dict, field: str, key: str) -> dict:
    """Attach a translation key beside an existing prose field."""
    if obj.get(field) is not None:
        obj[f"{field}_key"] = key
    return obj


def _load(stem: str) -> Optional[dict]:
    if stem in _CACHE:
        return _CACHE[stem]
    path = os.path.join(RESEARCH, f"{stem}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        _CACHE[stem] = json.load(fh)
    return _CACHE[stem]


def _checksum(stem: str) -> Optional[str]:
    prov = _load(f"{stem}_provenance")
    return prov.get("canonical_sha256") if prov else None


def _grid_pricing() -> dict:
    """Reference-path pricing, read from the CANONICAL validation artifact.

    `f*` is not solved analytically. `run_validation.py` sweeps a cap-factor
    grid in steps of 0.0005 and keeps the point whose reference-path effective
    rate lands closest to the amortizing loan's. So the residual is a **grid
    resolution** result: the registered value is the nearest point *the search
    visited*.

    **The residual is NOT evidence that an exact match is unattainable
    (D-056).** Within an interval where the paying-month count stays fixed, the
    terminal payment is clipped to the residue of the cap and therefore varies
    continuously with `f` — so the effective APR varies continuously too. A
    numerical root exists on the reference path at approximately
    `f = 1.09462066267694`. Changes in the paying-month count create kinks in
    that relationship; they do not create the universal gaps once claimed here.

    This docstring previously said "duration is an integer, so cost moves in
    steps and an exact match is not generally attainable". That reasoning is
    **withdrawn** — it confused a kink with a gap. Before that, the Lab said
    "equals", which promised an exact match the search never performed.

    Every number here is READ FROM THE ARTIFACT. None is hand-typed, so the
    residual cannot drift away from the file it describes, and if a future sweep
    lands exactly on target the wording follows automatically.
    """
    body = _load("validation_v2_canonical") or {}
    pricing = body.get("pricing") or {}
    ec = pricing.get("equal_cost") or {}
    achieved, target = ec.get("apr"), pricing.get("benchmark_b_apr")
    exact = (achieved is not None and target is not None and achieved == target)
    return {
        "f_star": ec.get("f_star"),
        "achieved_apr": achieved,
        "benchmark_apr": target,
        "residual_pp": (None if achieved is None or target is None
                        else abs(target - achieved) * 100.0),
        "exact_match": exact,
        "basis": "nearest point on the swept cap-factor grid",
    }


#: Approximate reference-path numerical root, located by bisection (D-056).
#: Quoted to 14 significant figures deliberately: it is a floating-point
#: approximation, not a closed-form solution, and calling it "exact" would
#: assert more than a bisection can establish.
NUMERICAL_ROOT_F = "1.09462066267694"


def _grid_pricing_parts() -> dict:
    """The pricing statement as a TRANSLATABLE key plus artifact-sourced params.

    Says three things, in order: what the registered value **is** (nearest point
    on a 0.0005-step grid), what its residual **means** (grid resolution), and
    what the residual does **not** mean (that no `f` attains the target).

    It used to return finished English prose, which was then inserted into a
    Vietnamese sentence as a `{grid}` parameter -- so a Vietnamese reader got a
    Vietnamese wrapper around a whole English paragraph. The residual-English
    scanner could not see it, because it skips any text node that contains a
    Vietnamese diacritic and the surrounding wrapper supplied one. The prose is
    now a catalogue entry in both languages and only the FIGURES travel as
    parameters, so they still come from the artifact at request time.
    """
    p = _grid_pricing()
    a, t, r = p["achieved_apr"], p["benchmark_apr"], p["residual_pp"]
    if a is None or t is None:
        return {
            "key": "labpage.grid.unavailable",
            "params": {},
            "text": ("The cost-matched cap factor is the nearest point found on "
                     "the registered search grid, not a solved root; the pricing "
                     "artifact needed to quote the residual is not loaded."),
        }
    if p["exact_match"]:
        return {
            "key": "labpage.grid.exact",
            "params": {"benchmark": f"{t:.6%}"},
            "text": (f"The cost-matched cap factor is the nearest point found on "
                     f"the registered 0.0005-step search grid. On this sweep that "
                     f"point lands on the benchmark's {t:.6%} to displayed "
                     f"precision."),
        }
    return {
        "key": "labpage.grid.residual",
        "params": {"achieved": f"{a:.6%}", "benchmark": f"{t:.6%}",
                   "residual": f"{r:.5f}", "rootF": f"{NUMERICAL_ROOT_F}"},
        "text": (
            f"The cost-matched cap factor is the NEAREST POINT FOUND ON THE "
            f"REGISTERED 0.0005-step search grid: it prices at {a:.6%} against the "
            f"amortizing loan's {t:.6%}, a residual of about {r:.5f} percentage "
            f"points. That residual is a GRID-RESOLUTION result — it reflects how "
            f"finely the search was stepped, not a limit on what is attainable. "
            f"Within an interval where the paying-month count stays fixed, the "
            f"clipped final payment changes continuously with the cap factor, so "
            f"the effective APR does too; a numerical root exists on the reference "
            f"path at approximately f = {NUMERICAL_ROOT_F}. Changes in the "
            f"paying-month count create kinks in that relationship, not gaps."),
    }


def _grid_pricing_sentence() -> str:
    """The English rendering, for the fields that still carry plain prose."""
    return _grid_pricing_parts()["text"]


def _resolve(track: str, scenario: str):
    """First artifact in the track containing this scenario."""
    for stem in TRACKS[track]:
        body = _load(f"{stem}_canonical")
        if body and scenario in body.get("scenarios", {}):
            return stem, body
    return None, None


def artifacts_available() -> bool:
    return _load("baseline_v3_canonical") is not None


def manifest() -> dict:
    roles = {
        "baseline_v3": "Illustrative pricing (cap factor 1.20) — ten scenarios",
        "baseline_equalcost_v2": "Reference-path cost-matched pricing — ten scenarios",
        "baseline_closure_v2": "Illustrative pricing — closure / zero-revenue",
        "baseline_closure_equalcost_v2": "Reference-path cost-matched — closure / zero-revenue",
    }
    out = []
    for stem, role in roles.items():
        body = _load(f"{stem}_canonical")
        if not body:
            continue
        c = body.get("canonical", {})
        out.append({
            "artifact": f"{stem}_canonical.json",
            "role": role,
            # The stem is a stable artifact identifier, so it keys the role
            # description without pinning any figure from the file.
            "role_key": f"labpage.artifactRole.{stem}",
            "sha256": _checksum(stem),
            "spec_version": c.get("spec_version"),
            "schema_version": c.get("schema_version"),
            "generator_fingerprint": c.get("generator_fingerprint"),
            "n_paths": body.get("n_paths"),
            "base_seed": body.get("base_seed"),
        })
    # Load the CANONICAL validation artifact, because that is the file this
    # block names and checksums.
    #
    # Two defects have now been fixed here. The first was that the block named
    # the superseded validation_v1.json while reading validation_v2. The second
    # survived that fix: the name and the checksum moved to
    # validation_v2_canonical.json but the READ stayed on the raw
    # validation_v2.json. The raw file carries no `canonical` block, so
    # `spec_version` came back null while a canonical checksum sat beside it —
    # a record that described one file with the contents of another. Reading
    # the canonical file makes the name, the checksum, the spec version and the
    # values all refer to the same bytes.
    val = _load("validation_v2_canonical")
    return {
        "artifacts": out,
        "pricing_reference": {
            "artifact": "validation_v2_canonical.json",
            "sha256": _checksum("validation_v2"),
            "spec_version": ((val or {}).get("canonical") or {}).get("spec_version"),
            "equal_cost": (val or {}).get("pricing", {}).get("equal_cost"),
            "benchmark_b_apr": (val or {}).get("pricing", {}).get("benchmark_b_apr"),
            "grid_pricing": _grid_pricing(),
            "note": _grid_pricing_sentence() + " Rates realised on simulated "
                    "paths differ again, because duration moves with revenue.",
        },
        "claim_taxonomy": _keyed_taxonomy(),
        "glossary": GLOSSARY,
        # Ordered and keyed. `glossary` above is unchanged for existing readers.
        "glossary_keyed": _keyed_glossary(),
        "integrity": {
            "data_basis": "SIMULATED. No observed seller revenue, repayment or "
                          "default outcome exists in this project.",
            "intervals": "Monte Carlo intervals over simulated paths. They "
                         "measure whether enough paths were run for a number to "
                         "be stable — NOT population uncertainty about real "
                         "sellers.",
            "parameters": "No contract parameter is externally sourced. All are "
                          "illustrative or derived, with sensitivity analysis "
                          "rather than claimed calibration.",
            "underwriting_model": "The RF+LR ensemble is a secondary, explicitly "
                                  "UNVALIDATED component with no measured "
                                  "predictive validity. Its training benchmark "
                                  "was withdrawn as circular. It plays no part "
                                  "in anything on this page.",
            "not_advice": "A research prototype. Not a lending service, a credit "
                          "offer, or financial advice.",
        },
    }


def scenarios() -> List[dict]:
    out = []
    for k, v in SCENARIOS.items():
        stem, _ = _resolve("illustrative", k)
        if stem:
            item = {"key": k, **v, "available": True}
            _k(item, "label", f"labpage.scenario.{k}.label")
            _k(item, "description", f"labpage.scenario.{k}.description")
            out.append(item)
    return sorted(out, key=lambda s: s["order"])


def _fmt_factor(f: float) -> str:
    """Cap factor as it reads on a chart: at least 2 decimals, at most 4, no
    trailing-zero noise. 1.2 -> "1.20", 1.0945 -> "1.0945"."""
    frac = len(f"{f:.4f}".rstrip("0").split(".")[1])
    return f"{f:.{max(2, frac)}f}"


def _fmt_money(x) -> dict:
    v = to_vnd(x)
    return {"vnd": v, "display": f"{v:,} ₫"}


def _censoring(a: dict) -> dict:
    """Duration and rate have DIFFERENT denominators. Report both separately.

    This function used to derive one qualifier from `incomplete_recovery_rate`
    and attach it to the duration *and* the rate. That was wrong, and A-9
    corrected it:

      * `duration_mean` averages paths that COMPLETED within the horizon.
      * `apr_mean` averages paths where an IRR EXISTS, which is a different and
        usually larger set. A path can fail to reach the contractual target and
        still have a perfectly well-defined return on the payments it made.

    At `closure_m13`, f = 1.20: 119 of 500 paths complete, but all 500 have a
    defined IRR. Labelling the rate "among completed paths" described 500 paths
    as 119 and understated the completed-path figure by about nine points.

    The artifacts now report `completed_rate` and `apr_defined_rate` explicitly,
    so neither denominator is inferred here. Older artifacts lack those fields;
    the fallbacks keep the Lab working against them without pretending to a
    precision they cannot supply.
    """
    incomplete = a.get("incomplete_recovery_rate") or 0.0
    completed = a.get("completed_rate")
    if completed is None:                       # pre-A-9 artifact
        completed = max(0.0, 1.0 - incomplete)
    apr_defined = a.get("apr_defined_rate")
    if apr_defined is None:                     # pre-A-9 artifact
        apr_defined = 1.0 if a.get("apr_mean") is not None else 0.0

    # ---- duration: conditioned on completion ------------------------------
    if 0.0 < completed < 1.0:
        duration_label = "Mean duration among completed paths"
        duration_label_key = "labpage.arm.durationLabelCompleted"
        duration_basis = (
            f"Averaged over the {completed:.1%} of simulated paths that reached "
            f"the repayment target within 24 months. The remaining "
            f"{1.0 - completed:.1%} did not and are excluded from this figure, "
            f"not counted as long.")
    elif completed >= 1.0:
        duration_label = "Mean duration"
        duration_label_key = "labpage.arm.durationLabel"
        duration_basis = ("Mean across simulated paths for this scenario. Every "
                          "path reached the repayment target.")
    else:
        duration_label = "Mean duration"
        duration_label_key = "labpage.arm.durationLabel"
        duration_basis = "No path reached the repayment target within 24 months."

    # ---- rate: conditioned on IRR existence, NOT on completion ------------
    if apr_defined <= 0.0:
        apr_label = "Effective APR"
        apr_label_key = "labpage.arm.aprLabelUndefined"
        apr_basis = ("No payment was made on any simulated path, so the rate "
                     "equation has no root and no APR is defined.")
    elif completed >= 1.0:
        apr_label = "Mean simulated APR"
        apr_label_key = "labpage.arm.aprLabel"
        apr_basis = ("Mean across simulated paths for this scenario. Every path "
                     "has a defined rate and every path reached the repayment "
                     "target.")
    else:
        apr_label = "Mean simulated APR among rate-defined paths"
        apr_label_key = "labpage.arm.aprLabelRateDefined"
        apr_basis = (
            f"Averaged over the {apr_defined:.1%} of simulated paths with a "
            f"defined internal rate of return — a different set from the "
            f"{completed:.1%} that reached the repayment target. A path can "
            f"miss the target and still have a rate on the payments it made. "
            f"Where the target is not reached this is the rate over the "
            f"observed 24-month window, not a final lifetime return; read it "
            f"beside the incomplete-recovery figure.")

    return {
        # `censored` is keyed to duration, which is what it always meant -- but
        # it previously read `0 < completed < 1`, so a scenario where NOTHING
        # completed reported `censored: False`. That is the most censored case
        # there is, and the flag gates whether the page shows its basis text at
        # all: at closure_m7 the reader saw a rate and a blank duration with no
        # explanation of either. Any incompleteness is now censoring, and the
        # total case is flagged separately rather than folded into "not
        # censored".
        "censored": completed < 1.0,
        "fully_censored": completed == 0.0,
        "completed_share": completed,
        "apr_defined_share": apr_defined,
        "denominators_differ": abs(apr_defined - completed) > 1e-12,
        "apr_label": apr_label,
        "duration_label": duration_label,
        # Carried beside the text so the catalogue entry tracks the CONDITION
        # the text describes, not merely the field name.
        "apr_label_key": apr_label_key,
        "duration_label_key": duration_label_key,
        "apr_basis": apr_basis,
        "duration_basis": duration_basis,
    }


def _arm_block(spec: dict, scenario: str) -> Optional[dict]:
    stem, body = _resolve(spec["track"], scenario)
    if not body:
        return None
    sc = body["scenarios"].get(scenario)
    if not sc or spec["arm"] not in sc:
        return None
    a = sc[spec["arm"]]
    terms = body.get("terms", {})
    total = a.get("total_repaid_mean")

    # The amortizing loan is an annuity: no cap factor, no contractual cap. Its
    # recovery denominator is the scheduled total, not a cap. Attributing the
    # RBF contract's cap to it would show a cap larger than its own total.
    has_cap = spec["id"] != "FIX-B"
    cap = terms.get("cap") if has_cap else None

    # Both arms have a repayment target; they differ in what defines it. A
    # revenue-based or cost-matched contract stops at a contractual cap. An
    # annuity has no cap at all — its target is simply what the schedule sums
    # to. Rendering the annuity as "no cap" said what it lacks instead of what
    # it owes, which is not a number a reader can use.
    target = {
        "label": "Contractual cap" if has_cap else "Scheduled total repayment",
        "amount": _fmt_money(cap if has_cap else (total or 0)),
        "basis": ("Advance × cap factor. Collection stops here."
                  if has_cap else
                  "Sum of the 12 scheduled instalments. This loan has no cap; "
                  "the schedule itself defines the total."),
    }

    # Chart labels carrying a cap factor are formatted from the artifact's own
    # terms, so the number on the chart and the number in the file cannot
    # disagree. Only arms without a cap factor keep a fixed label.
    f = terms.get("f")
    if spec.get("chart_label_fmt") and f is not None:
        chart_label = spec["chart_label_fmt"].format(f=_fmt_factor(f))
    else:
        chart_label = spec.get("chart_label") or spec["short"]

    note = spec["note"]
    if spec.get("note_grid"):
        note = _grid_pricing_sentence() + " " + note

    aid = spec["id"]
    block = {
        "id": aid,
        "name": spec["name"],
        "short": spec["short"],
        "chart_label": chart_label,
        "kind": spec["kind"],
        "palette": spec["palette"],
        "note": note,
        "source_artifact": f"{stem}_canonical.json",
        "source_sha256": _checksum(stem),
        "cap_factor": terms.get("f") if has_cap else None,
        "principal": _fmt_money(terms.get("A", 0)),
        "repayment_target": target,
        "contractual_cap": _fmt_money(cap) if cap is not None else None,
        "cap_basis": target["basis"],
        "total_repaid_mean": _fmt_money(total or 0),
        "effective_apr": a.get("apr_mean"),
        # A-9: undefined means the rate equation has no root -- i.e. no payment
        # was made at all. It does NOT mean the contract failed to complete;
        # closure_m7 misses the target on every path and still returns roughly
        # -86.5%, which is a result, not an absence.
        "apr_undefined_reason": (None if a.get("apr_mean") is not None else
                                 "no payment was made, so the rate equation "
                                 "has no root"),
        **_censoring(a),
        "burden": {
            "mean": a.get("burden_mean"),
            "p90": a.get("burden_p90"),
            "p95": a.get("burden_p95"),
            "max": a.get("burden_max"),
        },
        "high_burden_months": a.get("n_high_burden", {}),
        "duration_months_mean": a.get("duration_mean"),
        "duration_sd": a.get("duration_sd"),
        "censored_rate": a.get("duration_censored_rate"),
        "incomplete_recovery_rate": a.get("incomplete_recovery_rate"),
        "recovery_ratio": a.get("recovery_ratio", {}),
        "recovery_denominator": ("Contractual cap (advance × cap factor)" if has_cap
                                 else "Scheduled total repayment (this loan has no cap)"),
    }
    # Prose fields gain a sibling key; identifiers, checksums and money
    # `display` strings do not. The English values above are untouched.
    # Same reasoning for the illustrative arm's name, which quotes its cap
    # factor: the figure comes from the artifact, so it travels as a parameter.
    if aid == "RBF-ILL" and f is not None:
        block["name_key"] = "labpage.arm.RBF-ILL.nameFmt"
        block["name_params"] = {"f": _fmt_factor(f)}
    else:
        _k(block, "name", f"labpage.arm.{aid}.name")
    _k(block, "short", f"labpage.arm.{aid}.short")
    # The chart label carries the artifact's own cap factor. Keying the
    # RESOLVED label would re-freeze that figure in a translation string -- the
    # exact staleness the `chart_label_fmt` indirection was introduced to
    # remove. The FORMAT is translated; the number travels as a parameter.
    if spec.get("chart_label_fmt") and f is not None:
        block["chart_label_key"] = "labpage.arm.chartLabelFmt"
        block["chart_label_params"] = {"f": _fmt_factor(f)}
    else:
        _k(block, "chart_label", f"labpage.arm.{aid}.chartLabel")
    _k(block, "note", f"labpage.arm.{aid}.note")
    # The cost-matched arm's note quotes the grid residual, which is read from
    # the registered artifact at request time. It travels as a parameter so the
    # translated note cannot outlive the sweep it describes.
    if aid == "RBF-EQ":
        _g = _grid_pricing_parts()
        # The grid sentence is itself translated; only its figures are params.
        block["note_params"] = dict(_g["params"])
        block["note_param_keys"] = {"grid": _g["key"]}
    _k(block, "cap_basis", f"labpage.arm.{aid}.capBasis")
    # B1: these two labels CHANGE WITH THE DATA -- A-9 requires a mean taken
    # over a subset to say which subset. One shared catalogue key was attached
    # to every arm, and because apiText prefers the catalogue, the qualifier
    # ("among completed paths" / "among rate-defined paths") was discarded in
    # both languages. The key is now chosen by the same branch that chose the
    # English, so the translation cannot drop the condition.
    _k(block, "apr_label", block.pop("apr_label_key", "labpage.arm.aprLabel"))
    _k(block, "duration_label",
       block.pop("duration_label_key", "labpage.arm.durationLabel"))
    _k(block, "apr_basis", f"labpage.arm.{aid}.aprBasis")
    _k(block, "duration_basis", f"labpage.arm.{aid}.durationBasis")
    _k(block, "recovery_denominator", f"labpage.arm.{aid}.recoveryDenominator")
    _k(block, "apr_undefined_reason", "labpage.arm.aprUndefined")
    if isinstance(block.get("repayment_target"), dict):
        _k(block["repayment_target"], "label", f"labpage.arm.{aid}.targetLabel")
        _k(block["repayment_target"], "basis", f"labpage.arm.{aid}.capBasis")
    return block


def _keyed_assumptions() -> list:
    """ASSUMPTIONS as `[{text, text_key}]`, emitted BESIDE the string list.

    The existing `assumptions` field keeps its plain strings so a consumer that
    never learns about the keys is unaffected; this list carries the same items
    in the same order with a key attached.
    """
    return [{"text": a, "text_key": f"labpage.assumption.{i}"}
            for i, a in enumerate(ASSUMPTIONS)]


def _keyed_glossary() -> list:
    """GLOSSARY as an ordered list, both the term and its definition keyed.

    The dict form is kept under `glossary`; the term is itself reader-facing
    copy, so it needs a key of its own rather than being treated as an id.
    """
    out = []
    for i, (term, text) in enumerate(GLOSSARY.items()):
        out.append({"term": term, "term_key": f"labpage.glossary.{i}.term",
                    "text": text, "text_key": f"labpage.glossary.{i}.text"})
    return out


def _keyed_taxonomy() -> dict:
    out = {}
    for cls, body in CLAIM_TAXONOMY.items():
        item = dict(body)
        _k(item, "label", f"labpage.taxonomy.{cls}.label")
        _k(item, "meaning", f"labpage.taxonomy.{cls}.meaning")
        out[cls] = item
    return out


def _keyed_metric_definitions() -> dict:
    """METRIC_DEFINITIONS with a translation key beside each prose field.

    The English values are returned unchanged; only sibling `*_key` entries are
    added, so an existing consumer reading `definition` is unaffected.
    """
    out = {}
    for metric, body in METRIC_DEFINITIONS.items():
        item = dict(body)
        for field in ("definition", "why", "caveat"):
            _k(item, field, f"labpage.metric.{metric}.{field}")
        out[metric] = item
    return out


def comparison(scenario: str) -> Optional[dict]:
    if scenario not in SCENARIOS:
        return None
    arms = [b for b in (_arm_block(s, scenario) for s in ARMS) if b]
    if not arms:
        return None
    return {
        "scenario": {"key": scenario, **SCENARIOS[scenario],
                     "label_key": f"labpage.scenario.{scenario}.label",
                     "description_key": f"labpage.scenario.{scenario}.description"},
        "arms": arms,
        "metric_definitions": _keyed_metric_definitions(),
        "findings": _findings(scenario, arms),
        "assumptions": ASSUMPTIONS,
        "assumptions_keyed": _keyed_assumptions(),
        "caveats": caveats(),
        "summary": _summary(scenario, arms),
    }


def underreporting() -> Optional[dict]:
    """The omega sweep. Deliberately NOT presented as a scenario.

    It is a sensitivity sweep run on one revenue shape: the provider observes
    only ω of true revenue. Listing it beside 'severe downturn' would imply it
    is a revenue path, which it is not.
    """
    body = _load("baseline_v3_canonical")
    if not body or "underreporting" not in body:
        return None
    rows = []
    for omega in sorted(body["underreporting"], key=float):
        a = body["underreporting"][omega]
        rows.append({
            "omega": float(omega),
            "observed_share": f"{float(omega):.0%}",
            "duration_months_mean": a.get("duration_mean"),
            "incomplete_recovery_rate": a.get("incomplete_recovery_rate"),
            "burden_mean": a.get("burden_mean"),
            "effective_apr": a.get("apr_mean"),
            "total_repaid_mean": _fmt_money(a.get("total_repaid_mean") or 0),
        })
    # Derived from `rows`, never typed. A hard-coded "12.9 → 18.7" would go
    # stale silently the day the artifact changes — the exact failure mode the
    # literal scanner exists to catch on the HTML side.
    if not rows:                           # artifact present but sweep empty
        return None
    full, least = rows[-1], rows[0]        # rows ascend by ω: [0]=lowest
    all_complete = all(not (r["incomplete_recovery_rate"] or 0) for r in rows)
    if all_complete:
        observed_key = "labpage.finding.underreportingSweepComplete"
        observed_params = {"fromMonths": f"{full['duration_months_mean']:.1f}",
                           "toMonths": f"{least['duration_months_mean']:.1f}",
                           "fromOmega": f"{full['omega']:.0%}",
                           "toOmega": f"{least['omega']:.0%}"}
        observed = (
            f"In this sweep every path still reached the cap inside the "
            f"24-month window, so the total stayed at the cap and only the "
            f"duration moved: {full['duration_months_mean']:.1f} → "
            f"{least['duration_months_mean']:.1f} months as ω falls "
            f"{full['omega']:.0%} → {least['omega']:.0%}. That is this "
            f"sweep's result, not a general guarantee.")
    else:
        observed_key = "labpage.finding.underreportingSweepIncomplete"
        observed_params = {}
        observed = (
            "In this sweep some paths did NOT reach the cap inside the "
            "24-month window, so the total is not invariant across all of "
            "them — read the incomplete-recovery column.")

    return {
        "rows": rows,
        "source_artifact": "baseline_v3_canonical.json",
        "source_sha256": _checksum("baseline_v3"),
        "why_not_a_scenario": "This is a parameter sweep, not a revenue path. ω "
                              "is the share of true revenue the provider "
                              "observes; the underlying revenue shape is held "
                              "fixed. It is shown separately so it is not read "
                              "as one of the scenarios.",
        "why_not_a_scenario_key": "labpage.under.whyNotScenario",
        # A list, and split by claim class on purpose. The invariance argument
        # is a property of the contract; the duration numbers are an output of
        # one sweep. Carrying both under a single "mathematical_property" label
        # would promote a simulation result to a theorem.
        "findings": [
            {
                "classification": "mathematical_property",
                "text": "Under-reporting does not change what is owed. It "
                        "rescales the UNCAPPED remittances — the final "
                        "payment is clipped to whatever is left, so it does "
                        "not scale with \u03c9 — and raises the cumulative "
                        "sales needed to reach the cap. Invariance of the "
                        "total is conditional on the cap actually being "
                        "reached: under-reporting severe enough to push the "
                        "contract past the horizon leaves the cap unreached "
                        "and the total short.",
                "text_key": "labpage.finding.underreportingOwed",
                "source": "research/DERIVATIONS.md",
            },
            {
                "classification": "simulation_result",
                "text": observed,
                "text_key": observed_key,
                "text_params": observed_params,
                "source": "research/results/baseline_v3_canonical.json",
            },
        ],
    }


METRIC_DEFINITIONS = {
    "burden": {
        "label": "Payment burden",
        "definition": "Payment ÷ GMV in a given month — note the denominator is "
                      "GMV while remittance is charged on net sales, so this "
                      "is r·(1 − return rate), not r. Computed from revenue "
                      "alone; undefined in months with zero revenue.",
        "why": "It is the share of this month's takings that leaves as a payment.",
        "caveat": "Burden is measured against REVENUE, not against what the "
                  "seller has left. Margins, operating costs, reserves and other "
                  "debts are not modelled, so a lower burden here does not "
                  "establish that a contract is affordable.",
    },
    "high_burden_months": {
        "label": "Months above a burden threshold",
        "definition": "Count of months where payment burden exceeds 10%, 15%, "
                      "20% or 25%, out of a 24-month window.",
        "why": "Averages hide bad months. This counts them.",
        "caveat": "These thresholds are ILLUSTRATIVE reporting bands chosen for "
                  "this study. They are not validated hardship cutoffs and no "
                  "claim is made that crossing one causes distress. For a "
                  "revenue share the count is constant in these scenarios, but "
                  "NOT by construction: the remittance is a fixed share of net "
                  "sales while this count is measured against payment ÷ GMV, so "
                  "it can move when the return rate moves. It is constant only "
                  "while the net-sales/GMV ratio holds fixed. The informative "
                  "side is the fixed arm.",
    },
    "duration_months_mean": {
        "label": "Repayment duration",
        "definition": "Mean months until cumulative payments reach the "
                      "repayment target — computed ONLY over paths that reached "
                      "it within the 24-month window. Paths that did not are "
                      "excluded from this mean and reported separately as "
                      "incomplete recovery.",
        "why": "Revenue-based repayment extends the term when revenue falls, "
               "rather than holding the payment fixed. In the scenarios where "
               "the term extends, that extension is the provider's cost. "
               "Extension is NOT the same as preventing default: where revenue "
               "stops PERMANENTLY BEFORE COMPLETION while a contractual "
               "balance remains, no further payment occurs and the cap is "
               "never reached. A temporary zero-revenue spell is a different "
               "case and usually still completes -- temp_closure leaves 2.0% "
               "of paths incomplete at f = 1.20 and none at f*. Read this "
               "beside the incomplete-recovery rate.",
        "caveat": "Where any path fails to complete, this is a SURVIVOR "
                  "statistic. It describes the contracts that finished, not the "
                  "portfolio. A scenario with a short mean duration and a high "
                  "incomplete-recovery rate is not a fast contract — it is one "
                  "where the slow paths were dropped rather than counted.",
    },
    "recovery_ratio": {
        "label": "Provider recovery",
        "definition": "Share of the arm's own repayment target recovered by "
                      "month 12, 18 and 24. For the revenue-based and "
                      "cost-matched fixed arms the denominator is the "
                      "contractual cap; for the amortizing loan, which has no "
                      "cap, it is scheduled total repayment.",
        "why": "The other side of the trade-off. Where recovery is slower it is "
               "a real cost to the financier even when the full amount is "
               "eventually repaid — but the direction is not universal. "
               "Revenue-contingent recovery may lead or lag the cost-matched "
               "fixed arm depending on the realised path (P4), and both occur "
               "in the registered scenarios. Read the direction per scenario.",
        "caveat": "Denominators differ by arm, so read each arm against its own "
                  "target rather than comparing absolute amounts recovered.",
    },
    "incomplete_recovery_rate": {
        "label": "Incomplete recovery",
        "definition": "Share of simulated paths that do not reach the repayment "
                      "target within the 24-month observation window.",
        "why": "Censoring, not default.",
        "caveat": "This is NOT a default rate. No borrower behaviour and no "
                  "default is simulated on any arm.",
    },
    "effective_apr": {
        "label": "Effective APR",
        "definition": "Annualised internal rate of return of the payment stream "
                      "against the advance, averaged over the paths where a "
                      "rate EXISTS. Existence is the only condition: the mean "
                      "is NOT restricted to paths that reached the repayment "
                      "target. A path that stopped short of the cap but made "
                      "payments still has a well-defined rate over the observed "
                      "window, and it is counted here. Only a path that repays "
                      "nothing at all has no rate and is excluded.",
        "why": "Puts a revenue share and a fixed instalment on one axis.",
        # A-9. This caveat previously said the rate excluded every path that did
        # not complete. That was the pre-A-9 reading, withdrawn because the two
        # events are separate: completion is reaching the contractual target,
        # existence of an IRR is a sign condition on the cash-flow vector. They
        # coincide often enough to have hidden the error, and come apart sharply
        # at closure_m13 and closure_m7.
        "caveat": "Read the two denominators separately. DURATION is averaged "
                  "over completing paths only. THIS RATE is averaged over paths "
                  "with a defined internal rate of return, which is a different "
                  "and usually larger set — an incomplete path that made "
                  "payments has a defined rate over the OBSERVED WINDOW, and "
                  "that is a window figure, not a final lifetime return. "
                  "Neither conditional mean is automatically a portfolio-wide "
                  "outcome: each describes the subset it is computed over, so "
                  "read both beside the incomplete-recovery rate rather than "
                  "treating either as the scenario's result. Paths that fall "
                  "short are not 'unprofitable' — profitability is computed "
                  "nowhere in this project; they simply did not reach the cap "
                  "inside the horizon. Separately, this is the MEAN ACROSS "
                  "SIMULATED PATHS, not the reference-path rate the "
                  "cost-matched contract was priced on.",
    },
}

ASSUMPTIONS = [
    "Revenue paths are generated, not observed. Parameters are illustrative.",
    "Remittance is collected on net sales — gross merchandise value after returns.",
    "The seller draws the advance at month 1 and the observation window is 24 months.",
    "Both fixed arms are modelled as paid in full and on time. No borrower "
    "behaviour, hardship, renegotiation or default is simulated on any arm.",
    "The cost-matched fixed benchmark is priced once on a flat, shock-free "
    "reference path and held constant across every path in a scenario — a "
    "contract cannot be retro-priced by a shock that happens later.",
]

CAVEATS = [
    {"text": "Every figure here is simulation output under stated assumptions. "
             "No observed seller revenue, repayment or default outcome exists in "
             "this project.",
     "classification": "open_real_world_question"},
    {"text": "The fixed arms are modelled as paid in full and on time in every "
             "month of the schedule. The fixed arm is therefore an OPTIMISTIC "
             "SCHEDULED-RECOVERY BENCHMARK: it shows what the schedule would "
             "deliver under that assumption. It is not an upper bound derived "
             "from anything measured here, and this project makes no claim "
             "about how often real fixed-payment borrowers miss payments.",
     "classification": "open_real_world_question"},
    {"text": "Whether revenue-based repayment recovers faster or slower depends "
             "on the revenue path, and both directions appear in this scenario "
             "library. Nothing here supports a universal claim in either "
             "direction.",
     "classification": "simulation_result"},
    {"text": "Intervals in the underlying artifacts are Monte Carlo intervals "
             "over simulated paths. They are not population confidence intervals "
             "and say nothing about real sellers.",
     "classification": "open_real_world_question"},
    {"text": "{grid} The label describes how the price was chosen, not an "
             "outcome guaranteed on any path: across simulated paths the "
             "realised rate differs again, because duration varies with revenue "
             "and a longer duration lowers the annualised rate for the same "
             "total.",
     "classification": "sensitivity_result"},
    # A-9. The withdrawn version of this caveat put duration and rate under one
    # denominator. They have never had one.
    {"text": "Mean duration and mean rate have DIFFERENT denominators and must "
             "be read separately. Mean duration covers only paths that reached "
             "the repayment target. Mean rate covers paths with a defined "
             "internal rate of return — a larger set, because an incomplete "
             "path that made payments still has a rate over the observed "
             "window. Neither is automatically a portfolio-wide outcome; each "
             "describes the subset it was computed over, and both should be "
             "read beside the incomplete-recovery rate.",
     "classification": "simulation_result"},
    {"text": "Payment burden is measured against revenue, not against what the "
             "seller retains. Margins, operating costs, reserves and other debts "
             "are outside the model, so a lower burden is not by itself evidence "
             "that a contract is affordable.",
     "classification": "open_real_world_question"},
]


def caveats() -> List[dict]:
    """CAVEATS with artifact-sourced values substituted.

    The pricing caveat quotes a residual, and a quoted number must come from the
    file it describes. `{grid}` is filled from the canonical validation artifact
    at request time rather than baked into the constant, so the caveat cannot
    outlive the sweep it is describing.
    """
    g = _grid_pricing_parts()
    out = []
    for i, c in enumerate(CAVEATS):
        item = {**c, "text": c["text"].replace("{grid}", g["text"])}
        # Position is the only stable handle these constants carry, so the key
        # is index-based and a test pins the count. The grid sentence travels
        # as a translation KEY plus artifact-sourced figures -- not as finished
        # English prose, which is how an English paragraph used to end up
        # inside a Vietnamese caveat.
        item["text_key"] = f"labpage.caveat.{i}"
        if "{grid}" in c["text"]:
            item["text_params"] = dict(g["params"])
            item["text_param_keys"] = {"grid": g["key"]}
        out.append(item)
    return out


def _summary(scenario: str, arms: List[dict]) -> dict:
    """A compact headline for the top of the page, derived from this scenario's
    own values so it cannot drift from the charts below it."""
    by = {a["id"]: a for a in arms}
    fa, ill = by.get("FIX-A"), by.get("RBF-ILL")
    if not (fa and ill):
        return {}
    # NAME THE PAIR. This headline compares exactly two of the four arms --
    # FIX-A against RBF-ILL -- and there are two fixed arms and two
    # revenue-based arms on screen, so "the fixed arm" does not identify a row.
    #
    # And handle EQUALITY. `>=` used to select FIX-A at an exact tie and then
    # assert it had recovered more, which is false. No currently registered
    # scenario produces a tie (FIX-A sits at 0.923076923076923 in all thirteen
    # while RBF-ILL ranges 0.443 to 1.0), so this was latent rather than live;
    # it is fixed here rather than left for an artifact that produces one.
    f12 = fa["recovery_ratio"].get("12", 0)
    r12 = ill["recovery_ratio"].get("12", 0)

    # WHETHER THE TARGETS DIFFER IS READ FROM THE TARGETS, not assumed. This
    # pair happens to share a target -- both are the 1.20 cap on the same
    # advance, so both are 222,000,000 VND in every registered scenario -- and
    # for an equal target a larger share IS a larger amount. Saying otherwise
    # was wrong. The branch is derived so it stays right if a future artifact
    # prices them apart.
    fa_target = _target_vnd(fa)
    ill_target = _target_vnd(ill)
    same_target = (fa_target is not None and fa_target == ill_target)

    if f12 == r12:
        faster, faster_key = "both contracts", "labpage.armRef.both"
        sentence_key = ("labpage.summary.sentenceLevelSameTarget" if same_target
                        else "labpage.summary.sentenceLevel")
    elif f12 > r12:
        faster, faster_key = FIX_A_REF, "labpage.armRef.FIX-A"
        sentence_key = ("labpage.summary.sentenceSameTarget" if same_target
                        else "labpage.summary.sentence")
    else:
        faster, faster_key = RBF_ILL_REF, "labpage.armRef.RBF-ILL"
        sentence_key = ("labpage.summary.sentenceSameTarget" if same_target
                        else "labpage.summary.sentence")

    # The English built here is the fallback a reader sees when no catalogue
    # entry resolves, so it must say exactly what the catalogue entry for the
    # same branch says -- including in the tie case, where "the same share is
    # the same amount" is the precise statement and "compare like for like"
    # is not.
    tied = (f12 == r12)
    target_display = fa["repayment_target"]["amount"]["display"]
    if same_target and tied:
        target_clause = f" Both target {target_display}, so the same share is the same amount."
    elif same_target:
        target_clause = f" Both target {target_display}, so the two percentages compare like for like."
    elif tied:
        target_clause = " The two targets differ, so the same share is not the same amount."
    else:
        target_clause = (" The two targets differ, so this is not a comparison "
                         "of amounts recovered.")
    return {
        "scenario_label": SCENARIOS[scenario]["label"],
        "scenario_label_key": f"labpage.scenario.{scenario}.label",
        "peak_burden_fixed": fa["burden"]["max"],
        "peak_burden_rbf": ill["burden"]["max"],
        "recovery12_fixed": fa["recovery_ratio"].get("12"),
        "recovery12_rbf": ill["recovery_ratio"].get("12"),
        "incomplete_rbf": ill["incomplete_recovery_rate"],
        "faster_by_month_12": faster,
        "compared_pair": ["FIX-A", "RBF-ILL"],
        "same_target": same_target,
        "sentence": (
            f"Comparing {FIX_A_REF} with {RBF_ILL_REF}: peak payment burden "
            f"reaches {fa['burden']['max']:.1%} against "
            f"{ill['burden']['max']:.1%}, and by month 12 "
            + ("both have recovered the same share of their repayment "
               "target." if tied else
               f"{faster} has recovered a larger share of its repayment "
               "target.")
            + target_clause),
        "sentence_key": sentence_key,
        "sentence_params": {"fixedPct": f"{fa['burden']['max']:.1%}",
                            "rbfPct": f"{ill['burden']['max']:.1%}",
                            "target": fa["repayment_target"]["amount"]["display"]},
        "sentence_param_keys": {"fixedArm": "labpage.armRef.FIX-A",
                                "rbfArm": "labpage.armRef.RBF-ILL",
                                "faster": faster_key},
    }


def _rate_parts(rates_equal, eq, ill, eq_defined, scenario, has_window_note):
    """Translatable sentences for the composed rate finding.

    The English `text` beside this is unchanged and remains authoritative for
    existing consumers. Numbers travel as parameters so a translated sentence
    cannot drift from the artifact it describes.
    """
    parts = [{
        "key": ("labpage.finding.ratesEqual" if rates_equal
                else "labpage.finding.priceStructureSeparable"),
        "params": ({"rbfRate": f"{ill['effective_apr']:.2%}"} if rates_equal else
                   {"eqRate": f"{eq['effective_apr']:.2%}",
                    "illRate": f"{ill['effective_apr']:.2%}",
                    "definedPct": f"{eq_defined:.1%}"}),
        "param_keys": {"scenario": f"labpage.scenario.{scenario}.label"},
    }]
    differs = abs(eq["completed_share"] - ill["completed_share"]) > 1e-9
    parts.append({
        "key": ("labpage.finding.completionDiffers" if differs
                else "labpage.finding.completionSame"),
        "params": {"eqPct": f"{eq['completed_share']:.1%}",
                   "illPct": f"{ill['completed_share']:.1%}"},
        "param_keys": {},
    })
    if has_window_note:
        parts.append({"key": "labpage.finding.windowNote", "params": {}, "param_keys": {}})
    return parts


def _findings(scenario: str, arms: List[dict]) -> List[dict]:
    """Conclusions for THIS scenario, each carrying its claim classification.

    Comparative statements are derived from the values just returned — the same
    numbers the UI displays — so a finding cannot drift from the chart beside it.
    Every scenario-dependent statement names the scenario.
    """
    by = {a["id"]: a for a in arms}
    label = SCENARIOS[scenario]["label"].lower()
    out: List[dict] = [
        {"classification": "mathematical_property",
         "text": "Contractual remittance is a fixed share of NET SALES, so the "
                 "contractual burden is constant by construction. The burden "
                 "shown here uses a different denominator — payment ÷ GMV — "
                 "so it equals r·(1 − return rate) and MOVES when the return "
                 "rate moves. It is constant only in scenarios where the "
                 "net-sales/GMV ratio is fixed. Most registered scenarios hold "
                 "that ratio fixed; `returns_spike` is the explicit exception "
                 "where the displayed burden moves.",
         "text_key": "labpage.finding.burdenDenominator",
         "source": "research/DERIVATIONS.md"},
        {"classification": "mathematical_property",
         "text": "A fixed instalment does not adjust, so its burden rises in "
                 "INVERSE proportion to revenue: halve revenue and the burden "
                 "doubles. (It does not rise 'in proportion' — that would mean "
                 "falling with revenue, which is what the revenue share does.) "
                 "Under a revenue share the expected repayment period lengthens "
                 "instead. That is a statement about the payment rule, not about "
                 "whether the contract is ultimately repaid: where revenue stops "
                 "before the cap is reached, a balance goes unrecovered. The "
                 "trade is timing, not forgiveness — and not immunity.",
         "text_key": "labpage.finding.fixedBurdenInverse",
         "source": "research/DERIVATIONS.md"},
    ]

    fa, eq, ill = by.get("FIX-A"), by.get("RBF-EQ"), by.get("RBF-ILL")

    if fa and ill:
        out.append({
            "classification": "simulation_result",
            "text": (f"In the {label} scenario, the cost-matched fixed arm reaches "
                     f"a peak payment burden of {fa['burden']['max']:.1%}, against "
                     f"{ill['burden']['max']:.1%} for the revenue-based arm."),
            "text_key": "labpage.finding.peakBurden",
            "text_params": {"fixedPct": f"{fa['burden']['max']:.1%}",
                            "rbfPct": f"{ill['burden']['max']:.1%}"},
            "text_param_keys": {"scenario": f"labpage.scenario.{scenario}.label"},
            "source": fa["source_artifact"]})

        f12, r12 = fa["recovery_ratio"].get("12", 0), ill["recovery_ratio"].get("12", 0)
        # Same equality correction as _summary: an exact tie is "level with",
        # not "ahead of".
        if f12 == r12:
            direction, direction_key = "level with", "labpage.finding.direction.level"
        elif f12 > r12:
            direction, direction_key = "ahead of", "labpage.finding.direction.ahead"
        else:
            direction, direction_key = "behind", "labpage.finding.direction.behind"
        out.append({
            "classification": "simulation_result",
            # Same correction as the headline: read whether the targets match
            # rather than asserting that they differ.
            "text": (f"In the {label} scenario, recovery by month 12 reaches "
                     f"{f12:.1%} of target for {FIX_A_REF} and "
                     f"{r12:.1%} of target for {RBF_ILL_REF} — so "
                     f"{FIX_A_REF} is {direction} {RBF_ILL_REF} here. "
                     + (f"Both target {fa['repayment_target']['amount']['display']}, "
                        f"so these percentages compare like for like."
                        if _target_vnd(fa) is not None
                        and _target_vnd(fa) == _target_vnd(ill)
                        else "The two targets differ, so this is not a "
                             "comparison of amounts recovered.")
                     + f" This ordering is a property of this scenario and does "
                       f"not hold across all of them."),
            "text_key": ("labpage.finding.recovery12SameTarget"
                         if _target_vnd(fa) is not None
                         and _target_vnd(fa) == _target_vnd(ill)
                         else "labpage.finding.recovery12"),
            "text_params": {"fixedPct": f"{f12:.1%}", "rbfPct": f"{r12:.1%}",
                            "target": fa["repayment_target"]["amount"]["display"]},
            "text_param_keys": {"scenario": f"labpage.scenario.{scenario}.label",
                                "direction": direction_key,
                                "fixedArm": "labpage.armRef.FIX-A",
                                "rbfArm": "labpage.armRef.RBF-ILL"},
            "source": ill["source_artifact"]})

        if ill["incomplete_recovery_rate"] > 0:
            out.append({
                "classification": "simulation_result",
                "text": (f"In the {label} scenario "
                         f"{ill['incomplete_recovery_rate']:.1%} of simulated "
                         f"paths do not reach the repayment target within the "
                         f"24-month window. That is censoring under this "
                         f"scenario's revenue path, not a modelled default."),
                "text_key": "labpage.finding.incompleteRecovery",
                "text_params": {"pct": f"{ill['incomplete_recovery_rate']:.1%}"},
                "text_param_keys": {"scenario": f"labpage.scenario.{scenario}.label"},
                "source": ill["source_artifact"]})

    if eq and ill and eq["effective_apr"] is not None and ill["effective_apr"] is not None:
        # A-9 / D-050. This comparison is between two RATES, so the question is
        # whether the two rates were averaged over comparably selected sets --
        # which means comparing their APR-DEFINED shares, not their completion
        # shares. The previous version branched on `censored`, a duration
        # property, and then quoted completion shares as though they were the
        # rate's denominator. At closure_m7 that produced the worst possible
        # output: `censored` is False because *nothing* completed, so the page
        # asserted "every path completed under both" over 0/500.
        eq_defined = eq.get("apr_defined_share", 1.0)
        ill_defined = ill.get("apr_defined_share", 1.0)
        same_rate_population = abs(eq_defined - ill_defined) < 1e-9
        partial = min(eq["completed_share"], ill["completed_share"]) < 1.0

        # Completion is reported on its own, always, and never inferred from
        # the rate. It is a separate sentence because it is a separate fact.
        completion_note = (
            f"Completion is reported separately and differs between them: "
            f"{eq['completed_share']:.1%} of the cost-matched arm's paths and "
            f"{ill['completed_share']:.1%} of the illustrative arm's reached "
            f"the repayment target."
            if abs(eq["completed_share"] - ill["completed_share"]) > 1e-9 else
            f"Completion is reported separately: {eq['completed_share']:.1%} of "
            f"paths reached the repayment target under both.")

        # Where the target is not reached, the rate is an observed-window
        # figure over the 24-month horizon -- not the cost of a repaid
        # contract. It must never be read as a completed-contract price.
        window_note = (
            " Where the target is not reached the rate is an observed-window "
            "IRR over the payments made inside the 24-month horizon, not the "
            "cost of a completed contract." if partial else "")

        if same_rate_population:
            # Where the two rates COINCIDE there is no difference to attribute,
            # and saying the cap factor caused one would be an explanation of
            # nothing. At closure_m7 neither cap binds before revenue stops, so
            # the payment streams are identical and so are the rates -- the
            # targets differ but never become reachable.
            rates_equal = abs(eq["effective_apr"] - ill["effective_apr"]) < 5e-5
            if rates_equal:
                body = (f"Both cap factors give the same mean simulated rate of "
                        f"{ill['effective_apr']:.2%} in the {label} scenario. "
                        f"Neither cap binds before revenue stops, so the two "
                        f"contracts make identical payments and their "
                        f"observed-window rates coincide despite different "
                        f"contractual targets. There is no price effect here to "
                        f"attribute — the difference the cap factor makes "
                        f"elsewhere requires the cap to be reachable.")
            else:
                body = (f"Price and structure are separable. The same "
                        f"revenue-share structure priced at the reference-path "
                        f"cost-matched factor shows a mean simulated rate of "
                        f"{eq['effective_apr']:.2%} in the {label} scenario, "
                        f"against {ill['effective_apr']:.2%} at the illustrative "
                        f"1.20 factor. Both means are taken over the same share "
                        f"of paths — {eq_defined:.1%} have a defined rate under "
                        f"each — so the rate comparison is like-for-like and the "
                        f"difference is a property of the chosen cap factor, not "
                        f"of revenue-based repayment.")
            out.append({
                "classification": "sensitivity_result",
                "text": f"{body} {completion_note}{window_note}",
                # Each sentence is its own translatable unit: a denominator or a
                # selection caveat mistranslated inside a larger block would assert
                # something the artifact does not support.
                "text_parts": _rate_parts(rates_equal, eq, ill, eq_defined,
                                          scenario, bool(window_note)),
                "source": eq["source_artifact"]})
        else:
            out.append({
                "classification": "simulation_result",
                "text": (f"In the {label} scenario these two revenue-based arms "
                         f"cannot be compared on rate alone. The cost-matched arm "
                         f"shows {eq['effective_apr']:.2%}, averaged over the "
                         f"{eq_defined:.1%} of its paths with a defined rate; the "
                         f"illustrative arm shows {ill['effective_apr']:.2%} over "
                         f"{ill_defined:.1%} of its paths. Those are differently "
                         f"selected sets, so the difference between them combines "
                         f"the cap factor with differing selection and no "
                         f"like-for-like price conclusion is drawn. "
                         f"{completion_note}{window_note}"),
                "source": eq["source_artifact"]})
    elif ill and ill["effective_apr"] is None:
        out.append({
            "classification": "mathematical_property",
            "text": ("Effective rate is UNDEFINED for the revenue-based arm in "
                     "this scenario — not because repayment was incomplete, but "
                     "because no payment was made at all, so the rate equation "
                     "has no root. An incomplete contract that paid something "
                     "does have a rate, and it is reported. Here no discount "
                     "rate sets its present "
                     "value equal to the amount lent. The study reports this as "
                     "undefined rather than substituting a number "
                     "(specification §13, exclusion E-3)."),
            "source": "research/METHODOLOGY_SPEC.md §13"})

    out.append({
        "classification": "product_implication",
        "text": "A revenue share makes the CONTRACTUAL remittance a fixed share "
                "of net sales, so the contractual burden does not rise when "
                "revenue falls. The burden displayed here uses a different "
                "denominator — payment ÷ GMV — so it is constant only while the "
                "net-sales/GMV ratio is fixed, and it varies when returns vary. "
                "The price of the revenue-contingent structure is a MORE "
                "VARIABLE recovery period whose direction depends on the "
                "realised path: under P4 revenue-contingent recovery leads a "
                "cost-matched fixed schedule when the realised mean eligible "
                "base clears B* = P/r and lags when it does not, and both "
                "occur in the registered scenarios. Calling it uniformly "
                "longer would state one scenario's direction as a property "
                "of the structure. Which side of that trade is worth taking "
                "is a commercial judgement this study does not make.",
        "text_key": "labpage.finding.contractualVsDisplayed",
        "source": "author"})
    out.append({
        "classification": "open_real_world_question",
        "text": "Whether real sellers would repay on these paths, and at what "
                "default rate, cannot be answered here. It needs observed revenue "
                "and adjudicated repayment outcomes.",
        "text_key": "labpage.finding.openQuestion",
        "source": "research/CORRECTED_CLAIMS.md"})
    return out
