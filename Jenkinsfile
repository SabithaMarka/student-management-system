pipeline {
    agent any

    stages {
        stage('Install Dependencies') {
            steps {
                bat '"C:\\Users\\sabit\\AppData\\Local\\Programs\\Python\\Python315\\python.exe" -m pip install -r requirements.txt'
            }
        }

        stage('Run Application') {
            steps {
                bat '"C:\\Users\\sabit\\AppData\\Local\\Programs\\Python\\Python315\\python.exe" app.py'
            }
        }
    }
}