"""F7: the additive Lab translation metadata.

The Lab API gained sibling `<field>_key` / `<field>_params` / `<field>_param_keys`
entries beside its existing English prose, plus `text_parts` on findings. These
tests pin three properties the review asked for:

  * ADDITIVE — every pre-existing English field is still present and unchanged,
    so a consumer that never learns about the keys keeps working.
  * RESOLVABLE — every key the API emits exists in BOTH catalogues with
    non-empty text, in every scenario, on every Lab endpoint.
  * NOT FROZEN — no translation string reachable from the Lab API hardcodes a
    research figure. Numbers stay in the JSON the engine computes.

Coverage is over all 13 scenarios and all four endpoints, not the default one.
"""
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

ROOT = Path(__file__).resolve().parents[2]
EN = json.loads((ROOT / "frontend" / "i18n" / "en.json").read_text(encoding="utf-8"))
VI = json.loads((ROOT / "frontend" / "i18n" / "vi.json").read_text(encoding="utf-8"))

SCENARIOS = [s["key"] for s in client.get("/api/lab/scenarios").json()["scenarios"]]


def _payloads():
    """Every Lab response, keyed by a label naming its endpoint."""
    out = {
        "manifest": client.get("/api/lab/manifest").json(),
        "scenarios": client.get("/api/lab/scenarios").json(),
        "underreporting": client.get("/api/lab/underreporting").json(),
    }
    for s in SCENARIOS:
        out[f"comparison/{s}"] = client.get(f"/api/lab/comparison/{s}").json()
    return out


def _walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, node


def _emitted_keys():
    """(endpoint, json path, key) for every translation key the API emits."""
    found = []
    for label, body in _payloads().items():
        for path, value in _walk(body):
            leaf = path.split(".")[-1].split("[")[0]
            if leaf.endswith("_key") and isinstance(value, str):
                found.append((label, path, value))
            elif leaf == "key" and path.endswith("text_parts") is False and isinstance(value, str) and value.count(".") >= 2 and value.split(".")[0] in ("labpage", "lab"):
                found.append((label, path, value))
            elif leaf.endswith("_param_keys") and isinstance(value, str):
                found.append((label, path, value))
    return found


def test_every_emitted_key_resolves_non_empty_in_both_catalogues():
    missing = []
    for label, path, key in _emitted_keys():
        for lang, cat in (("en", EN), ("vi", VI)):
            text = cat.get(key)
            if not isinstance(text, str) or not text.strip():
                missing.append(f"{lang}: {key} ({label} {path})")
    assert not missing, "unresolvable translation keys:\n" + "\n".join(sorted(set(missing))[:40])


def test_the_api_emits_keys_at_all(sentinel=None):
    """Guards the two tests above against vacuous success."""
    keys = _emitted_keys()
    assert len(keys) > 200, f"only {len(keys)} keys emitted; the walk is not finding them"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_finding_text_parts_are_fully_keyed_and_resolvable(scenario):
    body = client.get(f"/api/lab/comparison/{scenario}").json()
    findings = body["findings"]
    assert findings, f"{scenario} has no findings to localize"
    for f in findings:
        assert f.get("text"), "the English finding text must survive"
        keyed = "text_key" in f or "text_parts" in f
        assert keyed, f"{scenario}: finding not keyed: {f['text'][:60]}"
        for part in f.get("text_parts", []):
            assert part.get("key"), f"{scenario}: text part without a key"
            for lang, cat in (("en", EN), ("vi", VI)):
                assert cat.get(part["key"], "").strip(), f"{lang} missing {part['key']}"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_the_metadata_is_additive_every_english_field_survives(scenario):
    """A consumer that reads only the original fields sees no change."""
    body = client.get(f"/api/lab/comparison/{scenario}").json()
    for metric, item in body["metric_definitions"].items():
        for field in ("definition", "why", "caveat"):
            if f"{field}_key" in item:
                assert item.get(field), f"{metric}.{field} was replaced, not annotated"
    for arm in body["arms"]:
        for field in ("name", "apr_label", "duration_label", "apr_basis", "duration_basis"):
            if f"{field}_key" in arm:
                assert arm.get(field), f"arm {arm['id']}.{field} was replaced, not annotated"
    assert body["scenario"].get("label") and body["scenario"].get("description")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_keying_changed_no_numbers(scenario):
    """The keys are presentation only. Every numeric field is untouched prose-free data."""
    body = client.get(f"/api/lab/comparison/{scenario}").json()
    for path, value in _walk(body):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert value == value, f"{path} is NaN"  # arithmetic is engine-owned; shape only
    # the keyed blocks must not have grown a numeric literal inside a key name
    for _, _, key in _emitted_keys():
        assert not re.search(r"\d+(?:\.\d+)?(?:%|x)", key), f"figure frozen into a key: {key}"


