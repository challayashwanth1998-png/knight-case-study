#!/bin/bash
set -e

REGION="us-east-1"
INSTANCE_TYPE="t3.small"
KEY_NAME="knight-key"
SG_NAME="knight-insurance-sg"

echo "Creating Key Pair ($KEY_NAME)..."
mkdir -p ~/.ssh
# Delete key if exists
aws ec2 delete-key-pair --key-name $KEY_NAME --region $REGION 2>/dev/null || true
rm -f ~/.ssh/$KEY_NAME.pem
aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text --region $REGION > ~/.ssh/$KEY_NAME.pem
chmod 400 ~/.ssh/$KEY_NAME.pem

echo "Fetching Default VPC..."
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text --region $REGION)

echo "Creating Security Group ($SG_NAME)..."
aws ec2 delete-security-group --group-name $SG_NAME --region $REGION 2>/dev/null || true
SG_ID=$(aws ec2 create-security-group --group-name $SG_NAME --description "Knight Insurance SG" --vpc-id $VPC_ID --query 'GroupId' --output text --region $REGION)

echo "Authorizing Ingress Rules..."
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $REGION
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 3000 --cidr 0.0.0.0/0 --region $REGION
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $REGION

echo "Finding latest Ubuntu 24.04 AMI..."
AMI_ID=$(aws ssm get-parameters --names /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id --query 'Parameters[0].Value' --output text --region $REGION)

echo "Preparing User Data..."
cat << 'EOF' > user-data.sh
#!/bin/bash
apt-get update -y
apt-get install -y docker.io docker-compose
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu
EOF

echo "Launching EC2 Instance ($INSTANCE_TYPE)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --user-data file://user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Knight-Insurance-App}]' \
    --query 'Instances[0].InstanceId' \
    --output text \
    --region $REGION)

echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region $REGION)

echo "Instance is running!"
echo "Public IP: $PUBLIC_IP"
echo "Waiting for SSH to become available (sleeping 45s)..."
sleep 45

# Replace PUBLIC_IP in docker-compose.yml before syncing
sed -i.bak "s/<REPLACE_WITH_PUBLIC_IP>/$PUBLIC_IP/g" docker-compose.yml
rm -f docker-compose.yml.bak

echo "Syncing application code to EC2..."
# We exclude node_modules, .next, venv to save huge transfer time
rsync -avz -e "ssh -o StrictHostKeyChecking=no -i ~/.ssh/$KEY_NAME.pem" \
    --exclude 'frontend/node_modules' \
    --exclude 'frontend/.next' \
    --exclude 'backend/venv' \
    --exclude '.git' \
    ./ ubuntu@$PUBLIC_IP:~/app/

echo "Starting Docker Compose on EC2..."
ssh -o StrictHostKeyChecking=no -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP << 'EOF'
    cd ~/app
    # Wait for docker to finish installing in background user-data
    while ! command -v docker-compose &> /dev/null; do
        echo "Waiting for docker-compose..."
        sleep 5
    done
    sudo docker-compose up -d --build
EOF

echo ""
echo "======================================================"
echo "DEPLOYMENT COMPLETE!"
echo "Frontend available at: http://$PUBLIC_IP:3000"
echo "Backend available at:  http://$PUBLIC_IP:8000"
echo "======================================================"
