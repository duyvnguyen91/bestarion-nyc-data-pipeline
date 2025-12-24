# Jenkins Helm Release
# resource "helm_release" "jenkins" {
#   name             = "jenkins"
#   repository       = "https://charts.jenkins.io"
#   chart            = "jenkins"
#   version          = "5.8.114"
#   namespace        = var.jenkins_namespace
#   create_namespace = true

#   # values = [
#   #   file("${path.module}/jenkins.yaml")
#   # ]

#   depends_on = [
#     google_container_node_pool.default_pool,
#   ]
# }

