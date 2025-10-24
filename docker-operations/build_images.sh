#!/bin/bash
# Docker Images Build Script
# Bu script Test Controller image'ini build eder
echo "  DOCKER IMAGES BUILD SCRIPT"


# Docker'in calisip calismadigini kontrol et
echo " Docker kontrol ediliyor..."
if ! command -v docker &> /dev/null; then
    echo " Docker bulunamadi!"
    echo "Docker kurulumu: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo " Docker calismiyor!"
    echo "Docker daemon'u baslatin."
    exit 1
fi

echo " Docker calisiyor"
echo ""

# 1. Test Controller Image Build
echo " Building Test Controller Image..."

# Docker buildx kontrolu
if docker buildx version &> /dev/null; then
    echo "Using Docker Buildx"
    docker buildx build -f ../devops-kubernetes/devops-k8s-controller/Dockerfile.controller -t insider-test-controller:latest ..
else
    echo "Using legacy Docker build"
    DOCKER_BUILDKIT=0 docker build -f ../devops-kubernetes/devops-k8s-controller/Dockerfile.controller -t insider-test-controller:latest ..
fi

if [ $? -eq 0 ]; then
    echo " Test Controller image basariyla build edildi!"
else
    echo " Test Controller image build hatasi!"
    exit 1
fi

echo ""

# 2. Tag for Docker Hub
echo "========================================"
echo "  Tagging image for Docker Hub..."
echo "========================================"

DOCKER_USERNAME="${DOCKER_USERNAME:-YOUR_DOCKERHUB_USERNAME}"
docker tag insider-test-controller:latest $DOCKER_USERNAME/insider-test-controller:latest

if [ $? -eq 0 ]; then
    echo " Image basariyla tag'lendi: $DOCKER_USERNAME/insider-test-controller:latest"
else
    echo " Tag islemi basarisiz!"
    exit 1
fi

echo ""

# Summary
echo "========================================"
echo "  BUILD SUMMARY"
echo "========================================"
echo ""
echo "Built Images:"
docker images | grep insider-test-controller
echo ""
echo "Chrome Node: selenium/standalone-chrome:latest"
echo ""
echo " Build islemi tamamlandi!"
echo ""