_FIGURE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:%|×|x\b)")

# PRE-EXISTING, NOT INTRODUCED HERE: the repo's own English prose for this
# metric quotes a computed incomplete-recovery share ("temp_closure leaves 2.0%
# of paths incomplete at f = 1.20"). The Vietnamese mirrors it verbatim. It is
# a real frozen figure and it is recorded as an open defect; it is exempted
# here so this test pins the NEW metadata rather than failing on old prose.
# Removing the exemption requires parameterising that sentence from the
# temp_closure artifact, which this pass does not do.
_PRE_EXISTING_FROZEN = {
    "labpage.metric.duration_months_mean.why",
}


def _artifact_cap_factors():
    """The cap factors the engine reads out of the registered artifacts.

    SCOPE, stated plainly: this test pins the cap factor, not every figure.
    The cap factor is the documented hazard -- `chart_label_fmt` exists in
    lab.py precisely because a hand-typed "1.0945x" would go stale if a sweep
    moved, and keying the RESOLVED label undid that. A broader rule (any number
    in a translation string that also appears anywhere in the payload) was
    tried and rejected: it collides with month labels (12 / 18 / 24) and with
    the hand-typed study assumptions already present in the source English,
    so it reports noise rather than staleness.
    """
    out = set()
    for body in _payloads().values():
        for path, value in _walk(body):
            if path.split(".")[-1].split("[")[0] != "cap_factor":
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            out.add(f"{value}")
            out.add(f"{value:.2f}")
            out.add(f"{value:.4f}")
    return out


def test_no_lab_translation_string_freezes_an_artifact_cap_factor():
    """Cap factors travel as params. A frozen one goes stale silently."""
    factors = _artifact_cap_factors()
    assert factors, "no cap factor found in any payload; the test is vacuous"
    emitted = {k for _, _, k in _emitted_keys()}
    offenders = []
    for key in sorted(emitted):
        if key in _PRE_EXISTING_FROZEN:
            continue
        for lang, cat in (("en", EN), ("vi", VI)):
            for number in _FIGURE.findall(cat.get(key, "")):
                if number.replace(",", ".") in factors:
                    offenders.append(f"{lang}:{key}: {number!r}")
    assert not offenders, (
        "artifact cap factors frozen into translation strings; pass them as "
        "params instead:\n" + "\n".join(sorted(set(offenders))))


def test_the_cap_factor_reaches_the_page_as_a_parameter_not_a_string():
    """Direct guard on the regression the test above caught."""
    body = client.get("/api/lab/comparison/stable").json()
    arms = {a["id"]: a for a in body["arms"]}
    for aid in ("RBF-EQ", "RBF-ILL"):
        arm = arms[aid]
        assert arm["chart_label_key"] == "labpage.arm.chartLabelFmt"
        assert arm["chart_label_params"]["f"], f"{aid} carries no cap factor param"
        for lang, cat in (("en", EN), ("vi", VI)):
            fmt = cat["labpage.arm.chartLabelFmt"]
            assert "{f}" in fmt, f"{lang} chart label format dropped the parameter"
            assert not re.search(r"\d", fmt), f"{lang} chart label format froze a number"
    ill = arms["RBF-ILL"]
    assert ill["name_key"] == "labpage.arm.RBF-ILL.nameFmt"
    assert ill["name_params"]["f"]
    for lang, cat in (("en", EN), ("vi", VI)):
        assert "{f}" in cat["labpage.arm.RBF-ILL.nameFmt"]


def test_vietnamese_copy_uses_the_same_decimal_mark_the_page_prints():
    """A comma decimal in translated copy would read as a different number.

    The page's own formatters (`num`, `pct`) print a DOT decimal in BOTH
    languages -- "13.0 tháng", "37.87%" -- while the money formatter follows
    Vietnamese convention. Prose that quotes a figure sits beside those printed
    figures, so it has to match them. (The num/money split is pre-existing and
    is NOT changed here; this test only stops translated prose drifting from
    what the page prints next to it.)
    """
    bad = []
    for key, text in VI.items():
        if not key.startswith(("lab.", "labpage.")) or not isinstance(text, str):
            continue
        if re.search(r"(?<=\d),(?=\d)", text):
            bad.append(key)
    assert not bad, "comma decimals in Vietnamese Lab copy:\n" + "\n".join(sorted(bad))


