pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Test') {
            steps {
                echo 'Installing Python dependencies...'
                bat 'python -m pip install -r requirements.txt'

                echo 'Running unit tests with Pytest...'
                bat 'python -m pytest -v'
            }
        }

        stage('Build') {
            steps {
                echo 'Building Docker image...'
                bat 'docker build -t aceest-fitness-gym:%BUILD_NUMBER% .'
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying ACEest Fitness and Gym...'
                bat 'docker compose up -d --build'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the console output.'
        }
        always {
            echo 'Jenkins pipeline execution finished.'
        }
    }
}