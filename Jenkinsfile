pipeline {
    agent any

    stages {
        stage('Install Dependencies') {
            steps {
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Run Application') {
            steps {
                bat 'python app.py'
            }
        }
    }
}