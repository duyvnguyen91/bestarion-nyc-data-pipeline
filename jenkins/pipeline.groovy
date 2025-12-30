pipeline {
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
      - /busybox/sh
      - -c
      - sleep infinity
    tty: true
    volumeMounts:
      - name: kaniko-cache
        mountPath: /kaniko/cache
  volumes:
    - name: kaniko-cache
      emptyDir: {}
"""
    }
  }

  environment {
    PROJECT_ID = "civil-treat-482015-n6"
    REGION     = "asia-east1"
    REPO       = "airflow"
    IMAGE_NAME = "airflow"
    IMAGE_URI  = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}"
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main',
            url: 'https://github.com/duyvnguyen91/bestarion-nyc-data-pipeline.git'
      }
    }

    stage('Build & Push Image') {
      steps {
        container('kaniko') {
          sh '''
            /kaniko/executor \
              --context ${WORKSPACE}/docker \
              --dockerfile ${WORKSPACE}/docker/Dockerfile \
              --destination ${IMAGE_URI}:${BUILD_NUMBER} \
              --destination ${IMAGE_URI}:latest \
              --cache=true \
              --cache-repo=${IMAGE_URI}-cache
          '''
        }
      }
    }
  }
}