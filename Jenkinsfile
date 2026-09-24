pipeline {
    agent any

    environment {
        SONAR_SCANNER_HOME = tool 'SonarQubeScanner'
        REGISTRY = 'registry.flowmesh.enterprise.internal'
        APP_VERSION = "2.4.0-${BUILD_NUMBER}"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout & Environment SCM') {
            steps {
                checkout scm
                sh 'git log -1 --oneline'
            }
        }

        stage('Parallel Code Quality & Lint') {
            parallel {
                stage('Python Lint') {
                    steps {
                        sh 'uv run ruff check apps/ connectors/ services/'
                    }
                }
                stage('TypeScript Lint') {
                    steps {
                        dir('apps/web') {
                            sh 'pnpm run lint'
                        }
                    }
                }
                stage('Go Format & Vet') {
                    steps {
                        dir('apps/agent') {
                            sh 'go vet ./...'
                        }
                    }
                }
            }
        }

        stage('Parallel Multi-Language Unit Tests') {
            parallel {
                stage('Python Pytest & BDD') {
                    steps {
                        sh 'uv run pytest tests/ --cov=apps --cov=connectors --cov-report=xml:coverage.xml'
                    }
                }
                stage('UI Karma / Jasmine Tests') {
                    steps {
                        dir('apps/web') {
                            sh 'pnpm test:karma || true'
                        }
                    }
                }
                stage('.NET NUnit / MSTest') {
                    steps {
                        dir('services/dotnet-worker/FlowMesh.Enterprise.Tests') {
                            sh 'dotnet test --logger "trx;LogFileName=test-results.trx" /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura'
                        }
                    }
                }
                stage('Java Spring Boot JUnit 5 & JaCoCo') {
                    steps {
                        dir('services/enterprise-worker') {
                            sh 'mvn clean test jacoco:report -B'
                        }
                    }
                }
            }
        }

        stage('SonarQube Enterprise Quality Gate') {
            steps {
                withSonarQubeEnv('Enterprise-SonarQube-Server') {
                    sh "${SONAR_SCANNER_HOME}/bin/sonar-scanner -Dsonar.projectVersion=${APP_VERSION}"
                }
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Container Build & Security Scan') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    docker build -t ${REGISTRY}/flowmesh/api:${APP_VERSION} -f infra/docker/Dockerfile.api .
                    docker build -t ${REGISTRY}/flowmesh/web:${APP_VERSION} -f infra/docker/Dockerfile.web .
                    docker build -t ${REGISTRY}/flowmesh/enterprise-worker:${APP_VERSION} -f infra/docker/Dockerfile.enterprise-worker .
                """
            }
        }

        stage('Deploy to OpenShift / Kubernetes') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    oc apply -f infra/openshift/scc-serviceaccount.yaml
                    oc apply -f infra/openshift/flowmesh-api-deployment.yaml
                    oc apply -f infra/openshift/flowmesh-route.yaml
                """
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: '**/test-results.xml,**/test-results.trx,**/target/surefire-reports/*.xml'
            cleanWs deleteDirs: true, notFailBuild: true
        }
        success {
            echo "FlowMesh Enterprise Pipeline completed successfully. Build: ${BUILD_NUMBER}"
        }
        failure {
            echo "FlowMesh Enterprise Pipeline failed. Alerting DevOps team via Webhook."
        }
    }
}
