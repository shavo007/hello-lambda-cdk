# hello-lambda-cdk

AWS CDK Python project that deploys a Python Lambda function as a container image on ARM64 (Graviton2), exposed via a public Function URL.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) -- Python package manager (manages the virtualenv and Python version automatically)
- [Docker](https://www.docker.com/) with ARM64 cross-build support (Docker Desktop includes this by default; on Linux, set up QEMU/buildx)
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials (`aws configure` or environment variables)
- An AWS account with permission to deploy CloudFormation, Lambda, and ECR resources

## Quick Start

```bash
# Install dependencies
uv sync

# One-time CDK bootstrap (once per AWS account/region)
uv run cdk bootstrap

# Deploy the stack
uv run cdk deploy
```

After deployment, CDK prints a `FunctionUrl` output. Curl it to test:

```bash
curl <FunctionUrl>
# {"message": "Hello from Lambda on ARM64!"}
```

To tear it down:

```bash
uv run cdk destroy
```

## Architecture

```
app.py                CDK app entry point
  -> stack.py         Defines HelloLambdaStack
       -> lambda/     Docker build context
            Dockerfile    Multi-stage build (python:3.13 -> python:3.13-slim)
            handler.py    Lambda handler
```

`stack.py` creates a `DockerImageFunction` targeting ARM64. CDK builds the Docker image locally, pushes it to a CDK-managed ECR repository, and wires it to a Lambda function with a public Function URL (no auth).

### Custom Base Image

This project does **not** use the AWS-provided Lambda base image (`public.ecr.aws/lambda/python`). Instead, it uses the official `python:3.13-slim` image with [`awslambdaric`](https://github.com/aws/aws-lambda-python-runtime-interface-client) installed manually. A multi-stage build keeps the final image small by compiling dependencies in a full `python:3.13` stage and copying only the runtime artifacts into the slim stage.

See [DOCKER_IMAGE.md](DOCKER_IMAGE.md) for the full image changelog (v1: AWS base image, v2: custom base image).

### Two Dependency Scopes

- **CDK project** (local machine): managed by `uv` / `pyproject.toml` -- `aws-cdk-lib`, `constructs`
- **Lambda container** (Docker image): managed by `pip` inside the `Dockerfile` -- `awslambdaric` and any handler dependencies

These are independent. Lambda dependencies do not go in `pyproject.toml`.

## Other Commands

```bash
uv run cdk synth     # Synthesize CloudFormation template without deploying
uv run cdk diff      # Show pending changes vs. deployed stack
```

## Constraints

- `requires-python = ">=3.12,<3.14"` -- `aws-cdk-lib` does not yet support Python 3.14+
- Docker must support `--platform linux/arm64` builds (cross-compilation via QEMU/buildx)
- The Function URL uses `FunctionUrlAuthType.NONE` -- publicly accessible, intended for testing only
