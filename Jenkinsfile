pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOYMENT_STRATEGY',
            choices: ['blue-green', 'rolling'],
            description: 'Choose how the new Docker image is deployed.'
        )
    }

    options {
        timestamps()
    }

    environment {
        PYTHON = 'C:\\Users\\chella\\AppData\\Local\\Python\\pythoncore-3.12-64\\python.exe'
        DOCKER = 'C:\\Users\\chella\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        DOCKER_COMPOSE = 'C:\\Users\\chella\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker-compose.exe'
        JAVA_HOME = 'C:\\Users\\chella\\AppData\\Local\\Programs\\Eclipse Adoptium\\jdk-21.0.12.101-hotspot'
    }

    stages {
        stage('Test') {
            steps {
                echo 'Checking Python installation...'
                bat '"%PYTHON%" --version'
                echo 'Installing Python dependencies...'
                bat '"%PYTHON%" -m pip install -r requirements.txt'
                echo 'Running Pytest and generating the SonarQube coverage report...'
                bat '"%PYTHON%" -m pytest --cov=. --cov-report=xml:coverage.xml -v'
            }
        }

        // SONARQUBE CODE ANALYSIS + QUALITY GATE
        stage('SonarQube Analysis') {
            steps {
                echo 'Starting SonarQube code analysis...'
                bat '"%JAVA_HOME%\\bin\\java.exe" -version'

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
                echo "Deploying with the ${params.DEPLOYMENT_STRATEGY} strategy..."
                bat '"%DOCKER_COMPOSE%" version'
                bat '"%PYTHON%" deploy.py --strategy "%DEPLOYMENT_STRATEGY%" --image "aceest-fitness-gym:%BUILD_NUMBER%"'
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