pipeline {
    agent any

    stages {
        stage('Install Dependencies') {
            steps {
                bat 'py -m pip install -r requirements.txt'
            }
        }

        stage('Run Application') {
            steps {
                bat 'py app.py'
            }
        }
    }
}