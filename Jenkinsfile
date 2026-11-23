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

        // SONARQUBE CODE ANALYSIS + QUALITY GATE
        stage('SonarQube Analysis') {
            steps {
                echo 'Starting SonarQube code analysis...'

                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube') {
                        bat "\"${scannerHome}\\bin\\sonar-scanner.bat\" -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=600"
                    }
                }

                echo 'SonarQube analysis and Quality Gate completed successfully.'
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
                echo 'Stopping previous ACEest deployment...'
                bat '"%DOCKER_COMPOSE%" down || exit /b 0'
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