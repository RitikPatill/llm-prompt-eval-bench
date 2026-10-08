def test_package_importable():
    import eval_bench  # noqa: F401


def test_cli_importable():
    from eval_bench.cli import app
    assert app is not None
