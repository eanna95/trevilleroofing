# AWS CloudFront Deployment Guide

This guide will help you deploy your React application to AWS CloudFront with S3 static hosting and secure authentication via AWS Parameter Store.

## Prerequisites

- AWS CLI installed and configured with your credentials
- An AWS account with appropriate permissions for S3, CloudFront, and Systems Manager Parameter Store

## Step 1: Set Up Authentication Parameters

First, set up secure authentication credentials in AWS Parameter Store:

1. **Create username parameter:**
   ```bash
   aws ssm put-parameter \
     --name "/treville-demo/auth/username" \
     --value "your-username" \
     --type "String" \
     --description "Username for Treville demo dashboard"
   ```

2. **Create password parameter (encrypted):**
   ```bash
   aws ssm put-parameter \
     --name "/treville-demo/auth/password" \
     --value "your-secure-password" \
     --type "SecureString" \
     --description "Password for Treville demo dashboard"
   ```

3. **Verify parameters were created:**
   ```bash
   aws ssm describe-parameters --parameter-filters "Key=Name,Values=/treville-demo/auth/"
   ```

## Step 2: Create S3 Bucket

1. **Create a new S3 bucket:**
   ```bash
   aws s3 mb s3://your-company-analysis-app --region us-east-1
   ```

2. **Enable static website hosting:**
   ```bash
   aws s3 website s3://your-company-analysis-app --index-document index.html --error-document index.html
   ```

3. **Set bucket policy for public read access:**
   Create a file called `bucket-policy.json`:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-company-analysis-app/*"
       }
     ]
   }
   ```

   Apply the policy:
   ```bash
   aws s3api put-bucket-policy --bucket your-company-analysis-app --policy file://bucket-policy.json
   ```

## Step 2: Upload Built Files to S3

1. **Upload the dist folder contents:**
   ```bash
   aws s3 sync ./dist/ s3://your-company-analysis-app --delete
   ```

2. **Set proper content types (important for fonts and CSS):**
   ```bash
   aws s3 cp s3://your-company-analysis-app s3://your-company-analysis-app --recursive --exclude "*" --include "*.css" --content-type "text/css" --metadata-directive REPLACE
   aws s3 cp s3://your-company-analysis-app s3://your-company-analysis-app --recursive --exclude "*" --include "*.js" --content-type "application/javascript" --metadata-directive REPLACE
   aws s3 cp s3://your-company-analysis-app s3://your-company-analysis-app --recursive --exclude "*" --include "*.html" --content-type "text/html" --metadata-directive REPLACE
   ```

## Step 3: Configure IAM for Parameter Store Access

The application needs permissions to read from Parameter Store. You have two options:

### Option A: Use IAM Roles (Recommended for EC2/Lambda)
If running on AWS services, attach this policy to your service role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": [
        "arn:aws:ssm:us-east-1:*:parameter/treville-demo/auth/*"
      ]
    }
  ]
}
```

### Option B: Environment Variables (For local development)
Set these environment variables with IAM user credentials:

```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key  
export AWS_DEFAULT_REGION=us-east-1
```

## Step 4: Create CloudFront Distribution

1. **Create a CloudFront distribution config file** (`cloudfront-config.json`):
   ```json
   {
     "CallerReference": "company-analysis-$(date +%s)",
     "Comment": "Company Analysis Dashboard",
     "DefaultRootObject": "index.html",
     "Origins": {
       "Quantity": 1,
       "Items": [
         {
           "Id": "S3-your-company-analysis-app",
           "DomainName": "your-company-analysis-app.s3.amazonaws.com",
           "S3OriginConfig": {
             "OriginAccessIdentity": ""
           }
         }
       ]
     },
     "DefaultCacheBehavior": {
       "TargetOriginId": "S3-your-company-analysis-app",
       "ViewerProtocolPolicy": "redirect-to-https",
       "MinTTL": 0,
       "ForwardedValues": {
         "QueryString": false,
         "Cookies": {
           "Forward": "none"
         }
       }
     },
     "CustomErrorResponses": {
       "Quantity": 1,
       "Items": [
         {
           "ErrorCode": 404,
           "ResponsePagePath": "/index.html",
           "ResponseCode": "200",
           "ErrorCachingMinTTL": 300
         }
       ]
     },
     "Enabled": true,
     "PriceClass": "PriceClass_100"
   }
   ```

2. **Create the CloudFront distribution:**
   ```bash
   aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
   ```

## Step 5: Alternative - Using AWS Console

If you prefer using the AWS Console:

### S3 Setup:
1. Go to S3 Console
2. Create new bucket (name it uniquely, e.g., `company-analysis-dashboard-[random]`)
3. Upload all files from the `dist/` folder
4. Go to Properties → Static Website Hosting → Enable
5. Set index document to `index.html`
6. Go to Permissions → Bucket Policy and add public read policy

### CloudFront Setup:
1. Go to CloudFront Console
2. Create Distribution
3. Set Origin Domain to your S3 bucket
4. Set Default Root Object to `index.html`
5. Under Error Pages, add custom error response:
   - HTTP Error Code: 404
   - Response Page Path: `/index.html`
   - HTTP Response Code: 200
6. Set Viewer Protocol Policy to "Redirect HTTP to HTTPS"
7. Create Distribution

### Parameter Store Setup (Console):
1. Go to Systems Manager Console → Parameter Store
2. Create parameter `/treville-demo/auth/username` as String type
3. Create parameter `/treville-demo/auth/password` as SecureString type
4. Set appropriate values for both parameters

## Step 6: Update and Redeploy

For future updates:

1. **Build the app:**
   ```bash
   npm run build
   ```

2. **Upload to S3:**
   ```bash
   aws s3 sync ./dist/ s3://your-company-analysis-app --delete
   ```

3. **Invalidate CloudFront cache:**
   ```bash
   aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
   ```

## Important Notes

- **Replace `your-company-analysis-app`** with your actual bucket name
- **Replace `YOUR_DISTRIBUTION_ID`** with your actual CloudFront distribution ID
- **The error document is set to `index.html`** to handle React Router (if you add routing later)
- **HTTPS is enforced** for security
- **The deployment will be available globally** through CloudFront's edge locations

## Security Considerations

### Authentication Security
- **Credentials are encrypted**: Passwords are stored as SecureString in Parameter Store
- **No hardcoded secrets**: All sensitive data is externalized to AWS Parameter Store  
- **IAM-based access**: Parameter Store access is controlled via IAM policies
- **Development fallback**: The app includes fallback credentials only in development mode

### Infrastructure Security
- **HTTPS enforced**: CloudFront redirects all HTTP traffic to HTTPS
- **Static file security**: S3 bucket allows public read access only to necessary files
- **Parameter Store encryption**: Sensitive parameters use AWS managed encryption

### Production Recommendations
For enhanced security in production:
- Use Origin Access Identity (OAI) to restrict direct S3 access
- Set up custom domain with SSL certificate
- Enable CloudFront WAF for additional protection
- Rotate credentials regularly using Parameter Store versioning
- Monitor access logs for unusual activity
- Consider adding multi-factor authentication

### Credential Management
- **To update credentials**:
  ```bash
  aws ssm put-parameter --name "/treville-demo/auth/password" --value "new-password" --type "SecureString" --overwrite
  ```
- **To rotate credentials**: Update Parameter Store values and the app will automatically use new credentials on next login attempt

Your application will be available at the CloudFront distribution URL once deployment is complete!