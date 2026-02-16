# Docker Image Changelog

## Previous: AWS Base Image (v1)

**Date:** 2026-02-16
**Status:** Replaced by v2

### Base Image

```
public.ecr.aws/lambda/python:3.12-arm64
```

- AWS-managed Python 3.12 Lambda base image
- Architecture: ARM64 (Graviton2)
- OS: Amazon Linux 2023 (minimal)
- Includes: Lambda runtime, runtime interface client, runtime interface emulator

### Dockerfile

```dockerfile
FROM public.ecr.aws/lambda/python:3.12-arm64
COPY handler.py ${LAMBDA_TASK_ROOT}/
CMD ["handler.handler"]
```

### What's Included

- No external dependencies (no `requirements.txt`)
- Single handler file copied to `${LAMBDA_TASK_ROOT}/`
- Handler entrypoint: `handler.handler`

### CDK Configuration

- `DockerImageFunction` with `Platform.LINUX_ARM64`
- Memory: 128 MB
- Timeout: 10 seconds
- Function URL: public (no auth)
- CDK builds the image and pushes to its managed ECR repo automatically

### ECR Image

- **Digest:** `sha256:08df1b61e4fbdad81a2ceaf1aa61f52e53b38923682b7e218a8bee76c4160653`
- **Tag:** `b12f46355b44e3f4c92084b4c8786fcb30b6f2bab55aeac5d14d7e5557fb0fe7`
- **Size:** 183.5 MB

### Vulnerability Scan Results

| Severity | Count |
|----------|-------|
| HIGH     | 5     |
| MEDIUM   | 4     |
| LOW      | 3     |
| **Total** | **12** |

Notable CVEs: CVE-2025-61731, CVE-2025-15467, CVE-2025-68119, CVE-2025-13151 (all HIGH)

### Notes

- This is the simplest setup using the AWS-provided base image
- No `--provenance=false` needed since CDK handles the Docker build
- No `USER` instruction needed; Lambda sets a least-privilege user automatically
- Python 3.12 base image deprecation date: Oct 2028

---

## Previous: Custom Base Image (v2)

**Date:** 2026-02-16
**Status:** Replaced by v3

### Base Image

```
python:3.13-slim (runtime stage)
python:3.13 (build stage)
```

- Official Python Docker image (Debian-based), not AWS-managed
- Architecture: ARM64 (via CDK `Platform.LINUX_ARM64`)
- Multi-stage build: full image for compilation, slim for runtime
- Requires `awslambdaric` -- the Lambda runtime interface client

### Dockerfile

```dockerfile
ARG FUNCTION_DIR="/function"

FROM python:3.13 AS build-image
ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}
COPY handler.py ${FUNCTION_DIR}
RUN pip install --target ${FUNCTION_DIR} awslambdaric

FROM python:3.13-slim
ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "handler.handler" ]
```

### What Changed from v1

| Aspect | v1 (AWS base) | v2 (Custom) |
|--------|---------------|-------------|
| Base image | `public.ecr.aws/lambda/python:3.12-arm64` | `python:3.13-slim` |
| Python version | 3.12 | 3.13 |
| Runtime client | Built into base image | Manually installed via `awslambdaric` |
| Build strategy | Single stage | Multi-stage (build + slim runtime) |
| Function dir | `${LAMBDA_TASK_ROOT}` (AWS-defined) | `/function` (custom) |
| Entrypoint | Handled by base image | Explicit `ENTRYPOINT` for `awslambdaric` |
| OS | Amazon Linux 2023 | Debian (bookworm) |
| Image size | 183.5 MB | 45.0 MB |
| Vulnerabilities | 12 (5 HIGH) | 1 (0 HIGH) |

### ECR Image

- **Digest:** `sha256:99857773794537ac785b12ca135b44ad46afdef504bbb4b77ffd654210035b98`
- **Tag:** `0f08869223988f1fbf24bf935cc2c5d30f3d43378269cfc39476b874b3493a20`
- **Size:** 45.0 MB

### Vulnerability Scan Results

| Severity | Count |
|----------|-------|
| HIGH     | 0     |
| MEDIUM   | 1     |
| LOW      | 0     |
| **Total** | **1** |

CVEs: CVE-2025-7709 (MEDIUM)

### CDK Configuration