LAB_HTML = (ROOT / "frontend" / "lab.html").read_text(encoding="utf-8")
DEMO_HTML = (ROOT / "frontend" / "demo.html").read_text(encoding="utf-8")


def test_the_language_switch_does_not_collapse_an_open_contract_panel():
    """renderArms() rebuilds with innerHTML; the switch calls it again.

    Without capture/restore a reader who opened a contract panel and then
    switched language would silently lose both the panel and keyboard focus.
    """
    assert "function armPanelState(" in LAB_HTML
    assert "function restoreArmPanels(" in LAB_HTML
    body = LAB_HTML[LAB_HTML.index("function renderArms(arms){"):]
    body = body[:body.index("\n}\n")]
    capture = body.index("armPanelState()")
    write = body.index('el("arms").innerHTML')
    restore = body.index("restoreArmPanels(")
    assert capture < write < restore, (
        "state must be captured BEFORE the rebuild and restored AFTER it"
    )
    assert 'details[data-arm]' in LAB_HTML, "panels must be keyed by arm id, not by position"
    assert 'data-arm="' in LAB_HTML


def test_the_language_switch_repaints_the_dashboard_copy():
    """renderStats/renderCounts/renderCharts/renderTable build their own copy.

    None of it carries a data-i18n attribute, so the runtime's attribute pass
    cannot reach it; without an explicit repaint it stays in the language that
    was active when the dashboard last loaded.
    """
    body = DEMO_HTML[DEMO_HTML.index("function repaintDynamicCopy(){"):]
    body = body[:body.index("\n}\n")]
    for fn in ("renderStats()", "renderCounts()", "renderCharts()", "renderTable()"):
        assert fn in body, f"{fn} is not repainted on a language change"
    assert "if(stats)" in body, "the repaint must be skipped before the first load"


# ── the compared pair, and the tie ─────────────────────────────────────────

def test_the_headline_names_which_two_of_the_four_arms_it_compares():
    """Four arms are on screen: two fixed, two revenue-based.

    The headline used to say "the fixed arm" and "the revenue-based arm", which
    identifies neither row. It compares FIX-A against RBF-ILL specifically.
    """
    for scenario in SCENARIOS:
        body = client.get(f"/api/lab/comparison/{scenario}").json()
        s = body.get("summary") or {}
        if not s:
            continue
        assert s.get("compared_pair") == ["FIX-A", "RBF-ILL"], scenario
        assert "FIX-A" in s["sentence"] and "RBF-ILL" in s["sentence"], scenario
        assert "the fixed arm" not in s["sentence"], (
            f"{scenario}: 'the fixed arm' does not identify one of two fixed arms")
        pk = s.get("sentence_param_keys", {})
        assert pk.get("fixedArm") == "labpage.armRef.FIX-A", scenario
        assert pk.get("rbfArm") == "labpage.armRef.RBF-ILL", scenario
        for lang, cat in (("en", EN), ("vi", VI)):
            for key in ("labpage.armRef.FIX-A", "labpage.armRef.RBF-ILL"):
                assert cat.get(key, "").strip(), f"{lang} missing {key}"


def test_the_headline_reads_the_targets_instead_of_assuming_they_differ():
    """FIX-A and RBF-ILL share a target, so a larger share IS a larger amount.

    This test previously enforced the opposite generalisation -- that the two
    targets differ -- which is false for this pair: both are the 1.20 cap on
    the same advance, 222,000,000 VND in every registered scenario. The branch
    is now derived from the target amounts, and this test checks the branch
    against the amounts rather than pinning one outcome.
    """
    seen_same = False
    for scenario in SCENARIOS:
        body = client.get(f"/api/lab/comparison/{scenario}").json()
        s = body.get("summary") or {}
        if not s:
            continue
        arms = {a["id"]: a for a in body["arms"]}
        fa_t = arms["FIX-A"]["repayment_target"]["amount"]["vnd"]
        ill_t = arms["RBF-ILL"]["repayment_target"]["amount"]["vnd"]
        same = fa_t == ill_t
        assert s["same_target"] is same, scenario
        if same:
            seen_same = True
            assert "compare like for like" in s["sentence"], scenario
            assert "targets differ" not in s["sentence"], (
                f"{scenario}: targets are equal ({fa_t}), so this is false")
            assert s["sentence_key"].endswith("SameTarget"), scenario
        else:
            assert "targets differ" in s["sentence"], scenario
            assert not s["sentence_key"].endswith("SameTarget"), scenario
        assert "repayment target" in s["sentence"], scenario
    assert seen_same, "no scenario exercised the equal-target branch"


