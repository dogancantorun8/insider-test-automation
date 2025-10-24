# Docker Operation Scripts

This folder contains scripts for Docker image build and Docker Hub push operations.

## Files

- **`build_images.sh`** - Docker image build script
- **`push_images.sh`** - Docker Hub push script

## Usage

### 1. Build Images

```bash
cd insider/
chmod +x docker-operation-scripts/build_images.sh
./docker-operation-scripts/build_images.sh
```

**What happens:**
- Test Controller image is built
- Tagged for Docker Hub (`YOUR_USERNAME/insider-test-controller:latest`)
- Optional: Custom Chrome Node build (not recommended, use `selenium/standalone-chrome:latest`)

### 2. Push to Docker Hub

```bash
chmod +x docker-operation-scripts/push_images.sh
./docker-operation-scripts/push_images.sh
```

**What happens:**
- Logs into Docker Hub
- Pushes Test Controller image
- Optional: Can create version tags

### 3. Build & Push in One Command

```bash
./docker-operation-scripts/build_images.sh && ./docker-operation-scripts/push_images.sh
```

## Configuration

### Docker Hub Credentials

**Method 1: Environment Variables**
```bash
export DOCKER_USERNAME="your_username"
export DOCKER_PASSWORD="your_password"
```

**Method 2: .env File** (Recommended)
```env
DOCKER_USERNAME=your_username
DOCKER_PASSWORD=your_password
```

**Method 3: Inside Script** (push_images.sh)
```bash
DOCKER_USERNAME="your_username"
DOCKER_PASSWORD="your_password"
```

## Notes

1. **Scripts must be run from project root directory**
   ```bash
   # Correct
   ./docker-operation-scripts/build_images.sh
   
   # Wrong
   cd docker-operation-scripts
   ./build_images.sh
   ```

2. **Chrome Node build is NOT REQUIRED**
   - Kubernetes manifests use `selenium/standalone-chrome:latest`
   - Selenium's official image is pulled directly from Docker Hub
   - Custom build not necessary

3. **Image name update is required**
   - In `k8s/controller-deployment.yaml`:
   - `image: YOUR_DOCKERHUB_USERNAME/insider-test-controller:latest`
   - Write your Docker Hub username

4. **Don't commit credentials to Git**
   - `.env` file is in `.gitignore`
   - Use environment variables

## Troubleshooting

### Docker not running
```bash
# Windows: Start Docker Desktop
# Linux/Mac:
sudo systemctl start docker
```

### Permission denied
```bash
chmod +x docker-operation-scripts/*.sh
```

### Login failed
```bash
# Test manual login
docker login -u YOUR_USERNAME
```

### Image build error
```bash
# Clean Docker cache
docker system prune -a

# Rebuild
./docker-operation-scripts/build_images.sh
```

## Related Files

- `../devops-k8s-controller/Dockerfile.controller` - Controller Dockerfile
- `../k8s/controller-deployment.yaml` - Controller deployment
- `../k8s/chrome-node-deployment.yaml` - Chrome Node deployment (selenium/standalone-chrome:latest)
- `../deploy_k8s.py` - Kubernetes deployment script

## Build Flow

```
1. build_images.sh is executed
   ↓
2. devops-k8s-controller/Dockerfile.controller is built
   ↓
3. Image is tagged (YOUR_USERNAME/insider-test-controller:latest)
   ↓
4. push_images.sh is executed
   ↓
5. Login to Docker Hub
   ↓
6. Controller image is pushed
   ↓
7. (Optional) Version tag is created (v1.0.0, v1.0.1, etc.)

NOTE: Chrome Node build is NOT REQUIRED - selenium/standalone-chrome:latest is used
```
