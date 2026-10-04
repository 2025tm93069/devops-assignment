pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        PYTHON = 'C:\\Users\\chella\\AppData\\Local\\Python\\pythoncore-3.12-64\\python.exe'
        DOCKER = 'C:\\Users\\chella\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        DOCKER_COMPOSE = 'C:\\Users\\chella\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe'
    }

    stages {

        stage('Test') {
            steps {
                echo 'Checking Python installation...'
                bat '"%PYTHON%" --version'

                echo 'Installing Python dependencies...'
                bat '"%PYTHON%" -m pip install -r requirements.txt'

                echo 'Running Pytest...'
                bat '"%PYTHON%" -m pytest -v'
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Checking Docker installation...'
                bat '"%DOCKER%" --version'

                echo 'Building Docker image...'
                bat '"%DOCKER%" build -t aceest-fitness-gym:%BUILD_NUMBER% .'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Checking Docker Compose...'
                bat '"%DOCKER_COMPOSE%" version'

                echo 'Removing previous ACEest container if it exists...'
                bat '"%DOCKER%" rm -f aceest-app-aceest-app-1 2>NUL || exit /b 0'

                echo 'Deploying ACEest Fitness and Gym...'
                bat '"%DOCKER_COMPOSE%" up -d --build'

                echo 'ACEest Fitness and Gym deployment completed.'
            }
        }
    }

    post {
        success {
            echo 'ACEest Fitness CI/CD pipeline completed successfully!'
        }

        failure {
            echo 'Jenkins pipeline execution failed. Check the console output.'
        }

        always {
            echo 'Jenkins pipeline execution finished.'
        }
    }
}