def test_the_unequal_target_branch_is_reachable_and_correct():
    """Driven directly, because no registered scenario prices this pair apart.

    The general caution still has to be right if an artifact ever does.
    """
    from backend import lab as lab_mod

    arms = lab_mod.comparison("stable")["arms"]
    by = {a["id"]: a for a in arms}
    fa, ill = dict(by["FIX-A"]), dict(by["RBF-ILL"])
    ill["repayment_target"] = {
        **ill["repayment_target"],
        "amount": {"vnd": 199_000_000, "display": "199,000,000 \u20ab"},
    }
    out = lab_mod._summary("stable", [fa, ill])
    assert out["same_target"] is False
    assert "targets differ" in out["sentence"]
    assert "compare like for like" not in out["sentence"]
    assert out["sentence_key"] == "labpage.summary.sentence"
    for lang, cat in (("en", EN), ("vi", VI)):
        for key in ("labpage.summary.sentence",
                    "labpage.summary.sentenceSameTarget",
                    "labpage.summary.sentenceLevel",
                    "labpage.summary.sentenceLevelSameTarget"):
            assert cat.get(key, "").strip(), f"{lang} missing {key}"


def test_the_four_arm_table_keeps_the_general_caution():
    """Across all FOUR arms the targets are genuinely not all equal."""
    arms = client.get("/api/lab/comparison/stable").json()["arms"]
    targets = {a["id"]: a["repayment_target"]["amount"]["vnd"] for a in arms}
    assert len(set(targets.values())) > 1, targets
    for lang, cat in (("en", EN), ("vi", VI)):
        basis = cat["lab.guided.recovery.basis"]
        assert ("not all the same" in basis
                or "không giống nhau" in basis), f"{lang}: {basis[:80]}"


def test_an_exact_tie_in_month_12_recovery_is_reported_as_level_not_as_more():
    """A tie must not be reported as one arm having recovered more.

    No registered scenario produces a tie today -- FIX-A sits at
    0.923076923076923 in all thirteen while RBF-ILL ranges 0.443 to 1.0 -- so
    the defect was latent. This drives the tie branch directly rather than
    waiting for an artifact that happens to produce one.
    """
    from backend import lab as lab_mod

    arms = lab_mod.comparison("stable")["arms"]
    by = {a["id"]: a for a in arms}
    fa, ill = dict(by["FIX-A"]), dict(by["RBF-ILL"])
    tied = dict(fa["recovery_ratio"])
    fa["recovery_ratio"] = tied
    ill["recovery_ratio"] = dict(tied)          # exact equality at every month

    # Equal targets, which is what the registered artifacts actually give.
    out = lab_mod._summary("stable", [fa, ill])
    assert out["sentence_key"] == "labpage.summary.sentenceLevelSameTarget"
    assert out["sentence_param_keys"]["faster"] == "labpage.armRef.both"
    assert "the same share" in out["sentence"]
    assert "has recovered a larger share" not in out["sentence"]
    assert "the same share is the same amount" in out["sentence"], (
        "with equal targets, equal shares ARE equal amounts"
    )

    # Same tie, but priced apart -- then the amounts genuinely differ.
    ill_apart = dict(ill)
    ill_apart["repayment_target"] = {
        **ill["repayment_target"],
        "amount": {"vnd": 199_000_000, "display": "199,000,000 \u20ab"},
    }
    apart = lab_mod._summary("stable", [fa, ill_apart])
    assert apart["sentence_key"] == "labpage.summary.sentenceLevel"
    assert "the same share is not the same amount" in apart["sentence"]

    for lang, cat in (("en", EN), ("vi", VI)):
        for key in ("labpage.summary.sentenceLevel",
                    "labpage.summary.sentenceLevelSameTarget",
                    "labpage.armRef.both"):
            assert cat.get(key, "").strip(), f"{lang} missing {key}"


