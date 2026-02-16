# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

AWS CDK Python project that deploys a Python Lambda function as a container image on ARM64 (Graviton2). Uses `uv` for dependency management.

## Commands

All commands run through `uv` to use the managed virtualenv:

```bash
uv sync                  # Install/update dependencies
uv run cdk synth         # Synthesize CloudFormation template
uv run cdk deploy        # Deploy stack to AWS
uv run cdk diff          # Show pending changes vs. deployed stack
uv run cdk destroy       # Tear down the stack
uv run cdk bootstrap     # One-time setup per AWS account/region
```

AWS credentials must be configured (`aws configure` or env vars) before any `cdk` command. Docker credentials for `dhi.io` must be configured to pull the hardened base image.

Pre-commit hooks (ruff, detect-secrets, etc.):

```bash
uv run pre-commit run --all-files   # Run all hooks manually
uv run pre-commit install           # Install git hooks (already done)
```

## Architecture

- **`app.py`** -- CDK app entry point, instantiates `HelloLambdaStack`
- **`stack.py`** -- Single stack defining a `DockerImageFunction` (ARM64) with a public Function URL (no auth). CDK builds the Docker image and pushes to its managed ECR repo automatically
- **`lambda/`** -- Container image context: multi-stage `Dockerfile` using `dhi.io/python:3.13` (Docker Hardened Image) as the runtime with `awslambdaric`, plus `handler.py`
- **`cdk.json`** -- Tells CDK CLI to run via `uv run python3 app.py`
- **`DOCKER_IMAGE.md`** -- Changelog tracking Docker image evolution (v1: AWS base image, v2: python:3.13-slim, v3: dhi.io/python:3.13)

## Two Dependency Scopes

- **CDK project** (local machine): managed by `uv` / `pyproject.toml` -- `aws-cdk-lib`, `constructs`, `pre-commit` (dev)
- **Lambda container** (Docker image): managed by `pip` in `Dockerfile` -- `awslambdaric` and any future handler dependencies

These are independent. Lambda container dependencies do not go in `pyproject.toml`.

## Key Constraints

- `requires-python = ">=3.12,<3.14"` in pyproject.toml -- `aws-cdk-lib` doesn't support Python 3.14+, uv will auto-fetch a compatible Python
- The Lambda container uses Python 3.13 (set in `lambda/Dockerfile`), independent of the CDK project Python version
- The Lambda container image is built with `--platform linux/arm64` (set via `Platform.LINUX_ARM64` in stack.py) -- Docker must support cross-platform builds
- Function URL uses `FunctionUrlAuthType.NONE` -- publicly accessible, intended for quick testing only
- DHI base image puts Python at `/opt/python/bin/python` (not `/usr/local/bin/python`) -- the `ENTRYPOINT` in the Dockerfile must use this path
- DHI image is extremely minimal (no `which`, no shell utilities) -- debugging inside the container is limited
