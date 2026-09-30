import zipfile
from typing import Final

from check_windows_wheel_install import (
    MAX_PATH,
    WORST_CASE_PREFIX,
    main,
    overlong_install_paths,
)


def _wheel(tmp_path, *entry_names):
    path = tmp_path / "pkg.whl"
    with zipfile.ZipFile(path, "w") as zf:
        for name in entry_names:
            zf.writestr(name, "{}")
    return str(path)


def test_flags_entry_one_char_over_budget(tmp_path):
    busts = "a" * (MAX_PATH - WORST_CASE_PREFIX + 1)
    assert overlong_install_paths(_wheel(tmp_path, busts)) == [busts]


def test_microsoft_store_prefix_flags_long_policy_templates(tmp_path):
    policy_template_prefix: Final = (
        "litellm/proxy/guardrails/guardrail_hooks/litellm_content_filter/policy_templates/"
    )
    filenames: Final = (
        "sg_pdpa_profiling_automated_decisions.yaml",
        "eu_ai_act_art5_emotion_recognition_fr.yaml",
        "eu_ai_act_art5_biometric_profiling_fr.yaml",
    )
    paths: Final = tuple(policy_template_prefix + filename for filename in filenames)
    assert overlong_install_paths(_wheel(tmp_path, *paths)) == list(paths)


def test_allows_entry_exactly_at_budget(tmp_path):
    at_limit = "a" * (MAX_PATH - WORST_CASE_PREFIX)
    assert (
        overlong_install_paths(_wheel(tmp_path, at_limit, "litellm/__init__.py")) == []
    )


def test_orders_offenders_longest_first(tmp_path):
    longer = "a" * (MAX_PATH - WORST_CASE_PREFIX + 5)
    shorter = "b" * (MAX_PATH - WORST_CASE_PREFIX + 1)
    assert overlong_install_paths(_wheel(tmp_path, shorter, longer)) == [
        longer,
        shorter,
    ]


def _dist_with(tmp_path, *entry_names):
    dist = tmp_path / "dist"
    dist.mkdir()
    with zipfile.ZipFile(dist / "litellm-0-py3-none-any.whl", "w") as zf:
        for name in entry_names:
            zf.writestr(name, "{}")


def test_lengths_only_passes_without_installing(tmp_path, monkeypatch):
    _dist_with(tmp_path, "litellm/__init__.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", "")
    assert main(["--lengths-only"]) == 0


def test_lengths_only_fails_on_an_overlong_path(tmp_path, monkeypatch):
    _dist_with(tmp_path, "a" * (MAX_PATH - WORST_CASE_PREFIX + 1))
    monkeypatch.chdir(tmp_path)
    assert main(["--lengths-only"]) == 1