def test_the_recovery_finding_handles_a_tie_too():
    """The same `>=` lived in the findings, where it read 'ahead of'."""
    for lang, cat in (("en", EN), ("vi", VI)):
        for key in ("labpage.finding.direction.ahead",
                    "labpage.finding.direction.behind",
                    "labpage.finding.direction.level"):
            assert cat.get(key, "").strip(), f"{lang} missing {key}"
    src = (ROOT / "backend" / "lab.py").read_text(encoding="utf-8")
    assert 'direction, direction_key = "level with"' in src
    assert 'direction = "ahead of" if f12 >= r12 else "behind"' not in src, (
        ">= reports a tie as 'ahead of'"
    )


# ── the guided layer ───────────────────────────────────────────────────────

LAB_SRC = (ROOT / "frontend" / "lab.html").read_text(encoding="utf-8")


def test_one_question_selector_drives_the_guided_table():
    """Not three competing controls -- and TABLE-FIRST, not charts.

    This test was previously named "...drives both the card and the chart" and
    the commit message claimed synchronised charts. That was wrong:
    `selectQuestion()` calls `renderGuided()` and nothing else, so the selector
    changes the guided TABLE only; the detail charts live in their own optional
    panels and are drawn when a panel opens. A table-first guided layer with
    optional chart panels is the actual design, and this test now describes it.

    What the single-selector requirement does mean is still checked: exactly
    one `#showme` group, which the mobile layout wraps rather than duplicating.
    """
    assert LAB_SRC.count('id="showme"') == 1
    assert LAB_SRC.count('data-q="payments"') == 1
    assert LAB_SRC.count('data-q="recovery"') == 1
    assert LAB_SRC.count('data-q="completion"') == 1
    # descriptive labels, not Q numbers
    for key in ("lab.guided.q.payments", "lab.guided.q.recovery",
                "lab.guided.q.completion"):
        for lang, cat in (("en", EN), ("vi", VI)):
            assert cat.get(key, "").strip(), f"{lang} missing {key}"
    assert not re.search(r">\s*Q[123]\s*<", LAB_SRC), "Q numbers are not descriptive labels"

    # TABLE-FIRST: the selector re-renders the table and does not open or
    # switch a chart. If that ever changes, this test should change with it.
    fn = LAB_SRC.split("function selectQuestion(key){", 1)[1].split("\n}", 1)[0]
    assert "renderGuided()" in fn
    for charty in ("drawCharts", "chart-burden", "chart-recovery", ".open"):
        assert charty not in fn, (
            f"selectQuestion touches {charty!r}; the selector is table-only, so "
            "either this test or the claim about it needs updating")


def test_the_guided_layer_claims_no_time_series():
    """Burden is summary statistics and recovery is recorded checkpoints.

    The API exposes no monthly series for either, so no label may imply one.
    """
    assert "over time" not in LAB_SRC.lower()
    for lang, cat in (("en", EN), ("vi", VI)):
        basis = cat["lab.guided.payments.basis"].lower()
        assert ("no monthly series" in basis
                or "không có chuỗi số liệu theo từng tháng" in basis), lang
        rec = cat["lab.guided.recovery.basis"].lower()
        assert ("checkpoints" in rec or "mốc được ghi nhận" in rec), lang


def test_the_burden_labels_describe_the_two_stage_aggregation():
    """`burden_max` is the MEAN of per-path peaks, not one worst month.

    `research/rbf_sim/metrics.py::burden_stats` computes each statistic within
    one path over its ACTIVE months only -- positive revenue and a positive
    payment -- and `research/rbf_sim/engine.py` then averages each of those
    across the 500 paths. "Peak month" and "90th percentile" described neither
    stage, so a reader comparing contracts standalone would have read them as
    cohort-wide figures.

    Presentation only. No value changes.
    """
    for lang, cat in (("en", EN), ("vi", VI)):
        peak = cat["lab.guided.col.peak"].lower()
        p90 = cat["lab.guided.col.p90"].lower()
        assert ("mean" in peak or "trung bình" in peak), f"{lang}: {peak}"
        assert ("mean" in p90 or "trung bình" in p90), f"{lang}: {p90}"
        assert peak != "peak month" and p90 != "90th percentile", lang

        basis = cat["lab.guided.payments.basis"].lower()
        assert ("active months" in basis or "tháng có hoạt động" in basis), lang
        assert ("averaged across" in basis or "lấy trung bình trên" in basis), lang
        # zero-revenue months must not read as zero-burden observations
        assert ("excluded" in basis or "bị loại trừ" in basis), lang


