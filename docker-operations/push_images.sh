#!/bin/bash
# Docker Images Push Script
# Bu script Docker images'lari Docker Hub'a yukler

echo "  DOCKER IMAGES PUSH SCRIPT"
echo ""

# .env dosyasindan credentials yukle
if [ -f .env ]; then
    echo " .env dosyasindan credentials yukleniyor..."
    
    export $(cat .env | grep -v '^#' | xargs)
    
    if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
        echo ".env dosyasinda DOCKER_USERNAME veya DOCKER_PASSWORD bulunamadi!"
        echo "Manuel giris yapilacak..."
        echo ""
        read -p "Docker Hub kullanici adi: " DOCKER_USERNAME
        read -sp "Docker Hub sifresi: " DOCKER_PASSWORD
        echo ""
    else
        echo " Credentials yuklendi: $DOCKER_USERNAME"
    fi
else
    echo ".env dosyasi bulunamadi!"
    echo "Manuel giris yapilacak..."
    echo ""
    read -p "Docker Hub kullanici adi: " DOCKER_USERNAME
    read -sp "Docker Hub sifresi: " DOCKER_PASSWORD
    echo ""
fi

echo ""

# Docker Hub Login
echo " Docker Hub'a login olunuyor..."


echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

if [ $? -eq 0 ]; then
    echo " Docker Hub login basarili!"
else
    echo " Docker Hub login basarisiz!"
    echo "Kullanici adi ve sifrenizi kontrol edin."
    exit 1
fi

echo ""

# Push Test Controller Image
echo " Pushing Test Controller Image..."


docker push dogancan4040/insider-test-controller:latest

if [ $? -eq 0 ]; then
    echo " Test Controller image basariyla yuklendi!"
    echo "    https://hub.docker.com/r/dogancan4040/insider-test-controller"
else
    echo " Test Controller image yukleme hatasi!"
    docker logout
    exit 1
fi

echo ""
read -p "Versiyon tag'i olusturmak istiyor musunuz? (orn: v1.0.0) (y/N): " createVersionTag

if [ "$createVersionTag" = "y" ] || [ "$createVersionTag" = "Y" ]; then
    read -p "Versiyon numarasi girin (orn: v1.0.0): " version
    
    if [ -n "$version" ]; then
        echo ""
        echo "  Creating version tag: $version"
        
        # Tag
        docker tag dogancan4040/insider-test-controller:latest dogancan4040/insider-test-controller:$version
        
        # Push
        docker push dogancan4040/insider-test-controller:$version
        
        if [ $? -eq 0 ]; then
            echo " Version tag basariyla yuklendi: $version"
        fi
    fi
fi

echo ""

# Logout
echo " Docker Hub'dan cikis yapiliyor..."
docker logout
echo " Logout basarili"
echo ""

# Summary
echo "  PUSH SUMMARY"
echo ""

echo " Yuklenen images:"
echo "    dogancan4040/insider-test-controller:latest"

if [ -n "$version" ]; then
    echo "    Version: $version"
fi

echo ""
echo "Docker Hub Links:"
echo "    https://hub.docker.com/r/dogancan4040/insider-test-controller"

echo ""
echo " Push islemi tamamlandi!"

