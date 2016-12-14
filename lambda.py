import boto3
from datetime import datetime
import time

def main(event, context):
	# Create / Get instance
	state = None
	instance = get_instance_by_role('plex-media-server')
	if instance:
		state = instance.state['Name']
	if not instance or state not in ['pending','running']:
		state = "pending"
		instance = create_instance(event)
	return {
		"statusCode": 200,
		"headers": { },
		"body": state
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
		MinCount = 1,
		MaxCount = 1)
	# Convert object into correct type
	instance = get_instance_by_id(reservation['Instances'][0]['InstanceId'])
	tag_instance(instance, {
		"Name": "plex-%s" % str(datetime.now()),
		"Role": "plex-media-server"
	})
	# Wait until the instance is running
	state = instance.state['Name']
	while state != "running":
		time.sleep(0.5)
		state = get_instance_by_id(instance.instance_id).state['Name']
	client.associate_address(
		InstanceId = instance.instance_id,
		AllocationId = event['eip_allocation_id'],
		AllowReassociation = False
	)
	return instance

def tag_instance(instance, data):
	ec2 = boto3.resource('ec2')
	tags = [ {'Key':k,'Value':v} for k,v in data.iteritems() ]
	ec2.create_tags(Resources=[instance.instance_id], Tags=tags)

def get_instance_by_role(name):
	ec2 = boto3.resource('ec2')
	filters = [
		{'Name':'instance-state-name','Values':['running','pending']},
		{'Name':'tag:Role','Values':[name]}
	]
	instances = list(ec2.instances.filter(Filters=filters))
	if len(instances) is 0:
		return None
	return instances[0]

def get_instance_by_id(id):
	ec2 = boto3.resource('ec2')
	instances = list(ec2.instances.filter(InstanceIds=[id]))
	if len(instances) is 0:
		return None
	return instances[0]
