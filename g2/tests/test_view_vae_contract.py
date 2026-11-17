import copy

import pytest

from g2.latent_cache.contract import (
    CacheError,
    contained,
    make_recipe,
    preprocessing_recipe,
    safe_relative,
    validate_recipe,
)


def test_recipe_detaches_dependencies_and_covers_precision_and_canvas():
    encoder = {"kind": "TEST_ONLY_FAKE", "weights_sha256": "a" * 64}
    a = make_recipe(encoder)
    encoder["weights_sha256"] = "b" * 64
    assert validate_recipe(a) == a
    assert make_recipe(encoder)["recipe_id"] != a["recipe_id"]
    assert (
        make_recipe(a["encoder"], storage_dtype="bfloat16")["recipe_id"]
        != a["recipe_id"]
    )
    assert (
        make_recipe(a["encoder"], preprocessing_recipe(128, 256))["recipe_id"]
        != a["recipe_id"]
    )
    bad = copy.deepcopy(a)
    bad["view_layout"] = "POOLED"
    with pytest.raises(CacheError):
        validate_recipe(bad)


@pytest.mark.parametrize("batch", [0, 2, True])
def test_no_unproved_mixed_batch(batch):
    with pytest.raises(CacheError, match="B=1"):
        make_recipe({"kind": "fake"}, batch_size=batch)


@pytest.mark.parametrize("config", [{}, [], False, ""])
def test_explicit_invalid_recipe_is_not_replaced_by_default(config):
    with pytest.raises(CacheError):
        make_recipe({"kind": "fake"}, preprocessing=config)


@pytest.mark.parametrize(
    "path",
    [
        ".",
        "../x.pt",
        "/x.pt",
        "sixview/../x.pt",
        "sixview//x.pt",
        "sixview/./x.pt",
        "a\\b.pt",
        "a\x00.pt",
        "",
    ],
)
def test_noncanonical_paths_refused(path):
    with pytest.raises(CacheError):
        safe_relative(path, ".pt")


def test_symlink_components_even_when_final_path_is_missing(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    (cache / "sixview").symlink_to(other, target_is_directory=True)
    with pytest.raises(CacheError, match="symbolic"):
        contained(cache, "sixview/floor_top.pt", allow_missing=True)
