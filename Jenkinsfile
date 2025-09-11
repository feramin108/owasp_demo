// Jenkinsfile - Declarative pipeline for demo
// Stages:
//  - Build (install requirements)
//  - SAST (Bandit)
//  - Dependency scan (Safety)
//  - Secrets scan (Gitleaks or gitleaks docker)
// Artifacts: archived JSON reports

pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = "1"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'python3 -m venv .venv || true'
                sh '. .venv/bin/activate && pip install --upgrade pip'
                sh '. .venv/bin/activate && pip install -r requirements.txt || true'
            }
        }

        stage('SAST - Bandit') {
            steps {
                // Bandit static analysis
                sh '. .venv/bin/activate && pip install bandit || true'
                sh '. .venv/bin/activate && bandit -r app -f json -o bandit-report.json || true'
            }
        }

        stage('Dependency Scan - Safety') {
            steps {
                // Safety checks for known vulnerable deps
                sh '. .venv/bin/activate && pip install safety || true'
                // --full-report is useful for demo
                sh '. .venv/bin/activate && safety check -r requirements.txt --full-report > safety-report.txt || true'
                sh 'python3 -c "import json, sys; print(\'Created safety-report.txt\')" || true'
            }
        }

        stage('Secrets Scan - Gitleaks (docker)') {
            steps {
                // Try to use gitleaks docker image (if Jenkins has docker)
                // This is resilient: if docker not available, the command might fail — allowed for demo
                sh 'docker run --rm -v $PWD:/repo zricethezav/gitleaks:latest detect --source /repo --report-path /repo/gitleaks-report.json || true'
            }
        }

        stage('Optional: Semgrep (Logic/Pattern scanning)') {
            steps {
                sh '. .venv/bin/activate && pip install semgrep || true'
                sh '. .venv/bin/activate && semgrep --config=p/ci -j 1 app || true'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'bandit-report.json, gitleaks-report.json, safety-report.txt', allowEmptyArchive: true
            junit allowEmptyResults: true, testResults: ''
        }
    }
}
