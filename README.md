# ACEest Fitness and Gym — DevOps Assignment

A Python Tkinter desktop application demonstrating a CI/CD workflow using **Pytest**, **Docker**, **Docker Compose**, **Jenkins**, and **GitHub Actions**.

## Project Overview

ACEest Fitness and Gym provides workout and diet information for three fitness programs:

- **Fat Loss (FL)**
- **Muscle Gain (MG)**
- **Beginner (BG)**

The project uses automated tests to validate the program data and display-update logic. Jenkins runs the tests, builds a Docker image, and deploys the application. GitHub Actions uses a self-hosted Windows runner to trigger the Jenkins pipeline when code is pushed to `main`.

> **Note:** The application uses Tkinter, so it is a desktop GUI rather than a Flask/web application. Docker runs the GUI in a virtual X display and makes it viewable through noVNC in a browser.

## Technology Stack

- Python 3.12
- Tkinter
- Pytest
- Docker and Docker Compose
- Jenkins Pipeline
- GitHub Actions (self-hosted Windows x64 runner)
- Xvfb, x11vnc, Fluxbox, and noVNC

## Repository Structure

```text
devops-assignment/
├── app.py
├── tests/
│   └── test_app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── start.sh
├── Jenkinsfile
├── .gitignore
└── .github/
    └── workflows/
        └── trigger-jenkins.yml
```

The `actions-runner/` directory may exist on the local Windows machine for the self-hosted runner. It should not be committed to the repository.

## Prerequisites

### Run locally

- Windows 11 (or another supported desktop OS)
- Python 3.12
- Git

### Run with Docker and CI/CD

- Docker Desktop, running on Windows
- Docker Compose
- Jenkins, accessible at `http://localhost:8080`
- A GitHub repository
- A configured GitHub Actions self-hosted runner on the same Windows machine as Jenkins
- Python available to the Jenkins service account

## 1. Clone the Repository

Open PowerShell and run:

```powershell
git clone https://github.com/2025tm93069/devops-assignment.git
cd devops-assignment
```

If the repository is already cloned, navigate to its local directory instead.

## 2. Set Up and Run Locally

Check Python:

```powershell
python --version
```

Install the test dependency:

```powershell
python -m pip install -r requirements.txt
```

Run the application:

```powershell
python app.py
```

The Tkinter application window should open on the desktop. Select a fitness program to view its workout and diet information.

## 3. Run the Automated Tests

From the project root, run:

```powershell
python -m pytest -v
```

The tests cover the available program configuration, workout and diet data, color configuration, and the `update_display()` logic. The tests are designed to test the application logic without opening the actual Tkinter window.

## 4. Run with Docker Compose

Ensure Docker Desktop is running. From the directory containing `docker-compose.yml`, build and start the application:

```powershell
docker-compose up -d --build
```

Check the container:

```powershell
docker-compose ps
docker-compose logs -f
```

Open the GUI in a browser at:

**http://localhost:6080/vnc.html**

If prompted by noVNC, connect to `localhost:5900` only if the interface asks for a VNC host. Port `5900` is intended for the VNC connection inside the container and should not normally be published to the Windows host; the browser-facing noVNC service is exposed on port `6080`.

Stop the deployment:

```powershell
docker-compose down
```

### Docker port troubleshooting

If Docker reports that port `6080` is already allocated, identify the container publishing it:

```powershell
docker ps --filter "publish=6080"
```

If an obsolete container is using the port, stop and remove that specific container by its name or ID:

```powershell
docker rm -f <container-name-or-id>
```

Then retry:

```powershell
docker-compose up -d --build
```

Do not remove a container unless you have confirmed it is the obsolete deployment.

## 5. Jenkins Pipeline

The `Jenkinsfile` defines these stages:

1. **Test** — checks Python, installs dependencies, and runs Pytest.
2. **Docker Build** — builds a versioned image using the Jenkins build number.
3. **Deploy** — stops the previous Compose deployment and starts the updated application.

### Jenkins job configuration

Create a Jenkins **Pipeline** job named `aceest-app`, then configure:

- **Definition:** Pipeline script from SCM
- **SCM:** Git
- **Repository URL:** `https://github.com/2025tm93069/devops-assignment.git`
- **Branch Specifier:** `*/main`
- **Script Path:** `Jenkinsfile`

The Jenkins service must be able to access Python, Docker, and `docker-compose.exe`. The paths in the `Jenkinsfile` should match the installation paths on your machine. Docker Desktop must be running and available to the Windows account running Jenkins.

Run **Build Now** to test the pipeline manually and review **Console Output** for each stage.

## 6. GitHub Actions → Jenkins Trigger

The workflow at `.github/workflows/trigger-jenkins.yml` is configured to run on pushes to `main`. It runs on a self-hosted Windows runner and calls the Jenkins API to trigger the `aceest-app` job.

### Configure the self-hosted runner

In your GitHub repository, open **Settings → Actions → Runners → New self-hosted runner**, follow the Windows x64 setup instructions, and configure the runner on the same Windows machine where Jenkins is available at `http://localhost:8080`.

If your workflow uses:

```yaml
runs-on: [self-hosted, Windows, X64]
```

the runner must have all three labels. Keep the runner running and online for workflows to execute.

Do not commit the runner installation directory, its credentials, or configuration files to Git.

### Configure repository secrets

In GitHub, open **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|---|---|
| `JENKINS_USER` | Your Jenkins username |
| `JENKINS_TOKEN` | A Jenkins API token for that user |

Use a Jenkins API token, not the account password. Do not place credentials directly in the workflow file or commit them to source control.

### Trigger and verify

Commit and push a change to `main`:

```powershell
git add .
git commit -m "Update application or pipeline"
git push origin main
```

Then verify:

1. The workflow starts under the repository's **Actions** tab.
2. The self-hosted runner picks up the job.
3. The workflow successfully calls Jenkins.
4. The `aceest-app` job starts in Jenkins.
5. The Jenkins console output shows the test, build, and deployment stages.

The workflow's Jenkins URL is `http://localhost:8080`, which is appropriate when the GitHub Actions self-hosted runner and Jenkins run on the same Windows machine. A GitHub-hosted runner would not be able to use `localhost` to reach your local Jenkins instance.

## CI/CD Flow

```text
Developer pushes to main
          |
          v
GitHub Actions workflow
          |
          v
Self-hosted Windows runner
          |
          v
Trigger Jenkins job: aceest-app
          |
          v
Jenkins: install dependencies and run Pytest
          |
          v
Build Docker image
          |
          v
Deploy with Docker Compose
          |
          v
Open application at http://localhost:6080/vnc.html
```

## Common Issues

### Jenkins cannot find Python or Docker

The Jenkins service may run under a different Windows account from your interactive PowerShell session. Verify the executable paths in the `Jenkinsfile` and ensure the Jenkins service account has permission to use them.

### `docker compose` is unavailable in Jenkins

This setup uses the standalone `docker-compose.exe` path configured in the `Jenkinsfile`. Confirm that the file exists at that path or update the environment variable to match your installation.

### Docker reports port `6080` is already allocated

An older container or another process may already be listening on port `6080`. Check with:

```powershell
docker ps --filter "publish=6080"
netstat -ano | findstr :6080
```

Stop only the confirmed process or container that should no longer use the port, then rerun the deployment.

### GitHub Actions is queued or waiting

Check that the self-hosted runner is online and running, that the workflow's `runs-on` labels match the runner, and that `JENKINS_USER` and `JENKINS_TOKEN` are configured correctly.

### Tests fail

Run the tests locally with:

```powershell
python -m pytest -v
```

Review the failing test output before building or deploying.

## Security Notes

- Never commit Jenkins API tokens, runner credentials, or other secrets.
- Keep `actions-runner/`, Python caches, virtual environments, and test caches out of Git.
- Do not expose Jenkins publicly without appropriate authentication, access controls, and network security.
- Use only trusted source code and container images.

## Author / Assignment

This repository demonstrates automated testing and a containerized CI/CD workflow for the ACEest Fitness and Gym application.
