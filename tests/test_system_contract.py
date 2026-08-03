"""Application-level contracts used by the competition runtime baseline."""

from server import config


def test_application_version_is_canonical():
    """The public runtime must expose one version used by docs and status APIs."""
    assert getattr(config, "APP_VERSION", None) == "4.2.0"


def test_personal_development_root_is_not_the_default():
    """A clean checkout must not depend on an absolute developer-only path."""
    assert str(config.TIANYAN_ROOT) != r"D:\Work space\天眼寻珍"
