# docker rmi django_hisup_explorer:0.0.1
docker build -t django_hisup_explorer:0.0.1 ./app
kind load docker-image django_hisup_explorer:0.0.1
kubectl apply -f k8s/django/deployment.yaml
kubectl apply -f k8s/django/service.yaml