- No changes to `stack.py` -- CDK still builds and pushes the image
- `Platform.LINUX_ARM64` still handles ARM64 cross-compilation

### Notes

- `awslambdaric` is required for any non-AWS base image to work with Lambda
- No runtime interface emulator included -- local testing requires mounting it externally
- No `USER` instruction needed; Lambda sets least-privilege user automatically
- Multi-stage build keeps the final image smaller by excluding build tools
- 75% smaller image and 92% fewer vulnerabilities compared to v1

---

## Current: Docker Hardened Image (v3)

**Date:** 2026-02-16
**Status:** Deployed

### Base Image

```
dhi.io/python:3.13 (runtime stage)
python:3.13 (build stage)
```

- Docker Hardened Image (DHI) -- security-hardened Python runtime
- Architecture: ARM64 (confirmed via `docker inspect` and Lambda config)
- Multi-stage build: standard Python for compilation, DHI for runtime
- Requires `awslambdaric` -- the Lambda runtime interface client

### Dockerfile

```dockerfile
ARG FUNCTION_DIR="/function"

FROM python:3.13 AS build-image
ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}
COPY handler.py ${FUNCTION_DIR}
RUN pip install --target ${FUNCTION_DIR} awslambdaric

FROM dhi.io/python:3.13
ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
ENTRYPOINT [ "/opt/python/bin/python", "-m", "awslambdaric" ]
CMD [ "handler.handler" ]
```

### What Changed from v2

| Aspect | v2 (Custom) | v3 (DHI) |
|--------|-------------|----------|
| Runtime image | `python:3.13-slim` | `dhi.io/python:3.13` |
| Build image | `python:3.13` (unchanged) | `python:3.13` (unchanged) |
| Python path | `/usr/local/bin/python` | `/opt/python/bin/python` |
| Security posture | Standard Debian slim | Docker Hardened Image |
| Image size | 45.0 MB | 27.0 MB |
| `awslambdaric` | Yes (unchanged) | Yes (unchanged) |
| Multi-stage build | Yes (unchanged) | Yes (unchanged) |

### CDK Configuration

- No changes to `stack.py` -- CDK still builds and pushes the image
- `Platform.LINUX_ARM64` still handles ARM64 cross-compilation

### ECR Image

- **Digest:** `sha256:cb2092ae9ad0845a283f0e2bc6c1cb01145507b822c058d5b227f478599e022d`
- **Tag:** `25dd5ffa31c4bfe886c32ea6f792bd0b48e2ec7fbf77d9c00701fd65af3ed3b2`
- **Size:** 27.0 MB

### Vulnerability Scan Results

ECR basic scanning does not support the DHI OS. Scanned via `docker scout cves dhi.io/python:3.13`:

| Severity | Count |
|----------|-------|
| CRITICAL | 0     |
| HIGH     | 0     |
| MEDIUM   | 0     |
| LOW      | 10    |
| **Total** | **10** |

All 10 LOW findings are unfixed upstream issues in 4 packages:

| Package | CVE Count | Notable CVEs |
|---------|-----------|-------------|
| glibc 2.41-12 | 7 | CVE-2019-9192, CVE-2019-1010025, CVE-2010-4756 |
| util-linux 2.41-5 | 1 | CVE-2022-0563 |
| openssl 3.5.4 | 1 | CVE-2010-0928 |
| sqlite3 3.46.1-7 | 1 | CVE-2021-45346 |

48 packages indexed, 29 MB image. Zero CRITICAL, HIGH, or MEDIUM vulnerabilities.

### Notes

- Only the runtime stage changed; the build stage still uses `python:3.13` for pip/compilation
- DHI images are pre-hardened with reduced attack surface, fewer packages, and patched CVEs
- Docker credentials for `dhi.io` are required to pull the image during CDK build
- Python binary is at `/opt/python/bin/python` (not `/usr/local/bin/python`) -- initial deploy failed with `Runtime.InvalidEntrypoint` until this was corrected
- DHI image is extremely minimal -- no `which`, no shell utilities; debugging inside the container is limited
- 40% smaller than v2, 85% smaller than v1

---

## Version Summary