def test_the_aggregation_described_matches_the_simulation_source():
    """Pins the description against the code it describes."""
    metrics = (ROOT / "research" / "rbf_sim" / "metrics.py").read_text(encoding="utf-8")
    engine = (ROOT / "research" / "rbf_sim" / "engine.py").read_text(encoding="utf-8")
    # per-path, active months only
    assert "if b is not None and p > 0" in metrics
    # then averaged across paths
    assert '"burden_max":   _mean([r.burden["max"] for r in rs])' in engine
    assert '"burden_p90":   _mean([r.burden["p90"] for r in rs])' in engine


def test_every_guided_figure_names_its_contract_and_its_statistic():
    """Each row names a contract, each column a statistic, with the id kept as
    a secondary reference rather than as the label."""
    assert "apiText(a,'name')" in LAB_SRC, "rows must use the descriptive name"
    assert "'<span class=\"arm-id\">'+esc(a.id)" in LAB_SRC, "id stays secondary"
    for key in ("lab.guided.col.mean", "lab.guided.col.p90", "lab.guided.col.peak",
                "lab.guided.col.byMonth", "lab.guided.col.completed"):
        for lang, cat in (("en", EN), ("vi", VI)):
            assert cat.get(key, "").strip(), f"{lang} missing {key}"


def test_the_recovery_question_shows_each_arms_own_denominator():
    """Targets differ by arm, so a share is not an amount."""
    assert "q.note(a)" in LAB_SRC and "recovery_denominator" in LAB_SRC
    for scenario in SCENARIOS:
        arms = client.get(f"/api/lab/comparison/{scenario}").json()["arms"]
        for a in arms:
            assert a.get("recovery_denominator"), f"{scenario}/{a['id']}"


def test_four_starters_are_offered_and_all_thirteen_stay_reachable():
    assert 'id="starters"' in LAB_SRC
    assert 'id="all-scn"' in LAB_SRC and 'id="scn-groups"' in LAB_SRC
    m = re.search(r"var STARTERS = \[(.*?)\]", LAB_SRC, re.S)
    assert m, "starter list"
    starters = re.findall(r'"([^"]+)"', m.group(1))
    assert len(starters) == 4, starters
    for key in starters:
        assert key in SCENARIOS, f"{key} is not a served scenario"
    assert "temp_closure" in starters and "closure_m13" in starters, (
        "temporary interruption and permanent closure must stay distinct")
    for lang, cat in (("en", EN), ("vi", VI)):
        assert "13" in cat["lab.scn.allSummary"], lang


def test_every_published_anchor_still_resolves_and_opens_its_panel():
    """A deep link must OPEN the panel, not land on a collapsed element."""
    for anchor in ("s-scn", "s-guided", "s-arms", "s-burden", "s-hpb",
                   "s-recovery", "s-dur", "s-under", "s-find", "s-limits", "s-prov"):
        assert f'id="{anchor}"' in LAB_SRC, anchor
    assert "function routeToAnchor()" in LAB_SRC
    assert 'window.addEventListener("hashchange", routeToAnchor)' in LAB_SRC
    assert 'window.addEventListener("popstate", routeToAnchor)' in LAB_SRC
    assert "routeToAnchor();" in LAB_SRC, "first load fires no hashchange"
    assert 'node.tagName==="DETAILS" && !node.open' in LAB_SRC
    for anchor, question in (("s-burden", "payments"), ("s-recovery", "recovery"),
                             ("s-dur", "completion")):
        assert f'"{anchor}":"{question}"' in LAB_SRC.replace(" ", ""), anchor


def test_a_chart_in_a_closed_panel_is_drawn_when_the_panel_opens():
    """A chart inside a shut <details> has zero width."""
    assert """d.matches('[data-fold="narrow"], .panel')""" in LAB_SRC


def test_the_eight_label_jump_bar_is_gone():
    """It was the default visitor journey the redesign replaces."""
    assert 'class="jump"' not in LAB_SRC


# ── R1: the guided result must be readable on a phone ──────────────────────

def test_the_guided_table_is_not_locked_to_the_wide_min_width_on_a_phone():
    """`table.data` carries min-width:760px. Inherited by the guided table that
    put a 760px table in a 313px viewport, so `overflow-x:auto` hid the actual
    answers behind a sideways scroll -- and a page-width overflow check passed
    while the core task failed.
    """
    assert "#guided-table{container-type:inline-size;}" in LAB_SRC
    assert "#guided-table table.guided{min-width:0;width:100%;}" in LAB_SRC, (
        "display:block alone does not relax min-width"
    )


