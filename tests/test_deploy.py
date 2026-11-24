import sys
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import deploy


def result(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def test_command_result_returns_successful_result(monkeypatch):
    completed = result(stdout="ok")
    run = Mock(return_value=completed)
    monkeypatch.setattr(deploy.subprocess, "run", run)

    actual = deploy.command_result(["tool", "arg"], capture_output=True)

    assert actual is completed
    assert run.call_args.kwargs["cwd"] == deploy.ROOT
    assert run.call_args.kwargs["capture_output"] is True
    assert run.call_args.kwargs["check"] is False


def test_command_result_reports_failure_output(monkeypatch):
    monkeypatch.setattr(
        deploy.subprocess, "run", Mock(return_value=result(1, "out", "err"))
    )

    with pytest.raises(RuntimeError, match=r"(?s)Command failed.*out.*err"):
        deploy.command_result(["tool"], capture_output=True)


def test_command_result_can_return_nonzero_when_check_is_disabled(monkeypatch):
    monkeypatch.setattr(deploy.subprocess, "run", Mock(return_value=result(1)))

    assert deploy.command_result(["tool"], check=False).returncode == 1


def test_docker_uses_configured_executable(monkeypatch):
    run_command = Mock(return_value=result())
    monkeypatch.setenv("DOCKER", r"C:\tools\docker.exe")
    monkeypatch.setattr(deploy, "command_result", run_command)

    deploy.docker("inspect", "aceest-blue", check=False)

    assert run_command.call_args.args[0] == [
        r"C:\tools\docker.exe",
        "inspect",
        "aceest-blue",
    ]
    assert run_command.call_args.kwargs["check"] is False


def test_compose_sets_image_and_project(monkeypatch):
    run_command = Mock(return_value=result())
    monkeypatch.setenv("DOCKER_COMPOSE", r"C:\tools\docker-compose.exe")
    monkeypatch.setattr(deploy, "command_result", run_command)

    deploy.compose("up", "-d", image="aceest:test")

    command = run_command.call_args.args[0]
    assert command[:5] == [
        r"C:\tools\docker-compose.exe",
        "--project-name",
        "aceest",
        "-f",
        "docker-compose.yml",
    ]
    assert command[-2:] == ["up", "-d"]
    assert run_command.call_args.kwargs["env"]["APP_IMAGE"] == "aceest:test"


@pytest.mark.parametrize(
    ("configuration", "expected"),
    [
        ("server aceest-blue:6080;", "green"),
        ("server aceest-green:6080;", "blue"),
        ("", "blue"),
        ("server aceest-blue:6080;\nserver aceest-green:6080;", "blue"),
    ],
)
def test_blue_green_target(configuration, expected):
    assert deploy.blue_green_target(configuration) == expected


def test_configured_colors_ignores_unrelated_upstream_lines():
    configuration = (
        "server aceest-blue:6080 max_fails=1;\n"
        "server other-service:6080;\n"
        "server aceest-green:6080 max_fails=1;"
    )

    assert deploy.configured_colors(configuration) == {"blue", "green"}


@pytest.mark.parametrize(
    ("configuration", "expected"),
    [
        ("server aceest-blue:6080;", {"blue"}),
        ("server other-service:6080;", set()),
    ],
)
def test_proxy_configuration(configuration, expected, monkeypatch):
    monkeypatch.setattr(
        deploy,
        "docker",
        Mock(return_value=result(stdout=configuration)),
    )

    actual = deploy.proxy_configuration()

    assert deploy.configured_colors(actual) == expected


def test_proxy_configuration_returns_empty_if_container_exec_fails(monkeypatch):
    monkeypatch.setattr(deploy, "docker", Mock(return_value=result(1)))

    assert deploy.proxy_configuration() == ""


@pytest.mark.parametrize(
    ("returncode", "expected"),
    [(0, True), (1, False)],
)
def test_container_exists_inspects_exact_name(returncode, expected, monkeypatch):
    docker = Mock(return_value=result(returncode))
    monkeypatch.setattr(deploy, "docker", docker)

    assert deploy.container_exists("aceest-proxy") is expected
    docker.assert_called_once_with(
        "inspect", "aceest-proxy", check=False, capture_output=True
    )


@pytest.mark.parametrize(
    ("returncode", "stdout", "expected"),
    [(0, "true", True), (0, "false", False), (1, "", False)],
)
def test_container_running(returncode, stdout, expected, monkeypatch):
    monkeypatch.setattr(
        deploy,
        "docker",
        Mock(return_value=result(returncode, stdout)),
    )

    assert deploy.container_running("aceest-proxy") is expected


def test_container_image_strips_inspect_output(monkeypatch):
    monkeypatch.setattr(
        deploy,
        "docker",
        Mock(return_value=result(stdout="aceest-fitness-gym:12\n")),
    )

    assert deploy.container_image("blue") == "aceest-fitness-gym:12"


def test_wait_until_healthy_returns_when_healthy(monkeypatch):
    monkeypatch.setattr(
        deploy, "docker", Mock(return_value=result(stdout="healthy\n"))
    )

    deploy.wait_until_healthy("blue")


def test_wait_until_healthy_reports_disappeared_container(monkeypatch):
    monkeypatch.setattr(deploy, "docker", Mock(return_value=result(1)))

    with pytest.raises(RuntimeError, match="disappeared"):
        deploy.wait_until_healthy("blue")


def test_wait_until_healthy_includes_container_logs(monkeypatch):
    def fake_docker(*args, **kwargs):
        if args[0] == "inspect":
            return result(stdout="unhealthy")
        return result(stdout="app output", stderr="app error")

    monkeypatch.setattr(deploy, "docker", fake_docker)

    with pytest.raises(RuntimeError, match="app output") as error:
        deploy.wait_until_healthy("green")
    assert "app error" in str(error.value)


def test_wait_until_healthy_times_out(monkeypatch):
    ticks = iter((0, 1, 2, 3))
    monkeypatch.setattr(deploy.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(deploy.time, "sleep", Mock())
    monkeypatch.setattr(
        deploy, "docker", Mock(return_value=result(stdout="starting"))
    )
    monkeypatch.setattr(deploy, "HEALTH_TIMEOUT_SECONDS", 3)

    with pytest.raises(TimeoutError, match="did not become healthy"):
        deploy.wait_until_healthy("blue")


def test_start_app_recreates_service_then_waits(monkeypatch):
    compose = Mock()
    wait = Mock()
    monkeypatch.setattr(deploy, "compose", compose)
    monkeypatch.setattr(deploy, "wait_until_healthy", wait)

    deploy.start_app("green", "aceest-fitness-gym:12")

    compose.assert_called_once_with(
        "up",
        "-d",
        "--no-deps",
        "--no-build",
        "--force-recreate",
        "aceest-green",
        image="aceest-fitness-gym:12",
    )
    wait.assert_called_once_with("green")


def test_apply_upstream_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        deploy.apply_upstream("missing.conf")


def test_apply_upstream_requires_existing_proxy_configuration(monkeypatch):
    monkeypatch.setattr(deploy, "docker", Mock(return_value=result(1, stderr="no file")))

    with pytest.raises(RuntimeError, match="Could not read the current"):
        deploy.apply_upstream("blue.conf")


def test_apply_upstream_copies_valid_config_and_reloads(monkeypatch):
    docker = Mock(return_value=result())
    monkeypatch.setattr(deploy, "docker", docker)

    deploy.apply_upstream("blue.conf")

    calls = [call.args for call in docker.call_args_list]
    assert calls[0][:2] == ("cp", f"{deploy.PROXY}:{deploy.UPSTREAM_PATH}")
    assert calls[0][2]
    assert calls[1] == (
        "cp",
        str(deploy.ROOT / "deploy/nginx/upstreams/blue.conf"),
        f"{deploy.PROXY}:{deploy.UPSTREAM_PATH}",
    )
    assert calls[2] == ("exec", deploy.PROXY, "nginx", "-t")
    assert calls[3] == ("exec", deploy.PROXY, "nginx", "-s", "reload")


def test_apply_upstream_restores_backup_when_validation_fails(monkeypatch):
    calls = []

    def fake_docker(*args, **kwargs):
        calls.append(args)
        if args[:4] == ("exec", deploy.PROXY, "nginx", "-t"):
            return result(1, stderr="invalid upstream")
        return result()

    monkeypatch.setattr(deploy, "docker", fake_docker)

    with pytest.raises(RuntimeError, match="invalid upstream"):
        deploy.apply_upstream("blue.conf")

    assert calls[-1][0] == "cp"
    assert calls[-1][2] == f"{deploy.PROXY}:{deploy.UPSTREAM_PATH}"


def test_apply_upstream_restores_backup_when_reload_fails(monkeypatch):
    reloads = 0

    def fake_docker(*args, **kwargs):
        nonlocal reloads
        if args[:5] == ("exec", deploy.PROXY, "nginx", "-s", "reload"):
            reloads += 1
            if reloads == 1:
                return result(1, stderr="reload failed")
        return result()

    monkeypatch.setattr(deploy, "docker", fake_docker)

    with pytest.raises(RuntimeError, match="reload failed"):
        deploy.apply_upstream("green.conf")

    assert reloads == 2


def test_start_proxy_starts_compose_service_and_validates(monkeypatch):
    compose = Mock()
    docker = Mock()
    monkeypatch.setattr(deploy, "compose", compose)
    monkeypatch.setattr(deploy, "docker", docker)

    deploy.start_proxy("aceest-fitness-gym:12")

    compose.assert_called_once_with(
        "up",
        "-d",
        "--no-deps",
        "--remove-orphans",
        "aceest-proxy",
        image="aceest-fitness-gym:12",
    )
    docker.assert_called_once_with("exec", deploy.PROXY, "nginx", "-t")


def test_blue_green_initial_deployment_starts_blue_and_proxy(monkeypatch):
    monkeypatch.setattr(deploy, "container_exists", lambda name: False)
    start_app = Mock()
    start_proxy = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "start_proxy", start_proxy)

    deploy.deploy_blue_green("aceest-fitness-gym:12")

    start_app.assert_called_once_with("blue", "aceest-fitness-gym:12")
    start_proxy.assert_called_once_with("aceest-fitness-gym:12")


def test_blue_green_rejects_non_blue_initial_target(monkeypatch):
    monkeypatch.setattr(deploy, "container_exists", lambda name: False)
    monkeypatch.setattr(deploy, "blue_green_target", lambda configuration: "green")
    start_app = Mock()
    start_proxy = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "start_proxy", start_proxy)

    with pytest.raises(RuntimeError, match="initial blue-green deployment"):
        deploy.deploy_blue_green("aceest-fitness-gym:12")

    start_app.assert_called_once_with("green", "aceest-fitness-gym:12")
    start_proxy.assert_not_called()


