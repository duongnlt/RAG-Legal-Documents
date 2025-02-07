pipeline {
    agent any

    environment {
        registry = 'duonghust1919/rag-controller'
        registryCredential = 'dockerhub'
        imageTag = "$BUILD_NUMBER"
    }
    
    stages {
        stage('Build and Push') {
            steps {
                script {
                    echo 'Building RAG controller image ...'
                    def dockerImage = docker.build("${registry}:${imageTag}", "-f ./rag_controller/Dockerfile ./rag_controller")
                    echo 'Pushing image to dockerhub..'
                    docker.withRegistry( '', registryCredential ) {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Deploy') {
            agent {
                kubernetes {
                    containerTemplate {
                        name 'helm'
                        image 'duonghust1919/jenkins-k8s:latest'
                        alwaysPullImage true
                    }
                }
            }
            
            steps {
                script {
                    container('helm') {
                        sh("helm upgrade --install rag-controller ./rag_controller/helm_rag_controller --namespace rag-controller --set deployment.image.name=${registry} --set deployment.image.version=${imageTag}")
                    }
                }
            }
        }
    }
}