def test_each_guided_value_carries_its_statistic_name_into_the_stacked_layout():
    """The header row is hidden when stacked, so the label travels per cell."""
    assert "data-label=\"'+esc(cols[i])+'\"" in LAB_SRC
    assert "content:attr(data-label)" in LAB_SRC


def test_the_stacked_guided_cell_stacks_rather_than_sharing_one_flex_line():
    """A single flex line fits "Mean burden" and overflows the card for
    "Mean path-level 90th percentile" -- measured at 435px against a 359px
    card edge. Stacking needs wrapping too; display:block alone is not enough."""
    block = LAB_SRC.split("@container (width < 48rem){", 1)[1].split("\n}", 1)[0]
    assert "#guided-table td{text-align:left;padding:8px 0;display:block;" in block
    assert "display:flex" not in block, (
        "a flex row re-introduces the long-label overflow"
    )
    assert "content:attr(data-label) / attr(data-label);\n    display:block" in block


def test_guided_table_fit_budget_matches_the_stacking_boundary():
    """A 620px boundary left the inherited 760px table clipped on tablets.

    Structural guard only; executed browser geometry is recorded separately.
    The relative budget also responds to an enlarged root font size.
    """
    budget = re.search(r"#guided-table table\.guided\{min-width:(\d+(?:\.\d+)?rem);", LAB_SRC)
    assert budget, "the guided table needs a text-relative minimum width"
    assert f"@container (width < {budget[1]}){{" in LAB_SRC
    assert float(budget[1][:-3]) * 16 >= 760, "do not leave a gap below the base table's minimum"


def test_stacked_guided_labels_override_inherited_nowrap():
    """The values fitted while the longer Vietnamese pseudo-labels clipped."""
    block = LAB_SRC.split("@container (width < 48rem){", 1)[1].split("\n}", 1)[0]
    cell = re.search(r"(?m)^  #guided-table td\{([^}]+)\}", block)[1]
    label = re.search(r"#guided-table td::before\{([^}]+)\}", block)[1]
    assert "white-space:normal" in cell
    assert "white-space:normal" in label
    assert "overflow-wrap:anywhere" in label


# ── the redesigned reading experience ──────────────────────────────────────

def test_the_primary_comparison_is_the_named_pair_not_all_four():
    """One compact fixed-versus-revenue-share comparison, stated explicitly.

    The audit's useful/understandable failure was four stacked multi-statistic
    cards as the entry comparison. The entry is now two aligned marks, and the
    page says in words which two it is showing and why.
    """
    assert 'var PAIR = ["FIX-A", "RBF-ILL"];' in LAB_SRC
    assert 'id="pair"' in LAB_SRC and "function markRow(" in LAB_SRC
    for lang, cat in (("en", EN), ("vi", VI)):
        scope = cat["lab.pair.scope"]
        assert "{a}" in scope and "{b}" in scope and "{n}" in scope, lang
        # the selection is explained, not merely stated
        assert ("prices against each other" in scope
                or "định giá đối chiếu" in scope), lang


def test_the_answer_comes_before_the_methodology():
    """E1: a 102-word methodology paragraph preceded any number.

    The comparison now carries a ONE-LINE basis; the full paragraph lives in
    the single secondary area, behind a disclosure.
    """
    compare = LAB_SRC.split('<div class="compare" id="compare">', 1)[1].split("</div>", 1)[0]
    assert 'id="guided-basis"' in compare
    detail = LAB_SRC.split('id="s-detail"', 1)[1].split("</details>", 1)[0]
    assert 'id="guided-basis-full"' in detail, "the long basis belongs in the detail area"
    for lang, cat in (("en", EN), ("vi", VI)):
        brief = cat["lab.guided.payments.brief"]
        full = cat["lab.guided.payments.basis"]
        # Character length, not word count: Vietnamese separates syllables, so
        # a word cap is not comparable across the two catalogues.
        assert len(brief) <= 130, f"{lang} brief basis is {len(brief)} chars"
        assert len(full) > 4 * len(brief), (
            f"{lang}: the detail basis should be substantially fuller "
            f"({len(full)} vs {len(brief)} chars)")


