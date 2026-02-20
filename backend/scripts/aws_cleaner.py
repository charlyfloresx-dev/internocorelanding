import boto3
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

REGION = 'us-east-2'

def get_client(service_name):
    return boto3.client(service_name, region_name=REGION)

def clean_nat_gateways():
    ec2 = get_client('ec2')
    logger.info("Scanning for NAT Gateways...")
    try:
        response = ec2.describe_nat_gateways(Filter=[{'Name': 'state', 'Values': ['available', 'pending', 'failed']}])
        nat_gateways = response.get('NatGateways', [])
        
        if not nat_gateways:
            logger.info("No active NAT Gateways found.")
            return

        for nat in nat_gateways:
            nat_id = nat['NatGatewayId']
            logger.info(f"Deleting NAT Gateway: {nat_id}")
            ec2.delete_nat_gateway(NatGatewayId=nat_id)
            logger.info(f"Successfully requested deletion for {nat_id}")
            
    except Exception as e:
        logger.error(f"Error cleaning NAT Gateways: {e}")

def clean_vpc_endpoints():
    ec2 = get_client('ec2')
    logger.info("Scanning for VPC Endpoints...")
    try:
        response = ec2.describe_vpc_endpoints()
        vpc_endpoints = response.get('VpcEndpoints', [])
        
        if not vpc_endpoints:
            logger.info("No VPC Endpoints found.")
            return

        ids_to_delete = [vpce['VpcEndpointId'] for vpce in vpc_endpoints]
        if ids_to_delete:
            logger.info(f"Deleting VPC Endpoints: {ids_to_delete}")
            ec2.delete_vpc_endpoints(VpcEndpointIds=ids_to_delete)
            logger.info("Successfully deleted VPC Endpoints.")
            
    except Exception as e:
        logger.error(f"Error cleaning VPC Endpoints: {e}")

def clean_rds_instances():
    rds = get_client('rds')
    logger.info("Scanning for RDS Instances...")
    try:
        response = rds.describe_db_instances()
        instances = response.get('DBInstances', [])
        
        if not instances:
            logger.info("No RDS instances found.")
            return

        for db in instances:
            db_id = db['DBInstanceIdentifier']
            status = db['DBInstanceStatus']
            
            if status in ['deleting', 'deleted']:
                logger.info(f"RDS Instance {db_id} is already deleting/deleted.")
                continue

            logger.info(f"Deleting RDS Instance: {db_id} (SkipFinalSnapshot=True)")
            # Prevent accidental deletion protection error handling could be added, 
            # but usually assuming it's disabled or we want it to fail if protected.
            try:
                rds.delete_db_instance(
                    DBInstanceIdentifier=db_id,
                    SkipFinalSnapshot=True,
                    DeleteAutomatedBackups=True
                )
                logger.info(f"Successfully requested deletion for {db_id}")
            except rds.exceptions.InvalidDBInstanceStateFault:
                logger.warning(f"Could not delete {db_id} in current state: {status}")
            
    except Exception as e:
        logger.error(f"Error cleaning RDS Instances: {e}")

def clean_elastic_ips():
    ec2 = get_client('ec2')
    logger.info("Scanning for unassociated Elastic IPs...")
    try:
        response = ec2.describe_addresses()
        addresses = response.get('Addresses', [])
        
        if not addresses:
            logger.info("No Elastic IPs found.")
            return

        for addr in addresses:
            allocation_id = addr.get('AllocationId')
            public_ip = addr.get('PublicIp')
            association_id = addr.get('AssociationId')

            if not association_id:
                logger.info(f"Releasing unassociated Elastic IP: {public_ip} ({allocation_id})")
                ec2.release_address(AllocationId=allocation_id)
                logger.info(f"Successfully released {public_ip}")
            else:
                logger.info(f"Skipping associated Elastic IP: {public_ip}")
            
    except Exception as e:
        logger.error(f"Error cleaning Elastic IPs: {e}")

def main():
    logger.info("Starting Zero-Waste Infrastructure Cleanup...")
    logger.warning("This script will delete NAT Gateways, VPC Endpoints, RDS Instances and release unused EIPs.")
    
    clean_nat_gateways()
    clean_vpc_endpoints()
    clean_rds_instances()
    clean_elastic_ips()
    
    logger.info("Cleanup process completed.")

if __name__ == "__main__":
    main()
