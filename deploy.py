import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROXY = "aceest-proxy"
COLORS = ("blue", "green")
UPSTREAM_PATH = "/etc/nginx/upstreams/active.conf"
HEALTH_TIMEOUT_SECONDS = 120


def command_result(command, *, check=True, capture_output=False, env=None):
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    if check and result.returncode:
        details = ""
        if capture_output:
            details = "\n".join(
                part for part in (result.stdout, result.stderr) if part
            )
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(map(str, command))}"
            + (f"\n{details}" if details else "")
        )
    return result


def docker(*args, check=True, capture_output=False):
    executable = os.environ.get("DOCKER", "docker")
    return command_result(
        [executable, *args], check=check, capture_output=capture_output
    )


def compose(*args, image, check=True, capture_output=False):
    executable = os.environ.get("DOCKER_COMPOSE", "docker-compose")
    env = os.environ.copy()
    env["APP_IMAGE"] = image
    return command_result(
        [executable, "--project-name", "aceest", "-f", "docker-compose.yml", *args],
        check=check,
        capture_output=capture_output,
        env=env,
    )


def proxy_configuration():
    result = docker(
        "exec", PROXY, "cat", UPSTREAM_PATH, check=False, capture_output=True
    )
    return result.stdout if result.returncode == 0 else ""


def configured_colors(configuration):
    return set(re.findall(r"server\s+aceest-(blue|green):6080\b", configuration))


def blue_green_target(configuration):
    active = configured_colors(configuration)
    if active == {"blue"}:
        return "green"
    if active == {"green"}:
        return "blue"
    return "blue"


def container_exists(color):
    return docker("inspect", f"aceest-{color}", check=False).returncode == 0


def container_running(name):
    result = docker(
        "inspect",
        "--format={{.State.Running}}",
        name,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def container_image(color):
    result = docker(
        "inspect",
        "--format={{.Config.Image}}",
        f"aceest-{color}",
        capture_output=True,
    )
    return result.stdout.strip()


def wait_until_healthy(color):
    deadline = time.monotonic() + HEALTH_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        result = docker(
            "inspect",
            "--format={{.State.Health.Status}}",
            f"aceest-{color}",
            check=False,
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(f"Container aceest-{color} disappeared during startup.")
        status = result.stdout.strip()
        if status == "healthy":
            return
        if status == "unhealthy":
            logs = docker("logs", "--tail", "50", f"aceest-{color}",
                          check=False, capture_output=True)
            raise RuntimeError(
                f"Container aceest-{color} is unhealthy.\n{logs.stdout}\n{logs.stderr}"
            )
        time.sleep(2)
    raise TimeoutError(
        f"Container aceest-{color} did not become healthy within "
        f"{HEALTH_TIMEOUT_SECONDS} seconds."
    )


def start_app(color, image):
    compose(
        "up", "-d", "--no-deps", "--no-build", "--force-recreate",
        f"aceest-{color}", image=image
    )
    wait_until_healthy(color)


def apply_upstream(configuration_name):
    source = ROOT / "deploy" / "nginx" / "upstreams" / configuration_name
    if not source.is_file():
        raise FileNotFoundError(f"Missing Nginx upstream configuration: {source}")

    with tempfile.TemporaryDirectory() as temporary_directory:
        backup = Path(temporary_directory) / "previous-upstream.conf"
        previous = docker(
            "cp", f"{PROXY}:{UPSTREAM_PATH}", str(backup),
            check=False, capture_output=True
        )
        if previous.returncode:
            raise RuntimeError(
                f"Could not read the current Nginx upstream configuration:\n"
                f"{previous.stderr}"
            )

        docker("cp", str(source), f"{PROXY}:{UPSTREAM_PATH}")
        validation = docker(
            "exec", PROXY, "nginx", "-t", check=False, capture_output=True
        )
        if validation.returncode:
            docker("cp", str(backup), f"{PROXY}:{UPSTREAM_PATH}")
            raise RuntimeError(
                f"Nginx rejected the new upstream configuration:\n"
                f"{validation.stdout}\n{validation.stderr}"
            )

        reload_result = docker(
            "exec", PROXY, "nginx", "-s", "reload",
            check=False, capture_output=True
        )
        if reload_result.returncode:
            docker("cp", str(backup), f"{PROXY}:{UPSTREAM_PATH}")
            docker("exec", PROXY, "nginx", "-t")
            docker("exec", PROXY, "nginx", "-s", "reload")
            raise RuntimeError(
                f"Nginx failed to load the new upstream configuration:\n"
                f"{reload_result.stdout}\n{reload_result.stderr}"
            )


def start_proxy(image):
    compose("up", "-d", "--no-deps", "aceest-proxy", image=image)
    docker("exec", PROXY, "nginx", "-t")


def deploy_blue_green(image):
    if container_exists(PROXY) and not container_running(PROXY):
        raise RuntimeError(
            "The ACEest proxy container exists but is stopped. Start or restore it "
            "before deploying."
        )
    configuration = proxy_configuration()
    if container_exists(PROXY) and not configured_colors(configuration):
        raise RuntimeError("Could not determine the proxy's active app slot.")
    target = blue_green_target(configuration)
    if configured_colors(configuration) == {"blue", "green"}:
        target = "green"
    print(f"Preparing the {target} slot.")
    start_app(target, image)

    if not container_exists(PROXY):
        if target != "blue":
            raise RuntimeError("The initial blue-green deployment must start in blue.")
        start_proxy(image)
    else:
        apply_upstream(f"{target}.conf")
    print(f"Traffic is now routed to the {target} slot.")


def deploy_rolling(image):
    if container_exists(PROXY) and not container_running(PROXY):
        raise RuntimeError(
            "The ACEest proxy container exists but is stopped. Start or restore it "
            "before deploying."
        )
    existing = [color for color in COLORS if container_exists(color)]
    if not existing:
        print("No existing deployment; creating both slots before enabling traffic.")
        for color in COLORS:
            start_app(color, image)
        start_proxy(image)
        apply_upstream("both.conf")
        return

    baseline_image = container_image(existing[0])
    for color in COLORS:
        if not container_exists(color):
            print(f"Starting the missing {color} slot on the currently deployed image.")
            start_app(color, baseline_image)

    if not container_exists(PROXY):
        start_proxy(image)

    apply_upstream("both.conf")
    for color in COLORS:
        print(f"Updating the {color} slot.")
        start_app(color, image)
        apply_upstream("both.conf")
    print("Both slots are running the new image.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Deploy ACEest app containers through the Nginx traffic proxy."
    )
    parser.add_argument("--strategy", choices=("blue-green", "rolling"), required=True)
    parser.add_argument("--image", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        if args.strategy == "blue-green":
            deploy_blue_green(args.image)
        else:
            deploy_rolling(args.image)
    except (OSError, RuntimeError) as error:
        print(f"Deployment failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
