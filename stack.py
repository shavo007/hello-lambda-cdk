from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


class HelloLambdaStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fn = _lambda.DockerImageFunction(
            self,
            "HelloFunction",
            code=_lambda.DockerImageCode.from_image_asset(
                str(Path(__file__).parent / "lambda"),
                platform=cdk.aws_ecr_assets.Platform.LINUX_ARM64,
            ),
            architecture=_lambda.Architecture.ARM_64,
            memory_size=128,
            timeout=cdk.Duration.seconds(10),
        )

        fn_url = fn.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
        )

        cdk.CfnOutput(self, "FunctionUrl", value=fn_url.url)