@pytest.mark.parametrize(
    ("configuration", "expected_slot"),
    [
        ("server aceest-blue:6080;", "green"),
        ("server aceest-green:6080;", "blue"),
        ("server aceest-blue:6080;\nserver aceest-green:6080;", "green"),
    ],
)
def test_blue_green_deploys_inactive_slot_and_switches(
    configuration, expected_slot, monkeypatch
):
    monkeypatch.setattr(deploy, "container_exists", lambda name: True)
    monkeypatch.setattr(deploy, "container_running", lambda name: True)
    monkeypatch.setattr(deploy, "proxy_configuration", lambda: configuration)
    start_app = Mock()
    apply_upstream = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "apply_upstream", apply_upstream)

    deploy.deploy_blue_green("aceest-fitness-gym:12")

    start_app.assert_called_once_with(expected_slot, "aceest-fitness-gym:12")
    apply_upstream.assert_called_once_with(f"{expected_slot}.conf")


def test_blue_green_refuses_stopped_proxy(monkeypatch):
    monkeypatch.setattr(deploy, "container_exists", lambda name: True)
    monkeypatch.setattr(deploy, "container_running", lambda name: False)

    with pytest.raises(RuntimeError, match="proxy container exists but is stopped"):
        deploy.deploy_blue_green("aceest-fitness-gym:12")