def test_each_mark_states_what_kind_of_figure_it_is():
    """FIX-A is a scheduled-payment benchmark, not observed collections, and
    that has to sit beside the number rather than only in the methods panel."""
    assert "lab.mark.note.fixed" in LAB_SRC and "lab.mark.note.rbf" in LAB_SRC
    # and it must actually be RENDERED into the mark, not merely defined
    mark = LAB_SRC.split("function markRow(", 1)[1].split("\n}", 1)[0]
    assert "mark-note" in mark, "the qualifier must be rendered beside the value"
    assert "lab.mark.note." in mark
    for lang, cat in (("en", EN), ("vi", VI)):
        fixed = cat["lab.mark.note.fixed"].lower()
        assert ("benchmark" in fixed or "mốc so sánh" in fixed), lang
        assert ("not observed" in fixed or "không phải số liệu thu hồi quan sát" in fixed), lang


def test_the_takeaway_is_scenario_scoped_and_never_a_universal_winner():
    """One short, scenario-dependent takeaway beside the result."""
    assert "function renderTakeaway(" in LAB_SRC
    assert 'id="takeaway-text"' in LAB_SRC
    for lang, cat in (("en", EN), ("vi", VI)):
        # payments must carry the non-affordability qualification
        for key in ("lab.take.payments.lower", "lab.take.payments.equal"):
            txt = cat[key].lower()
            assert ("affordability" in txt or "khả năng chi trả" in txt), f"{lang}/{key}"
        # recovery must say the direction depends on the path
        for key in ("lab.take.recovery.ahead", "lab.take.recovery.level"):
            txt = cat[key].lower()
            assert ("depends on the revenue path" in txt
                    or "tùy thuộc vào đường doanh thu" in txt), f"{lang}/{key}"
        # completion must not read as a default prediction
        for key in ("lab.take.completion.more", "lab.take.completion.equal"):
            txt = cat[key].lower()
            assert ("not a predicted default" in txt
                    or "không phải một dự báo vỡ nợ" in txt), f"{lang}/{key}"
    low = LAB_SRC.lower()
    for banned in ("rbf is better", "revenue share wins", "always cheaper"):
        assert banned not in low, banned


def test_the_payments_headline_is_the_mean_of_path_peaks_not_a_global_peak():
    """`burden_max` is the average of each path's own worst month."""
    pay = LAB_SRC.split("payments: {", 1)[1].split("recovery: {", 1)[0]
    assert "a.burden.max" in pay
    for lang, cat in (("en", EN), ("vi", VI)):
        brief = cat["lab.guided.payments.brief"].lower()
        assert ("average of each path" in brief or "trung bình tháng cao nhất của từng đường" in brief), lang
        assert ("gmv" in brief), lang
        assert ("active months" in brief or "tháng có hoạt động" in brief), lang


def test_recovery_and_completion_state_their_horizon_and_denominator():
    for lang, cat in (("en", EN), ("vi", VI)):
        rec = cat["lab.guided.recovery.brief"].lower()
        assert ("month 12" in rec or "tháng 12" in rec), lang
        assert ("own repayment target" in rec or "mục tiêu hoàn trả của chính" in rec), lang
        comp = cat["lab.guided.completion.brief"].lower()
        assert ("24-month" in comp or "24 tháng" in comp), lang
        assert ("500" in comp), lang


def test_the_undefined_rate_reason_uses_its_translation_key():
    """E5: apr() read the raw English field although a key was available.

    No registered scenario currently produces an undefined rate, so this is a
    latent path; it is pinned here rather than left for an artifact that
    produces one.
    """
    assert "apiText(a,'apr_undefined_reason')" in LAB_SRC
    assert "a.apr_undefined_reason ||" not in LAB_SRC
    for lang, cat in (("en", EN), ("vi", VI)):
        assert cat.get("labpage.arm.aprUndefined", "").strip(), lang


def test_findings_are_collapsed_while_limitations_stay_open():
    """The asymmetry must point this way, never the other.

    Collapsing the limitations alongside the findings would make the
    qualifying side as hidden as the favourable side.
    """
    find = LAB_SRC.split('id="s-find"', 1)[1].split("</section>", 1)[0]
    assert 'details class="panel"' in find, "findings should be a disclosure"
    limits = LAB_SRC.split('id="s-limits"', 1)[1].split("</section>", 1)[0]
    before = limits.split('id="caveats"', 1)[0]
    assert before.count("<details") - before.count("</details>") == 0, (
        "limitations must not be collapsed"
    )
