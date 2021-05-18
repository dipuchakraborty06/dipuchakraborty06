# 1. Create package for core template, specifying arbitrary s3 bucket name
#    Deploy the package with the core stack name -> core-cfn-stack
#    ==========================================================================================================
aws cloudformation package --template-file ./core.template.yaml --s3-bucket sit01-corecfn-codebase --s3-prefix s3-notification-lambda --output-template-file ./core.packaged.template.yaml --force-upload
aws cloudformation deploy --template-file ./core.packaged.template.yaml --stack-name core-cfn-stack --capabilities CAPABILITY_NAMED_IAM --role-arn arn:aws:iam::568211590521:role/core-CloudFormationStackAdminRole
#    ==========================================================================================================

# 2. Create package for S3 event lambda template, specifying arbitrary s3 bucket name
#    Deploy the package with the core stack name -> s3-event-lambda-cfn-stack
#    ==========================================================================================================
aws cloudformation package --template-file ./lambda.template.yaml --s3-bucket sit01-corecfn-codebase --s3-prefix s3-notification-lambda --output-template-file ./lambda.packaged.template.yaml --force-upload
aws cloudformation deploy --template-file ./lambda.packaged.template.yaml --stack-name s3-event-lambda-cfn-stack --capabilities CAPABILITY_NAMED_IAM --role-arn arn:aws:iam::568211590521:role/core-CloudFormationStackAdminRole
#    ==========================================================================================================

# 3. Upload EC2 access key-pair to core S3 bucket
#    ==========================================================================================================
aws s3 cp ../core-ec2-keypair.pem s3://sit01-corecfn-codebase/keypair/core-ec2-keypair.pem
#    ==========================================================================================================

# 4. Manually create Lambda event notification on the S3 bucket -> sit01-test-notification or 
#    use the following commnd to put notification
#    ==========================================================================================================
aws s3api put-bucket-notification-configuration --bucket sit01-test-notification --notification-configuration file://s3_notification_settings.json
#    ==========================================================================================================

# 5. Install all the requirements and upload .zip file to Lambda layer
#    =============================================================================================================
cd src\s3-notification-lambda
python -m venv venv
pip install -r requirements.txt -t python
zip -r paramiko_layer /python
aws s3 cp paramiko_layer.zip s3://sit01-corecfn-codebase/lambdaLayers/paramiko_layer.zip
aws lambda publish-layer-version --layer-name paramiko-layer --description "Lambda layer for paramiko package dependancy" --license-info "Personal" --content S3Bucket=sit01-corecfn-codebase,S3Key=lambdaLayers/paramiko_layer.zip --compatible-runtimes python3.6 python3.7 python3.8