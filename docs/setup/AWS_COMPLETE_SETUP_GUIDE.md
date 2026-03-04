# Complete AWS Setup Guide for SarkariSaathi

## Table of Contents

1. [AWS Account Creation](#1-aws-account-creation)
2. [Initial AWS Configuration](#2-initial-aws-configuration)
3. [IAM User Setup](#3-iam-user-setup)
4. [AWS CLI Installation and Configuration](#4-aws-cli-installation-and-configuration)
5. [Node.js and AWS CDK Setup](#5-nodejs-and-aws-cdk-setup)
6. [Project Dependencies Installation](#6-project-dependencies-installation)
7. [AWS Services Configuration](#7-aws-services-configuration)
8. [CDK Bootstrap and Deployment](#8-cdk-bootstrap-and-deployment)
9. [Amazon Connect Setup](#9-amazon-connect-setup)
10. [Testing and Verification](#10-testing-and-verification)
11. [Monitoring Setup](#11-monitoring-setup)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. AWS Account Creation

### Step 1.1: Create AWS Account

1. **Open your web browser** and go to: https://aws.amazon.com/

2. **Click "Create an AWS Account"** button (top right corner)

3. **Enter your email address**
   - Use a valid email you have access to
   - Example: `your-email@example.com`
   - Click "Verify email address"

4. **Check your email** for verification code
   - Open the email from AWS
   - Copy the 6-digit verification code
   - Paste it in the AWS signup page
   - Click "Verify"

5. **Create your AWS account password**
   - Password requirements:
     - At least 8 characters
     - Include uppercase letter
     - Include lowercase letter
     - Include number
     - Include special character
   - Re-enter password to confirm
   - Click "Continue"

6. **Enter your AWS account name**
   - Choose a name for your account
   - Example: `SarkariSaathi-Production`
   - This is just for your reference
   - Click "Continue"

7. **Select account type**
   - Choose "Personal" (for individual use)
   - OR "Business" (if you have a company)
   - For this project, "Personal" is fine

8. **Enter contact information**
   - Full Name: Your full name
   - Phone Number: Your mobile number with country code
     - Example: +91 9876543210 (for India)
   - Country/Region: Select your country
   - Address: Your complete address
   - City: Your city
   - State/Province: Your state
   - Postal Code: Your postal/ZIP code
   - Check the "AWS Customer Agreement" checkbox
   - Click "Continue to payment information"

9. **Enter payment information**
   - Credit/Debit Card Number
   - Expiration Date (MM/YY)
   - Cardholder Name
   - Billing Address (if different from contact address)
   - Click "Verify and Continue"

   **Note:** AWS will charge ₹2 (or $1) for verification, which will be refunded

10. **Verify your phone number**
    - Select your country code
    - Enter your phone number
    - Choose verification method:
      - "Text message (SMS)" - Recommended
      - OR "Voice call"
    - Click "Send SMS" or "Call me now"
    - Enter the 4-digit verification code you receive
    - Click "Verify code"

11. **Select a support plan**
    - Choose "Basic support - Free"
    - This is sufficient for development
    - Click "Complete sign up"

12. **Wait for account activation**
    - You'll see "Congratulations" message
    - Account activation takes 5-10 minutes
    - You'll receive email when ready
    - Click "Go to the AWS Management Console"

### Step 1.2: Sign in to AWS Console

1. **Go to AWS Console**: https://console.aws.amazon.com/

2. **Select "Root user"**

3. **Enter your email address** (the one you used to create account)

4. **Click "Next"**

5. **Enter your password**

6. **Click "Sign in"**

7. **You're now in the AWS Management Console!**

---

## 2. Initial AWS Configuration

### Step 2.1: Set Your Default Region

1. **Look at the top-right corner** of AWS Console

2. **Click on the region dropdown** (shows current region like "N. Virginia")

3. **Select "Asia Pacific (Mumbai) ap-south-1"**
   - This is closest to India
   - Better latency for Indian users
   - Some services might be cheaper here

4. **Verify the region changed** - should now show "Mumbai"

### Step 2.2: Enable MFA (Multi-Factor Authentication) - Recommended

1. **Click on your account name** (top-right corner)

2. **Click "Security credentials"**

3. **Scroll to "Multi-factor authentication (MFA)"**

4. **Click "Assign MFA device"**

5. **Choose MFA device type**:
   - "Authenticator app" - Recommended (Google Authenticator, Authy)
   - OR "Security key" (physical device)
   - OR "Hardware TOTP token"

6. **For Authenticator app**:
   - Install Google Authenticator or Authy on your phone
   - Click "Show QR code"
   - Scan QR code with your authenticator app
   - Enter two consecutive MFA codes
   - Click "Add MFA"

---

## 3. IAM User Setup

**Important:** Don't use root account for daily operations. Create IAM user instead.

### Step 3.1: Access IAM Service

1. **In AWS Console**, click the search bar at top

2. **Type "IAM"** and press Enter

3. **Click "IAM"** from results

4. **You're now in IAM Dashboard**

### Step 3.2: Create IAM User

1. **Click "Users"** in left sidebar

2. **Click "Create user"** button (orange button)

3. **Enter user details**:
   - User name: `sarkari-saathi-admin`
   - Check "Provide user access to the AWS Management Console"
   - Select "I want to create an IAM user"
   - Console password: Choose "Custom password"
   - Enter a strong password
   - Uncheck "Users must create a new password at next sign-in" (optional)
   - Click "Next"

4. **Set permissions**:
   - Select "Attach policies directly"
   - Search and check these policies:
     - `AdministratorAccess` (for full access during development)
     - OR for production, use these specific policies:
       - `AmazonDynamoDBFullAccess`
       - `AmazonS3FullAccess`
       - `AWSLambda_FullAccess`
       - `AmazonAPIGatewayAdministrator`
       - `AmazonConnectFullAccess`
       - `AmazonPollyFullAccess`
       - `AmazonTranscribeFullAccess`
       - `CloudWatchFullAccess`
       - `IAMFullAccess`
   - Click "Next"

5. **Review and create**:
   - Review the user details
   - Click "Create user"

6. **Save credentials**:
   - **IMPORTANT:** Download the CSV file with credentials
   - OR copy the Console sign-in URL, username, and password
   - Store these securely - you won't see them again!
   - Click "Return to users list"

### Step 3.3: Create Access Keys for CLI

1. **Click on the user** you just created (`sarkari-saathi-admin`)

2. **Click "Security credentials"** tab

3. **Scroll to "Access keys"** section

4. **Click "Create access key"**

5. **Select use case**:
   - Choose "Command Line Interface (CLI)"
   - Check "I understand the above recommendation"
   - Click "Next"

6. **Set description** (optional):
   - Description: `SarkariSaathi Development CLI`
   - Click "Create access key"

7. **Save your access keys**:
   - **Access key ID**: Starts with `AKIA...`
   - **Secret access key**: Long random string
   - **CRITICAL:** Click "Download .csv file" and save it securely
   - You cannot retrieve the secret key again!
   - Click "Done"

---

## 4. AWS CLI Installation and Configuration

### Step 4.1: Install AWS CLI

#### For Windows:

1. **Download AWS CLI installer**:
   - Go to: https://awscli.amazonaws.com/AWSCLIV2.msi
   - Save the file

2. **Run the installer**:
   - Double-click the downloaded `.msi` file
   - Click "Next" through the installation wizard
   - Accept the license agreement
   - Click "Install"
   - Click "Finish"

3. **Verify installation**:
   - Open Command Prompt (cmd) or PowerShell
   - Type: `aws --version`
   - Should show: `aws-cli/2.x.x Python/3.x.x Windows/...`

#### For macOS:

1. **Open Terminal**

2. **Install using curl**:

   ```bash
   curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
   sudo installer -pkg AWSCLIV2.pkg -target /
   ```

3. **Verify installation**:
   ```bash
   aws --version
   ```

#### For Linux:

1. **Open Terminal**

2. **Download and install**:

   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

3. **Verify installation**:
   ```bash
   aws --version
   ```

### Step 4.2: Configure AWS CLI

1. **Open Terminal/Command Prompt**

2. **Run configuration command**:

   ```bash
   aws configure
   ```

3. **Enter your credentials** (from the CSV file you downloaded):

   ```
   AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
   AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   Default region name [None]: ap-south-1
   Default output format [None]: json
   ```

4. **Verify configuration**:

   ```bash
   aws sts get-caller-identity
   ```

   Should return:

   ```json
   {
     "UserId": "AIDAI...",
     "Account": "123456789012",
     "Arn": "arn:aws:iam::123456789012:user/sarkari-saathi-admin"
   }
   ```

5. **Test S3 access** (optional):
   ```bash
   aws s3 ls
   ```
   Should return empty list or your existing buckets

---

## 5. Node.js and AWS CDK Setup

### Step 5.1: Install Node.js

#### For Windows:

1. **Download Node.js**:
   - Go to: https://nodejs.org/
   - Download "LTS" version (recommended)
   - Example: `node-v20.x.x-x64.msi`

2. **Run installer**:
   - Double-click the downloaded file
   - Click "Next" through wizard
   - Accept license agreement
   - Keep default installation path
   - Click "Install"
   - Click "Finish"

3. **Verify installation**:
   - Open new Command Prompt
   - Type: `node --version`
   - Should show: `v20.x.x`
   - Type: `npm --version`
   - Should show: `10.x.x`

#### For macOS:

1. **Using Homebrew** (recommended):

   ```bash
   brew install node
   ```

2. **OR download from website**:
   - Go to: https://nodejs.org/
   - Download macOS installer
   - Run the `.pkg` file

3. **Verify**:
   ```bash
   node --version
   npm --version
   ```

#### For Linux:

1. **Using package manager**:

   ```bash
   # Ubuntu/Debian
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs

   # CentOS/RHEL
   curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
   sudo yum install -y nodejs
   ```

2. **Verify**:
   ```bash
   node --version
   npm --version
   ```

### Step 5.2: Install AWS CDK

1. **Open Terminal/Command Prompt**

2. **Install CDK globally**:

   ```bash
   npm install -g aws-cdk
   ```

3. **Verify installation**:

   ```bash
   cdk --version
   ```

   Should show: `2.x.x (build ...)`

4. **If you get permission errors on macOS/Linux**:
   ```bash
   sudo npm install -g aws-cdk
   ```

---

## 6. Project Dependencies Installation

### Step 6.1: Navigate to Project Directory

1. **Open Terminal/Command Prompt**

2. **Navigate to your project**:

   ```bash
   cd path/to/AI_for_bharat
   ```

   Example:
   - Windows: `cd C:\Users\YourName\Projects\AI_for_bharat`
   - macOS/Linux: `cd ~/Projects/AI_for_bharat`

3. **Verify you're in correct directory**:

   ```bash
   # Windows
   dir

   # macOS/Linux
   ls -la
   ```

   You should see files like:
   - `package.json`
   - `cdk.json`
   - `lib/` folder
   - `lambda/` folder

### Step 6.2: Install Node.js Dependencies

1. **Install all npm packages**:

   ```bash
   npm install
   ```

2. **Wait for installation** (may take 2-5 minutes)

3. **Verify installation**:

   ```bash
   npm list --depth=0
   ```

   Should show all installed packages

### Step 6.3: Install Python Dependencies (for Lambda functions)

1. **Check if Python is installed**:

   ```bash
   python --version
   ```

   OR

   ```bash
   python3 --version
   ```

   Should show: `Python 3.9.x` or higher

2. **If Python not installed**:

   **Windows:**
   - Download from: https://www.python.org/downloads/
   - Run installer
   - **IMPORTANT:** Check "Add Python to PATH"
   - Click "Install Now"

   **macOS:**

   ```bash
   brew install python3
   ```

   **Linux:**

   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   ```

3. **Install pip (if not already installed)**:

   ```bash
   python -m ensurepip --upgrade
   ```

4. **Create virtual environment** (recommended):

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` doesn't exist, install these manually:

   ```bash
   pip install boto3 requests hypothesis pytest
   ```

### Step 6.4: Build the Project

1. **Compile TypeScript**:

   ```bash
   npm run build
   ```

2. **Check for errors**:
   - If successful, you'll see: "Compiled successfully"
   - If errors, read the error messages and fix them

---

## 7. AWS Services Configuration

### Step 7.1: Create S3 Buckets

We need several S3 buckets for the project.

1. **Go to S3 Console**:
   - In AWS Console, search for "S3"
   - Click "S3"

2. **Create Audio Storage Bucket**:
   - Click "Create bucket"
   - Bucket name: `sarkari-saathi-audio-storage-[YOUR-ACCOUNT-ID]`
     - Replace `[YOUR-ACCOUNT-ID]` with your AWS account ID
     - Example: `sarkari-saathi-audio-storage-123456789012`
   - Region: `Asia Pacific (Mumbai) ap-south-1`
   - Block Public Access: Keep all checked (recommended)
   - Bucket Versioning: Disable
   - Default encryption: Enable
     - Encryption type: SSE-S3
   - Click "Create bucket"

3. **Create TTS Cache Bucket**:
   - Click "Create bucket"
   - Bucket name: `sarkari-saathi-tts-cache-[YOUR-ACCOUNT-ID]`
   - Region: `ap-south-1`
   - Same settings as above
   - Click "Create bucket"

4. **Create Scheme Documents Bucket**:
   - Click "Create bucket"
   - Bucket name: `sarkari-saathi-schemes-[YOUR-ACCOUNT-ID]`
   - Region: `ap-south-1`
   - Same settings as above
   - Click "Create bucket"

5. **Configure Lifecycle Policies** (for cost optimization):

   For Audio Storage Bucket:
   - Click on the bucket name
   - Go to "Management" tab
   - Click "Create lifecycle rule"
   - Rule name: `delete-old-audio`
   - Choose rule scope: Apply to all objects
   - Lifecycle rule actions:
     - Check "Expire current versions of objects"
     - Days after object creation: `30`
   - Click "Create rule"

   For TTS Cache Bucket:
   - Same steps but set expiration to `7` days

### Step 7.2: Request Service Quota Increases

Some AWS services have default limits that might be too low.

1. **Go to Service Quotas**:
   - Search for "Service Quotas" in AWS Console
   - Click "Service Quotas"

2. **Check Lambda Concurrent Executions**:
   - Click "AWS services"
   - Search for "Lambda"
   - Click "AWS Lambda"
   - Find "Concurrent executions"
   - Default is 1000 (usually sufficient)
   - If you need more, click "Request quota increase"

3. **Check API Gateway Limits**:
   - Go back to AWS services
   - Search for "API Gateway"
   - Check "Throttle rate" and "Throttle burst"
   - Default: 10,000 requests per second (sufficient for most cases)

4. **Check Amazon Connect Limits**:
   - Search for "Amazon Connect"
   - Check "Concurrent calls per instance"
   - Default: 10 (for new accounts)
   - Request increase if needed for production

### Step 7.3: Enable Required AWS Services

Some services need to be explicitly enabled.

1. **Enable Amazon Bedrock** (for AI features):
   - Search for "Bedrock" in AWS Console
   - Click "Amazon Bedrock"
   - Click "Get started"
   - Click "Model access" in left sidebar
   - Click "Manage model access"
   - Find "Claude 3.5 Sonnet"
   - Click "Request access" or "Enable"
   - Wait for approval (usually instant for Claude)

2. **Enable Amazon Transcribe**:
   - Search for "Transcribe"
   - Click "Amazon Transcribe"
   - Service is automatically enabled when you use it

3. **Enable Amazon Polly**:
   - Search for "Polly"
   - Click "Amazon Polly"
   - Service is automatically enabled

4. **Enable Amazon Pinpoint** (for SMS):
   - Search for "Pinpoint"
   - Click "Amazon Pinpoint"
   - Click "Create a project"
   - Project name: `SarkariSaathi`
   - Click "Create"
   - Note the Project ID

### Step 7.4: Configure Systems Manager Parameters

1. **Go to Systems Manager**:
   - Search for "Systems Manager" or "SSM"
   - Click "AWS Systems Manager"

2. **Create Parameter Store entries**:
   - Click "Parameter Store" in left sidebar
   - Click "Create parameter"

3. **Create Bhashini API Key parameter**:
   - Name: `/sarkari-saathi/api-keys/bhashini`
   - Description: `Bhashini API key for language translation`
   - Tier: Standard
   - Type: SecureString
   - KMS key: Use default
   - Value: `YOUR_BHASHINI_API_KEY` (get from https://bhashini.gov.in/)
   - Click "Create parameter"

4. **Create OpenAI API Key parameter** (if using):
   - Name: `/sarkari-saathi/api-keys/openai`
   - Type: SecureString
   - Value: `YOUR_OPENAI_API_KEY`
   - Click "Create parameter"

5. **Create feature flags**:
   - Name: `/sarkari-saathi/features/enable-debug-logging`
   - Type: String
   - Value: `false`
   - Click "Create parameter"

---

## 8. CDK Bootstrap and Deployment

### Step 8.1: Bootstrap CDK

This is a one-time setup per AWS account and region.

1. **Open Terminal in project directory**

2. **Run bootstrap command**:

   ```bash
   cdk bootstrap aws://ACCOUNT-ID/ap-south-1
   ```

   Replace `ACCOUNT-ID` with your AWS account ID (12-digit number)

   Example:

   ```bash
   cdk bootstrap aws://123456789012/ap-south-1
   ```

3. **Wait for completion** (takes 2-3 minutes)

4. **Verify bootstrap**:
   - Go to CloudFormation in AWS Console
   - You should see a stack named `CDKToolkit`
   - Status should be `CREATE_COMPLETE`

### Step 8.2: Review CDK Stack

1. **Check what will be deployed**:

   ```bash
   cdk synth
   ```

   This shows the CloudFormation template that will be created

2. **See the differences** (if updating existing stack):
   ```bash
   cdk diff
   ```

### Step 8.3: Deploy CDK Stack

1. **Deploy the stack**:

   ```bash
   cdk deploy
   ```

2. **Review changes**:
   - CDK will show you what resources will be created
   - Review the list carefully

3. **Confirm deployment**:
   - Type `y` and press Enter when prompted
   - OR use `--require-approval never` to skip confirmation:
     ```bash
     cdk deploy --require-approval never
     ```

4. **Wait for deployment** (takes 10-20 minutes):
   - You'll see progress in terminal
   - Resources are created one by one
   - Don't close the terminal!

5. **Deployment complete**:
   - You'll see "✅ SarkariSaathiStack"
   - Note the outputs shown (API endpoints, etc.)
   - Save these outputs!

### Step 8.4: Verify Deployment

1. **Check CloudFormation**:
   - Go to CloudFormation in AWS Console
   - Find stack: `SarkariSaathiStack`
   - Status should be: `CREATE_COMPLETE`
   - Click on stack name
   - Go to "Resources" tab
   - Verify all resources are created

2. **Check Lambda Functions**:
   - Go to Lambda in AWS Console
   - You should see functions like:
     - `SarkariSaathi-AudioInputHandler`
     - `SarkariSaathi-SpeechToText`
     - `SarkariSaathi-TextToSpeech`
     - `SarkariSaathi-ConversationManager`
     - `SarkariSaathi-IvrHandler`
     - And more...

3. **Check DynamoDB Tables**:
   - Go to DynamoDB in AWS Console
   - Click "Tables"
   - You should see:
     - `SarkariSaathi-Users`
     - `SarkariSaathi-Sessions`
     - `SarkariSaathi-Schemes`
     - `SarkariSaathi-Applications`
     - `SarkariSaathi-IvrCallbacks`

4. **Check API Gateway**:
   - Go to API Gateway in AWS Console
   - Find: `SarkariSaathi API`
   - Note the Invoke URL
   - Example: `https://abc123.execute-api.ap-south-1.amazonaws.com/prod`

---

## 9. Amazon Connect Setup

### Step 9.1: Create Amazon Connect Instance

1. **Go to Amazon Connect**:
   - Search for "Connect" in AWS Console
   - Click "Amazon Connect"

2. **Click "Create instance"**

3. **Step 1: Identity management**:
   - Access URL: `sarkari-saathi-ivr`
   - This creates: `https://sarkari-saathi-ivr.my.connect.aws`
   - Store users: Select "Store users within Amazon Connect"
   - Click "Next"

4. **Step 2: Administrator**:
   - Specify administrator:
     - First name: `Admin`
     - Last name: `User`
     - Username: `admin`
     - Email: Your email
     - Password: Create strong password
   - Click "Next"

5. **Step 3: Telephony**:
   - Check "I want to handle incoming calls with Amazon Connect"
   - Check "I want to make outbound calls with Amazon Connect"
   - Click "Next"

6. **Step 4: Data storage**:
   - Call recordings: Use default bucket (or select custom)
   - Enable encryption: Check this
   - Exported reports: Use default
   - Enable encryption: Check this
   - Click "Next"

7. **Step 5: Review and create**:
   - Review all settings
   - Click "Create instance"
   - Wait 2-3 minutes for creation

8. **Save Instance Details**:
   - Instance ARN: Copy and save
   - Instance ID: Copy and save (last part of ARN)
   - Access URL: Save for later login

### Step 9.2: Claim Phone Number

1. **Click on your instance** in Amazon Connect console

2. **Click "Claim a phone number"**

3. **Select country**: India (+91)

4. **Select phone type**: DID (Direct Inward Dialing)

5. **Choose a phone number**:
   - Browse available numbers
   - Select one you like
   - Click "Next"

6. **Set description**: "SarkariSaathi Main IVR Line"

7. **Select contact flow**: "Sample inbound flow" (temporary)

8. **Click "Save"**

9. **Note the phone number**: Example: +91-80-XXXX-XXXX

### Step 9.3: Configure Lambda Integration

1. **In Amazon Connect console**, click your instance

2. **Click "Contact flows"** in left sidebar

3. **Click "AWS Lambda"** section

4. **Click "Add Lambda Function"**

5. **Select region**: ap-south-1

6. **Find and select**: `SarkariSaathi-IvrHandler`

7. **Click "Add Lambda Function"**

8. **Verify**: Function should appear in the list

### Step 9.4: Create Contact Flow

1. **Access Contact Flow Designer**:
   - In Amazon Connect instance dashboard
   - Click "Contact flows" in left menu
   - Click "Create contact flow"

2. **Name the flow**:
   - Click "Enter a name" at top
   - Name: `SarkariSaathi Main IVR Flow`
   - Description: `Main IVR flow with DTMF support`

3. **Enable Logging**:
   - From left panel, drag "Set logging behavior" block to canvas
   - Connect from "Entry point" to this block
   - Click on the block
   - Enable CloudWatch Logs
   - Click "Save"

4. **Enable Call Recording**:
   - Drag "Set recording and analytics behavior" block
   - Place it after logging block
   - Connect logging block to this block
   - Click on the block
   - Set "Call recording": On
   - Set "Analytics": Enable
   - Click "Save"

5. **Add Welcome Lambda**:
   - Drag "Invoke AWS Lambda function" block
   - Place after recording block
   - Connect recording to this block
   - Click on the block
   - Select function: `SarkariSaathi-IvrHandler`
   - Timeout: 8 seconds
   - Add parameter:
     - Key: `action`
     - Value: `handleIncomingCall`
   - Click "Save"

6. **Play Welcome Message**:
   - Drag "Play prompt" block
   - Connect Lambda "Success" to this block
   - Click on the block
   - Select "Text-to-speech"
   - Set to "User Defined"
   - In text field, type: `$.External.message`
   - Click "Save"

7. **Get DTMF Input**:
   - Drag "Get customer input" block
   - Connect from Play prompt
   - Click on the block
   - Select "User input"
   - Set timeout: 10 seconds
   - Set max digits: 1
   - Store customer input: Yes
   - Attribute name: `dtmfInput`
   - Click "Save"

8. **Process DTMF**:
   - Drag another "Invoke AWS Lambda function" block
   - Connect from "Get customer input" success
   - Click on the block
   - Select function: `SarkariSaathi-IvrHandler`
   - Timeout: 8 seconds
   - Add parameters:
     - Key: `action`, Value: `processDtmfInput`
     - Key: `dtmfInput`, Value: `$.StoredCustomerInput`
   - Click "Save"

9. **Check Should End**:
   - Drag "Check contact attributes" block
   - Connect from Lambda success
   - Click on the block
   - Attribute to check: `$.External.shouldEnd`
   - Add condition:
     - Condition: Equals
     - Value: `true`
   - Click "Save"

10. **Play Response**:
    - Drag "Play prompt" block
    - Connect from "Check Should End" No Match branch
    - Click on the block
    - Select "Text-to-speech"
    - Set to "User Defined"
    - Text: `$.External.message`
    - Click "Save"

11. **Add Disconnect Block**:
    - Drag "Disconnect / hang up" block
    - Connect from "Check Should End" Equals branch
    - This ends the call

12. **Loop Back for More Input**:
    - Connect "Play Response" back to "Get customer input"
    - This creates a loop for conversation

13. **Add Error Handling**:
    - Drag "Play prompt" block for errors
    - Connect all Error branches to this block
    - Set message: "We're experiencing technical difficulties"
    - Connect this to Disconnect block

14. **Save the Flow**:
    - Click "Save" button (top right)
    - Wait for save confirmation

15. **Publish the Flow**:
    - Click "Publish" button (top right)
    - Confirm publication
    - Note the Contact Flow ID from URL

### Step 9.5: Associate Flow with Phone Number

1. **Go to Phone Numbers**:
   - Click "Channels" → "Phone numbers"

2. **Click on your phone number**

3. **Edit phone number**:
   - Contact flow: Select "SarkariSaathi Main IVR Flow"
   - Click "Save"

### Step 9.6: Run Configuration Script

1. **Open Terminal in project directory**

2. **Make script executable** (macOS/Linux):

   ```bash
   chmod +x scripts/setup-connect-ivr.sh
   ```

3. **Run the script**:

   ```bash
   # macOS/Linux
   ./scripts/setup-connect-ivr.sh

   # Windows (use Git Bash or WSL)
   bash scripts/setup-connect-ivr.sh
   ```

4. **Enter the details when prompted**:
   - Instance ID: (from Step 9.1)
   - Contact Flow ID: (from Step 9.4)
   - Queue ID: (leave empty for now)
   - Phone Number: (from Step 9.2)

5. **Confirm**: Type `yes` when asked

6. **Wait for completion**: Script will configure everything

---

## 10. Testing and Verification

### Step 10.1: Test API Gateway

1. **Get API URL**:
   - Go to API Gateway in AWS Console
   - Click on "SarkariSaathi API"
   - Click "Stages" → "prod"
   - Copy the "Invoke URL"

2. **Test health endpoint**:

   ```bash
   curl https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/prod/health
   ```

   Should return:

   ```json
   {
     "status": "healthy",
     "timestamp": "2024-..."
   }
   ```

3. **Test with Postman** (optional):
   - Download Postman: https://www.postman.com/downloads/
   - Create new request
   - Method: GET
   - URL: `https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/prod/schemes`
   - Click "Send"
   - Should return list of schemes

### Step 10.2: Test Lambda Functions

1. **Go to Lambda Console**

2. **Select a function**: `SarkariSaathi-AudioInputHandler`

3. **Click "Test" tab**

4. **Create test event**:
   - Event name: `test-audio-input`
   - Template: API Gateway AWS Proxy
   - Modify the body:
     ```json
     {
       "body": "{\"audio\": \"base64-encoded-audio-data\"}",
       "headers": {
         "Content-Type": "application/json"
       }
     }
     ```
   - Click "Save"

5. **Click "Test"**

6. **Check results**:
   - Execution result should be "Succeeded"
   - Check the response
   - Check CloudWatch Logs link

### Step 10.3: Test IVR System

1. **Call the phone number** from your mobile

2. **Listen to welcome message**

3. **Test DTMF navigation**:
   - Press 1 for scheme discovery
   - Press 2 for eligibility check
   - Press 9 to repeat menu
   - Press 0 to end call

4. **Verify call recording**:
   - Go to S3 Console
   - Find Amazon Connect bucket
   - Navigate to recordings folder
   - Your call should be recorded

5. **Check CloudWatch Logs**:
   - Go to CloudWatch Console
   - Click "Log groups"
   - Find `/aws/lambda/SarkariSaathi-IvrHandler`
   - Click on latest log stream
   - Verify your call was logged

### Step 10.4: Test SMS (if configured)

1. **Get SMS endpoint**:

   ```
   https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/prod/sms
   ```

2. **Send test SMS** using curl:

   ```bash
   curl -X POST https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/prod/sms \
     -H "Content-Type: application/json" \
     -d '{
       "phoneNumber": "+919876543210",
       "message": "Tell me about PM-KISAN scheme"
     }'
   ```

3. **Check response**:
   - Should return success message
   - Check your phone for SMS reply

### Step 10.5: Verify DynamoDB Data

1. **Go to DynamoDB Console**

2. **Click "Tables"**

3. **Select "SarkariSaathi-Sessions"**

4. **Click "Explore table items"**

5. **Verify**:
   - You should see session entries from your tests
   - Check the data structure

6. **Repeat for other tables**:
   - Users table
   - Applications table
   - IvrCallbacks table

---

## 11. Monitoring Setup

### Step 11.1: Create CloudWatch Dashboard

1. **Go to CloudWatch Console**

2. **Click "Dashboards"** in left sidebar

3. **Click "Create dashboard"**

4. **Name**: `SarkariSaathi-Monitoring`

5. **Add widgets**:

   **Lambda Errors Widget:**
   - Click "Add widget"
   - Select "Line"
   - Select "Metrics"
   - Select "Lambda" → "By Function Name"
   - Select all your Lambda functions
   - Metric: "Errors"
   - Click "Create widget"

   **API Gateway Requests:**
   - Add another widget
   - Select "API Gateway" → "By API Name"
   - Select your API
   - Metric: "Count"
   - Click "Create widget"

   **DynamoDB Read/Write:**
   - Add widget
   - Select "DynamoDB" → "Table Metrics"
   - Select your tables
   - Metrics: "ConsumedReadCapacityUnits", "ConsumedWriteCapacityUnits"
   - Click "Create widget"

6. **Save dashboard**

### Step 11.2: Set Up Alarms

1. **Lambda Error Alarm**:
   - Go to CloudWatch → Alarms
   - Click "Create alarm"
   - Click "Select metric"
   - Select Lambda → By Function Name
   - Select `SarkariSaathi-IvrHandler` → Errors
   - Click "Select metric"
   - Conditions:
     - Threshold type: Static
     - Whenever Errors is: Greater than
     - Than: 5
   - Period: 5 minutes
   - Click "Next"
   - Notification:
     - Create new SNS topic
     - Topic name: `SarkariSaathi-Alerts`
     - Email: Your email
   - Click "Create topic"
   - Click "Next"
   - Alarm name: `SarkariSaathi-Lambda-Errors`
   - Click "Create alarm"

2. **Confirm SNS subscription**:
   - Check your email
   - Click confirmation link in email from AWS

3. **API Gateway 5XX Errors**:
   - Create another alarm
   - Metric: API Gateway → 5XXError
   - Threshold: Greater than 10
   - Same SNS topic as above

4. **DynamoDB Throttling**:
   - Create alarm
   - Metric: DynamoDB → UserErrors
   - Threshold: Greater than 5
   - Same SNS topic

### Step 11.3: Enable X-Ray Tracing (Optional)

1. **Go to Lambda Console**

2. **For each Lambda function**:
   - Click on function name
   - Go to "Configuration" tab
   - Click "Monitoring and operations tools"
   - Click "Edit"
   - Enable "Active tracing"
   - Click "Save"

3. **View traces**:
   - Go to X-Ray Console
   - Click "Service map"
   - You'll see visual representation of your services

---

## 12. Troubleshooting

### Issue 1: CDK Deploy Fails

**Error**: `Need to perform AWS calls for account XXX, but no credentials configured`

**Solution**:

```bash
# Reconfigure AWS CLI
aws configure

# Verify credentials
aws sts get-caller-identity
```

---

**Error**: `This stack uses assets, so the toolkit stack must be deployed`

**Solution**:

```bash
# Bootstrap CDK
cdk bootstrap aws://ACCOUNT-ID/ap-south-1
```

---

**Error**: `CREATE_FAILED` for some resources

**Solution**:

1. Check CloudFormation console for specific error
2. Common issues:
   - Bucket name already exists → Change bucket name in code
   - Insufficient permissions → Add required IAM policies
   - Service quota exceeded → Request quota increase
3. Delete failed stack:
   ```bash
   cdk destroy
   ```
4. Fix the issue and redeploy:
   ```bash
   cdk deploy
   ```

---

### Issue 2: Lambda Function Errors

**Error**: `Task timed out after 3.00 seconds`

**Solution**:

1. Go to Lambda Console
2. Click on function
3. Configuration → General configuration
4. Click "Edit"
5. Increase timeout to 30 seconds
6. Click "Save"

---

**Error**: `Unable to import module 'lambda_function'`

**Solution**:

1. Check Lambda deployment package
2. Verify all dependencies are included
3. Redeploy:
   ```bash
   cd lambda
   zip -r function.zip .
   aws lambda update-function-code \
     --function-name SarkariSaathi-IvrHandler \
     --zip-file fileb://function.zip
   ```

---

**Error**: `Access Denied` when accessing DynamoDB

**Solution**:

1. Go to IAM Console
2. Find Lambda execution role
3. Attach policy: `AmazonDynamoDBFullAccess`
4. OR create custom policy with specific table access

---

### Issue 3: Amazon Connect Issues

**Error**: Cannot claim phone number

**Solution**:

1. Check if your account is in sandbox mode
2. Request production access:
   - Go to Amazon Connect Console
   - Click "Support" → "Create case"
   - Request phone number access for your region
3. Wait for approval (usually 24-48 hours)

---

**Error**: Lambda not invoked from Contact Flow

**Solution**:

1. Verify Lambda is added to Amazon Connect:
   - Connect Console → Contact flows → AWS Lambda
   - Check if function is listed
2. Check Lambda permissions:
   ```bash
   aws lambda get-policy --function-name SarkariSaathi-IvrHandler
   ```
3. Add permission if missing:
   ```bash
   aws lambda add-permission \
     --function-name SarkariSaathi-IvrHandler \
     --statement-id AllowConnectInvoke \
     --action lambda:InvokeFunction \
     --principal connect.amazonaws.com
   ```

---

**Error**: Call recording not working

**Solution**:

1. Check S3 bucket permissions
2. Verify "Set recording behavior" block in contact flow
3. Check Amazon Connect instance settings:
   - Data storage → Call recordings
   - Ensure bucket is configured
   - Enable encryption

---

### Issue 4: API Gateway Errors

**Error**: `{"message":"Missing Authentication Token"}`

**Solution**:

1. Check API endpoint URL is correct
2. Verify the path exists:
   - Go to API Gateway Console
   - Check Resources
   - Ensure path is deployed
3. Redeploy API:
   - Click "Actions" → "Deploy API"
   - Stage: prod
   - Click "Deploy"

---

**Error**: `{"message":"Internal server error"}`

**Solution**:

1. Check Lambda function logs in CloudWatch
2. Enable API Gateway logging:
   - API Gateway Console
   - Settings
   - CloudWatch log role ARN: Create IAM role
   - Enable CloudWatch Logs
3. Check logs for detailed error

---

### Issue 5: DynamoDB Issues

**Error**: `ProvisionedThroughputExceededException`

**Solution**:

1. Go to DynamoDB Console
2. Click on table
3. Go to "Additional settings" tab
4. Change capacity mode:
   - From "Provisioned" to "On-demand"
   - OR increase provisioned capacity
5. Click "Save"

---

**Error**: Cannot find items in table

**Solution**:

1. Check if data was actually written:
   - Check Lambda logs
   - Look for write errors
2. Verify table name in Lambda environment variables
3. Check IAM permissions for Lambda

---

### Issue 6: Cost Issues

**Problem**: Unexpected high costs

**Solution**:

1. Check AWS Cost Explorer:
   - AWS Console → Cost Explorer
   - View costs by service
2. Common cost culprits:
   - OpenSearch domain (if running continuously)
   - NAT Gateway (if using VPC)
   - Data transfer
   - CloudWatch Logs (large volume)
3. Optimize:
   - Stop unused resources
   - Use S3 lifecycle policies
   - Reduce CloudWatch log retention
   - Use on-demand pricing for DynamoDB

---

### Issue 7: Bedrock Access Issues

**Error**: `AccessDeniedException` when calling Bedrock

**Solution**:

1. Go to Bedrock Console
2. Click "Model access" in left sidebar
3. Click "Manage model access"
4. Enable "Claude 3.5 Sonnet"
5. Wait for approval (usually instant)
6. Verify Lambda has Bedrock permissions:
   - Add policy: `AmazonBedrockFullAccess`

---

### Issue 8: Network/Connectivity Issues

**Error**: Lambda cannot connect to external APIs

**Solution**:

1. If Lambda is in VPC:
   - Add NAT Gateway for internet access
   - OR use VPC endpoints for AWS services
2. Check security groups:
   - Allow outbound traffic on required ports
3. Check network ACLs

---

### Issue 9: Python Dependencies Issues

**Error**: `ModuleNotFoundError: No module named 'boto3'`

**Solution**:

1. Install dependencies in Lambda layer:
   ```bash
   mkdir python
   pip install boto3 -t python/
   zip -r layer.zip python
   ```
2. Create Lambda layer:
   ```bash
   aws lambda publish-layer-version \
     --layer-name sarkari-saathi-dependencies \
     --zip-file fileb://layer.zip \
     --compatible-runtimes python3.9
   ```
3. Attach layer to Lambda function

---

### Issue 10: Debugging Tips

**Enable Debug Logging**:

```bash
# Set environment variable
aws lambda update-function-configuration \
  --function-name SarkariSaathi-IvrHandler \
  --environment Variables="{DEBUG=true,LOG_LEVEL=DEBUG}"
```

**View Real-time Logs**:

```bash
# Tail CloudWatch Logs
aws logs tail /aws/lambda/SarkariSaathi-IvrHandler --follow
```

**Test Lambda Locally**:

```bash
# Install SAM CLI
pip install aws-sam-cli

# Test function
sam local invoke SarkariSaathiIvrHandler -e test-event.json
```

---

## Additional Resources

### Official Documentation

- **AWS Documentation**: https://docs.aws.amazon.com/
- **AWS CDK Guide**: https://docs.aws.amazon.com/cdk/
- **Amazon Connect Guide**: https://docs.aws.amazon.com/connect/
- **Lambda Developer Guide**: https://docs.aws.amazon.com/lambda/
- **DynamoDB Guide**: https://docs.aws.amazon.com/dynamodb/

### Useful AWS CLI Commands

**List all Lambda functions**:

```bash
aws lambda list-functions --region ap-south-1
```

**List DynamoDB tables**:

```bash
aws dynamodb list-tables --region ap-south-1
```

**Get API Gateway endpoints**:

```bash
aws apigateway get-rest-apis --region ap-south-1
```

**View CloudWatch logs**:

```bash
aws logs describe-log-groups --region ap-south-1
```

**Check S3 buckets**:

```bash
aws s3 ls
```

**Get account ID**:

```bash
aws sts get-caller-identity --query Account --output text
```

### Cost Estimation

**Free Tier Limits** (first 12 months):

- Lambda: 1M requests/month, 400,000 GB-seconds compute
- DynamoDB: 25 GB storage, 25 read/write capacity units
- S3: 5 GB storage, 20,000 GET requests, 2,000 PUT requests
- API Gateway: 1M API calls/month
- CloudWatch: 10 custom metrics, 10 alarms

**Estimated Monthly Costs** (after free tier):

- Lambda: $5-10 (for moderate usage)
- DynamoDB: $5-15 (on-demand pricing)
- S3: $2-5 (with lifecycle policies)
- API Gateway: $3-7 (per million requests)
- Amazon Connect: $50-100 (depends on call volume)
- **Total: $65-137/month** (for moderate production usage)

### Security Best Practices

1. **Never commit credentials to Git**:

   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "*.pem" >> .gitignore
   echo "credentials.csv" >> .gitignore
   ```

2. **Use IAM roles instead of access keys** for Lambda

3. **Enable MFA** on root and IAM users

4. **Rotate access keys** every 90 days

5. **Use AWS Secrets Manager** for sensitive data

6. **Enable CloudTrail** for audit logging

7. **Use VPC** for sensitive Lambda functions

8. **Encrypt all data** at rest and in transit

### Monitoring Best Practices

1. **Set up billing alerts**:
   - Go to Billing Dashboard
   - Create budget alert
   - Set threshold (e.g., $50/month)

2. **Monitor key metrics**:
   - Lambda errors and duration
   - API Gateway 4XX/5XX errors
   - DynamoDB throttling
   - S3 storage growth

3. **Set up log retention**:
   - Default: Never expire (costly)
   - Recommended: 30-90 days
   - Archive old logs to S3 Glacier

4. **Use tags** for resource organization:
   ```bash
   aws lambda tag-resource \
     --resource arn:aws:lambda:... \
     --tags Project=SarkariSaathi,Environment=Production
   ```

---

## Next Steps

### After Successful Setup

1. **Populate scheme data**:
   - Upload scheme documents to S3
   - Run ingestion pipeline
   - Verify data in OpenSearch

2. **Test end-to-end flows**:
   - Voice input → scheme discovery
   - SMS interaction
   - IVR navigation
   - Application submission

3. **Set up CI/CD** (optional):
   - GitHub Actions
   - AWS CodePipeline
   - Automated testing

4. **Configure custom domain** (optional):
   - Register domain in Route 53
   - Create SSL certificate in ACM
   - Configure API Gateway custom domain

5. **Set up staging environment**:
   - Deploy separate stack for testing
   - Use different AWS account or region

6. **Implement monitoring dashboards**:
   - Business metrics
   - User engagement
   - System health

7. **Plan for scaling**:
   - Load testing
   - Auto-scaling configuration
   - Database optimization

### Getting Help

**AWS Support**:

- Basic (Free): Documentation, forums
- Developer ($29/month): Technical support
- Business ($100/month): 24/7 support

**Community Resources**:

- AWS Forums: https://forums.aws.amazon.com/
- Stack Overflow: Tag questions with `amazon-web-services`
- AWS Reddit: r/aws

**Project-Specific Help**:

- Check project documentation
- Review CloudWatch logs
- Enable debug mode
- Contact project maintainers

---

## Conclusion

You've now completed the full AWS setup for SarkariSaathi!

**What you've accomplished**:
✅ Created AWS account
✅ Configured IAM users and permissions
✅ Installed and configured AWS CLI
✅ Set up Node.js and AWS CDK
✅ Deployed infrastructure with CDK
✅ Configured Amazon Connect IVR
✅ Set up monitoring and alarms
✅ Tested all components

**Your system is now ready for**:

- Voice-based interactions
- SMS messaging
- IVR phone calls
- Scheme discovery and eligibility checking
- Application assistance

**Remember to**:

- Monitor costs regularly
- Keep credentials secure
- Update dependencies
- Review CloudWatch logs
- Test thoroughly before production use

Good luck with your SarkariSaathi project! 🚀
