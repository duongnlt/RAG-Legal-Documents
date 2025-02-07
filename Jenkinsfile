pipeline {
    agent any

    environment {
        registry = 'duonghust1919/rag-controller',
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
    }
}