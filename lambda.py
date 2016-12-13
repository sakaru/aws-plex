import boto3
from datetime import datetime

def main(event, context):
	instance = create_instance(event)
	tag_instance(instance, {
		"Name": "plex-%s" % str(datetime.now()),
		"Role": "plex-media-server"
	})
	return {
		"statusCode": 200,
		"headers": { },
		"body": "Success"
	}

def create_instance(event):
	client = boto3.client('ec2',
		region_name = event['region'],
		aws_access_key_id = event['aws_access_key_id'],
		aws_secret_access_key = event['aws_secret_access_key'],
		)
	reservation = client.run_instances(
		ImageId = 'ami-b953f2da',
		KeyName = event['key_name'],
		InstanceType = event['instance_type'],
		SecurityGroupIds = event['security_groups'].split(' '),
		SubnetId = event['subnet_id'],
		InstanceInitiatedShutdownBehavior = "terminate",
		MinCount=1,
		MaxCount=1)
	return reservation['Instances'][0]

def tag_instance(instance, data):
	ec2 = boto3.resource('ec2')
	tags = [ {'Key':k,'Value':v} for k,v in data.iteritems() ]
	ec2.create_tags(Resources=[instance['InstanceId']], Tags=tags)
