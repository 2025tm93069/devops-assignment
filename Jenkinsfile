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

                echo 'Running Pytest...'

                bat 'python -m pytest -v'
            }
        }

        stage('Docker Build') {
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
            echo 'ACEest Fitness CI/CD pipeline completed successfully!'
        }

        failure {
            echo 'ACEest Fitness CI/CD pipeline failed. Check the console output.'
        }

        always {
            echo 'Jenkins pipeline execution finished.'
        }
    }
}