def test_blue_green_refuses_unknown_active_slot(monkeypatch):
    monkeypatch.setattr(deploy, "container_exists", lambda name: True)
    monkeypatch.setattr(deploy, "container_running", lambda name: True)
    monkeypatch.setattr(deploy, "proxy_configuration", lambda: "")

    with pytest.raises(RuntimeError, match="Could not determine"):
        deploy.deploy_blue_green("aceest-fitness-gym:12")


def test_rolling_first_deployment_creates_both_slots(monkeypatch):
    monkeypatch.setattr(deploy, "container_exists", lambda name: False)
    start_app = Mock()
    start_proxy = Mock()
    apply_upstream = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "start_proxy", start_proxy)
    monkeypatch.setattr(deploy, "apply_upstream", apply_upstream)

    deploy.deploy_rolling("aceest-fitness-gym:12")

    assert start_app.call_args_list == [
        call("blue", "aceest-fitness-gym:12"),
        call("green", "aceest-fitness-gym:12"),
    ]
    start_proxy.assert_called_once_with("aceest-fitness-gym:12")
    apply_upstream.assert_called_once_with("both.conf")


def test_rolling_recovery_replaces_partial_slots_when_proxy_is_missing(monkeypatch):
    existing_names = {"aceest-blue"}
    monkeypatch.setattr(
        deploy,
        "container_exists",
        lambda name: name in existing_names,
    )
    start_app = Mock()
    start_proxy = Mock()
    apply_upstream = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "start_proxy", start_proxy)
    monkeypatch.setattr(deploy, "apply_upstream", apply_upstream)

    deploy.deploy_rolling("aceest-fitness-gym:12")

    assert start_app.call_args_list == [
        call("blue", "aceest-fitness-gym:12"),
        call("green", "aceest-fitness-gym:12"),
    ]
    start_proxy.assert_called_once_with("aceest-fitness-gym:12")
    apply_upstream.assert_called_once_with("both.conf")


