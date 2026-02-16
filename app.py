import aws_cdk as cdk

from stack import HelloLambdaStack

app = cdk.App()
HelloLambdaStack(app, "HelloLambdaStack")
app.synth()
