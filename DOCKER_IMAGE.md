# Docker Image Changelog

## Previous: AWS Base Image (v1)

**Date:** 2026-02-16
**Status:** Deployed

### Base Image

```
public.ecr.aws/lambda/python:3.13-arm64
```

- AWS-managed Python 3.12 Lambda base image
- Architecture: ARM64 (Graviton2)
- OS: Amazon Linux 2023 (minimal)
- Includes: Lambda runtime, runtime interface client, runtime interface emulator

### Dockerfile

```dockerfile
FROM public.ecr.aws/lambda/python:3.13-arm64
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

### Notes

- This is the simplest setup using the AWS-provided base image
- No `--provenance=false` needed since CDK handles the Docker build
- No `USER` instruction needed; Lambda sets a least-privilege user automatically
- Python 3.12 base image deprecation date: Oct 2028

---

## Current: Custom Base Image (v2)

**Date:** 2026-02-16
**Status:** Deployed

### Base Image

```
python:3.13-slim (runtime stage)
python:3.13 (build stage)
```

- Official Python Docker image (Debian-based), not AWS-managed
- Architecture: ARM64 (via CDK `Platform.LINUX_ARM64`)
- Multi-stage build: full image for compilation, slim for runtime
- Requires `awslambdaric` — the Lambda runtime interface client

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
| Base image | `public.ecr.aws/lambda/python:3.13-arm64` | `python:3.13-slim` |
| Runtime client | Built into base image | Manually installed via `awslambdaric` |
| Build strategy | Single stage | Multi-stage (build + slim runtime) |
| Function dir | `${LAMBDA_TASK_ROOT}` (AWS-defined) | `/function` (custom) |
| Entrypoint | Handled by base image | Explicit `ENTRYPOINT` for `awslambdaric` |
| OS | Amazon Linux 2023 | Debian (bookworm) |

### CDK Configuration

- No changes to `stack.py` — CDK still builds and pushes the image
- `Platform.LINUX_ARM64` still handles ARM64 cross-compilation

### Notes

- `awslambdaric` is required for any non-AWS base image to work with Lambda
- No runtime interface emulator included — local testing requires mounting it externally
- No `USER` instruction needed; Lambda sets least-privilege user automatically
- Multi-stage build keeps the final image smaller by excluding build tools