def test_rolling_initializes_slots_when_proxy_has_no_backends(monkeypatch):
    monkeypatch.setattr(
        deploy, "container_exists", lambda name: name == deploy.PROXY
    )
    monkeypatch.setattr(deploy, "container_running", lambda name: True)
    start_app = Mock()
    start_proxy = Mock()
    apply_upstream = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "start_proxy", start_proxy)
    monkeypatch.setattr(deploy, "apply_upstream", apply_upstream)

    deploy.deploy_rolling("aceest-fitness-gym:12")

    assert start_app.call_args_list == [
        call("blue", "aceest-fitness-gym:12"),
        call("green", "aceest-fitness-gym:12"),
    ]
    start_proxy.assert_not_called()
    apply_upstream.assert_called_once_with("both.conf")


def test_rolling_update_adds_missing_slot_and_updates_each(monkeypatch):
    existing_names = {"aceest-proxy", "aceest-blue"}
    monkeypatch.setattr(
        deploy,
        "container_exists",
        lambda name: name in existing_names,
    )
    monkeypatch.setattr(deploy, "container_running", lambda name: True)
    monkeypatch.setattr(deploy, "container_image", lambda color: "aceest-old:7")
    start_app = Mock()
    start_proxy = Mock()
    apply_upstream = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "start_proxy", start_proxy)
    monkeypatch.setattr(deploy, "apply_upstream", apply_upstream)

    deploy.deploy_rolling("aceest-fitness-gym:12")

    assert start_app.call_args_list == [
        call("green", "aceest-old:7"),
        call("blue", "aceest-fitness-gym:12"),
        call("green", "aceest-fitness-gym:12"),
    ]
    start_proxy.assert_not_called()
    assert apply_upstream.call_count == 3


def test_rolling_update_keeps_existing_proxy_and_updates_both(monkeypatch):
    monkeypatch.setattr(deploy, "container_exists", lambda name: True)
    monkeypatch.setattr(deploy, "container_running", lambda name: True)
    monkeypatch.setattr(deploy, "container_image", lambda color: "aceest-old:7")
    start_app = Mock()
    start_proxy = Mock()
    apply_upstream = Mock()
    monkeypatch.setattr(deploy, "start_app", start_app)
    monkeypatch.setattr(deploy, "start_proxy", start_proxy)
    monkeypatch.setattr(deploy, "apply_upstream", apply_upstream)

    deploy.deploy_rolling("aceest-fitness-gym:12")

    assert start_app.call_args_list == [
        call("blue", "aceest-fitness-gym:12"),
        call("green", "aceest-fitness-gym:12"),
    ]
    start_proxy.assert_not_called()
    assert apply_upstream.call_count == 3


def test_rolling_refuses_stopped_proxy(monkeypatch):
    monkeypatch.setattr(deploy, "container_exists", lambda name: True)
    monkeypatch.setattr(deploy, "container_running", lambda name: False)

    with pytest.raises(RuntimeError, match="proxy container exists but is stopped"):
        deploy.deploy_rolling("aceest-fitness-gym:12")


@pytest.mark.parametrize("strategy", ["blue-green", "rolling"])
def test_parse_args(strategy, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["deploy.py", "--strategy", strategy, "--image", "aceest:test"],
    )

    args = deploy.parse_args()

    assert args.strategy == strategy
    assert args.image == "aceest:test"


def test_main_dispatches_blue_green(monkeypatch):
    monkeypatch.setattr(
        deploy, "parse_args", lambda: SimpleNamespace(
            strategy="blue-green", image="aceest:test"
        )
    )
    deployer = Mock()
    monkeypatch.setattr(deploy, "deploy_blue_green", deployer)

    assert deploy.main() == 0
    deployer.assert_called_once_with("aceest:test")


def test_main_reports_deployment_error(monkeypatch, capsys):
    monkeypatch.setattr(
        deploy, "parse_args", lambda: SimpleNamespace(
            strategy="rolling", image="aceest:test"
        )
    )
    monkeypatch.setattr(
        deploy, "deploy_rolling", Mock(side_effect=RuntimeError("deployment error"))
    )

    assert deploy.main() == 1
    assert "Deployment failed: deployment error" in capsys.readouterr().err