| Version | Base Image | Size | Vulnerabilities |
|---------|-----------|------|-----------------|
| v1 | `public.ecr.aws/lambda/python:3.12-arm64` | 183.5 MB | 12 (5 HIGH) |
| v2 | `python:3.13-slim` | 45.0 MB | 1 (0 HIGH) |
| v3 | `dhi.io/python:3.13` | 27.0 MB | 10 (0 HIGH, 10 LOW) |

**Note:** Stack destroyed and ECR repository (`cdk-hnb659fds-container-assets-<ACCOUNT_ID>-us-east-1`) manually cleaned up on 2026-02-16. All images (v1, v2, v3) no longer exist in ECR.

---

## Architecture Switch Test (x86_64 → ARM64)

**Date:** 2026-02-16

Tested whether CDK/CloudFormation can switch a running Lambda function's architecture in-place without destroying and recreating.

### Steps

1. Modified `stack.py` to use `Platform.LINUX_AMD64` and `Architecture.X86_64`
2. Deployed the stack -- Lambda created with x86_64 architecture
3. Verified function URL returned `{"message": "Hello from Lambda on ARM64!"}` and `Architectures: ["x86_64"]`
4. Modified `stack.py` back to `Platform.LINUX_ARM64` and `Architecture.ARM_64`
5. Redeployed the stack -- CloudFormation updated the function in-place

### Results

| Phase | Architecture | Function URL | Status |
|-------|-------------|-------------|--------|
| Deploy 1 | x86_64 | `https://bxjb3yna3eced2pxg2hz5xzrfa0whzrg.lambda-url.us-east-1.on.aws/` | Working |
| Deploy 2 | arm64 | Same URL (unchanged) | Working |

### Findings

- CloudFormation handles the architecture switch as an **in-place update** -- no resource replacement needed
- The function URL remains the same across the architecture change -- no disruption
- The Dockerfile did not need to change -- `dhi.io/python:3.13` is multi-arch and Docker pulls the correct variant based on the `--platform` flag
- The DHI python path (`/opt/python/bin/python`) is the same on both x86_64 and arm64 variants

---

## Verification Commands

Commands to verify a deployed image and Lambda function.

### Check Lambda architecture

```bash
# Get function name
aws lambda list-functions \
  --query "Functions[?starts_with(FunctionName, 'HelloLambda')].FunctionName" \
  --output text

# Verify ARM64 architecture
aws lambda get-function-configuration \
  --function-name <FUNCTION_NAME> \
  --query "Architectures" \
  --output json
```

### Check ECR image architecture

```bash
# List images in CDK-managed ECR repo
aws ecr describe-images \
  --repository-name cdk-hnb659fds-container-assets-<ACCOUNT_ID>-us-east-1 \
  --query "imageDetails | sort_by(@, &imagePushedAt)" \
  --output json

# Get image manifest to inspect architecture
aws ecr batch-get-image \
  --repository-name cdk-hnb659fds-container-assets-<ACCOUNT_ID>-us-east-1 \
  --image-ids imageDigest=<DIGEST> \
  --query "images[0].imageManifest" \
  --output text
```

Then parse the config blob digest from the manifest and fetch it:

```bash
aws ecr batch-get-image \
  --repository-name cdk-hnb659fds-container-assets-<ACCOUNT_ID>-us-east-1 \
  --image-ids imageDigest=<DIGEST> \
  --query "images[0].imageManifest" \
  --output text | python3 -c "
import sys, json
manifest = json.load(sys.stdin)
print(json.dumps(manifest, indent=2))
" # Look for "architecture": "arm64" in the config
```

### Check ECR vulnerability scan results

```bash
# Scan severity summary
aws ecr describe-image-scan-findings \
  --repository-name cdk-hnb659fds-container-assets-<ACCOUNT_ID>-us-east-1 \
  --image-id imageDigest=<DIGEST> \
  --query "imageScanFindings.findingSeverityCounts" \
  --output json

# Detailed findings
aws ecr describe-image-scan-findings \
  --repository-name cdk-hnb659fds-container-assets-<ACCOUNT_ID>-us-east-1 \
  --image-id imageDigest=<DIGEST> \
  --query "imageScanFindings.findings[*].{name:name,severity:severity,uri:uri}" \
  --output json
```

### Test Lambda function URL

```bash
# Get function URL
aws lambda get-function-url-config \
  --function-name <FUNCTION_NAME> \
  --query "FunctionUrl" \
  --output text

# Invoke
curl -s <FUNCTION_URL>
```
