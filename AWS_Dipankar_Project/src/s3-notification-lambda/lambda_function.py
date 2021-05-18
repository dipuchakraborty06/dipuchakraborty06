import boto3, os, logging, botocore
import paramiko
logger = logging.getLogger()
logger.setLevel(logging.INFO)

function_name = os.environ["LAMBDA_FUNCTION_NAME"]
log_retention_in_days = os.environ["LOG_RETENTION_IN_DAYS"]
core_s3_bucket = os.environ["CODE_S3_BUCKET"]
key_pair_name = os.environ["KEY_PAIR_NAME"]
environment = os.environ["ENVIRONMENT"]

log_client = boto3.client("logs")
s3_client = boto3.client("s3",config=botocore.config.Config(s3={'addressing_style':'path'}))
ec2_client = boto3.client("ec2")

def lambda_handler(event, context):
    file_event = event["Records"]
    if file_event and len(file_event) > 0:
        for _file in file_event:
            folder_name = _file["s3"]["object"]["key"].split("/")[0]
            file_name = _file["s3"]["object"]["key"].split("/")[1]
            bucket_name = _file["s3"]["bucket"]["name"]
            logger.info("Event source - %s, Event type - %s, Folder name - %s, File name - %s" % (_file["eventSource"], _file["eventName"],folder_name,file_name))
            logger.info("=================> Downloading and sending the file to EC2 instance for processing ===================>")

            try:
                s3_client.download_file(core_s3_bucket,("keypair/"+key_pair_name),("/tmp/"+key_pair_name))
                logger.info("Downloaded EC2 keypair file from S3 bucket - %s to location - /tmp/%s" % (core_s3_bucket,key_pair_name))
            except Exception as e:
                logger.info("Encountered exception while downloading EC2 keypair from S3 bucket - %s" % core_s3_bucket)
                logger.info("Exception - %s" % e)

            bastion_instance_privatedns = ''
            bastion_instance_privateip = ''
            try:
                ec2_bastion_instances = ec2_client.describe_instances(Filters=[{"Name": "tag:Name", "Values": [environment+"-CoreCFNBastionEC2Instance"]}])["Reservations"][0]["Instances"]
                if ec2_bastion_instances and len(ec2_bastion_instances) > 0:
                    bastion_instance_privatedns = ec2_bastion_instances[0]["PrivateDnsName"]
                    bastion_instance_privateip = ec2_bastion_instances[0]["PrivateIpAddress"]
                    logger.log("Fetched processing EC2 instance connectivity details, Private DNS - %s, Private IP - %s" % (bastion_instance_privatedns,bastion_instance_privateip))
                logger.info("%s" % ec2_bastion_instances)
            except Exception as e:
                logger.info("Encountered exception while fetching processing EC2 instance details")
                logger.info("Exception - %s" % e)

            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                private_key = paramiko.RSAKey.from_private_key_file("/tmp/"+key_pair_name)
                ssh.connect(bastion_instance_privateip,username="ubuntu",pkey=private_key)
                logger.info("SSH to bastion instance is successfull !! Downloading S3 inbound file to local path - /home/ubuntu")

                commands = [
                    "aws s3 cp s3://"+bucket_name+"/"+folder_name+"/"+file_name+" ~/"+file_name
                ]
                for c in commands:
                    logger.info("Executing command - %s" % c)
                    ssh.exec_command(c)
                    logger.info("Feed file successfully downloaded into the processing EC2 instance")
            except Exception as e:
                logger.info("Encountered exception while connecting to preocess EC2 instance")
                logger.info("Exception - %s" % e)

def put_loggroup_retention():
    try:
        log_group = log_client.describe_log_groups(logGroupNamePrefix=("/aws/lambda/"+function_name))["logGroups"]
        if len(log_group) > 0:
            log_client.put_retention_policy(logGroupName=log_group[0]["logGroupName"], retentionInDays=int(log_retention_in_days))
    except Exception as e:
        logger.info("Encountered exception while updating log group log retention policy, Log group name - /aws/lambda/%s" % function_name)
        logger.info("Exception - %s" % e)
