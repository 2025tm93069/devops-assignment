from deploy import blue_green_target, configured_colors


def test_blue_green_target_uses_inactive_slot():
    assert blue_green_target("server aceest-blue:6080;") == "green"
    assert blue_green_target("server aceest-green:6080;") == "blue"


def test_blue_green_target_defaults_to_blue_without_single_active_slot():
    assert blue_green_target("") == "blue"
    assert blue_green_target(
        "server aceest-blue:6080;\nserver aceest-green:6080;"
    ) == "blue"


def test_configured_colors_ignores_unrelated_upstream_lines():
    configuration = (
        "server aceest-blue:6080 max_fails=1;\n"
        "server other-service:6080;\n"
        "server aceest-green:6080 max_fails=1;"
    )

    assert configured_colors(configuration) == {"blue", "green"}
