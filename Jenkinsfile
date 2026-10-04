pipeline {
    agent any

    triggers {
        pollSCM('H/1 * * * *')
    }

    stages {
        stage('Test') {
            steps {
                bat 'python -m pip install -r requirements.txt'
                bat 'python -m pytest -v'
            }
        }

        stage('Build') {
            steps {
                bat 'docker build -t aceest-fitness-gym:%BUILD_NUMBER% .'
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                bat 'docker compose up -d --build'
            }
        }
    }
}