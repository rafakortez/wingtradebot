import axios, { AxiosResponse } from 'axios';
import { config } from '../config';

interface AuthResult {
  success: boolean;
  token?: string;
  error?: string;
  responseTime: number;
  statusCode?: number;
  details?: any;
}

interface AccountData {
  success: boolean;
  data?: any;
  error?: string;
  responseTime: number;
  statusCode?: number;
}

export class SimpleFXAPITester {
  private baseURL = config.SIMPLEFX_API_URL;

  /**
   * Test authentication with primary API credentials
   */
  async testPrimaryAuthentication(): Promise<AuthResult> {
    return this.testAuthentication(
      config.SIMPLEFX_API_KEY,
      config.SIMPLEFX_API_SECRET,
      'Primary'
    );
  }

  /**
   * Test authentication with secondary API credentials
   */
  async testSecondaryAuthentication(): Promise<AuthResult> {
    return this.testAuthentication(
      config.SIMPLEFX_API_KEY2,
      config.SIMPLEFX_API_SECRET2,
      'Secondary'
    );
  }

  /**
   * Test authentication with provided credentials
   */
  async testAuthentication(apiKey: string, secret: string, label: string = 'Unknown'): Promise<AuthResult> {
    const startTime = Date.now();

    try {
      console.log(`\n🔐 Testing ${label} API Authentication...`);
      console.log(`API Key: ${apiKey}`);
      console.log(`Secret: ${secret.substring(0, 8)}...`);

      const response: AxiosResponse = await axios.post(
        `${this.baseURL}/auth/key`,
        {
          clientId: apiKey,
          clientSecret: secret
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'WingTradeBot/1.0'
          },
          timeout: 10000
        }
      );

      const responseTime = Date.now() - startTime;

      if (response.status === 200 && response.data.data && response.data.data.token) {
        console.log(`✅ ${label} Authentication successful!`);
        console.log(`Token: ${response.data.data.token.substring(0, 20)}...`);
        console.log(`Response time: ${responseTime}ms`);

        return {
          success: true,
          token: response.data.data.token,
          responseTime,
          statusCode: response.status,
          details: response.data
        };
      } else {
        console.log(`❌ ${label} Authentication failed - Invalid response format`);
        console.log(`Status: ${response.status}`);
        console.log(`Response:`, response.data);

        return {
          success: false,
          error: 'Invalid response format',
          responseTime,
          statusCode: response.status,
          details: response.data
        };
      }
    } catch (error: any) {
      const responseTime = Date.now() - startTime;

      console.log(`❌ ${label} Authentication failed!`);
      console.log(`Error: ${error.message}`);

      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Response:`, error.response.data);

        return {
          success: false,
          error: error.message,
          responseTime,
          statusCode: error.response.status,
          details: error.response.data
        };
      } else {
        console.log(`Network error or timeout`);

        return {
          success: false,
          error: error.message,
          responseTime,
          details: { networkError: true }
        };
      }
    }
  }

  /**
   * Validate a bearer token by making a test API call
   */
  async validateBearerToken(token: string): Promise<boolean> {
    try {
      console.log(`\n🔍 Validating bearer token...`);

      const response = await axios.get(
        `${this.baseURL}/accounts`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          timeout: 10000
        }
      );

      if (response.status === 200) {
        console.log(`✅ Bearer token is valid`);
        console.log(`Accounts found: ${response.data.length || 'N/A'}`);
        return true;
      } else {
        console.log(`❌ Bearer token validation failed - Status: ${response.status}`);
        return false;
      }
    } catch (error: any) {
      console.log(`❌ Bearer token validation failed: ${error.message}`);
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Response:`, error.response.data);
      }
      return false;
    }
  }

  /**
   * Test account access with specific login number and reality
   */
  async testAccountAccess(loginNumber: string, reality: string, token: string): Promise<AccountData> {
    const startTime = Date.now();

    try {
      console.log(`\n📊 Testing account access...`);
      console.log(`Login: ${loginNumber}, Reality: ${reality}`);

      const response = await axios.get(
        `${this.baseURL}/accounts/${loginNumber}?reality=${reality}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          timeout: 10000
        }
      );

      const responseTime = Date.now() - startTime;

      if (response.status === 200) {
        console.log(`✅ Account access successful!`);
        console.log(`Balance: ${response.data.balance || 'N/A'}`);
        console.log(`Currency: ${response.data.currency || 'N/A'}`);
        console.log(`Response time: ${responseTime}ms`);

        return {
          success: true,
          data: response.data,
          responseTime,
          statusCode: response.status
        };
      } else {
        console.log(`❌ Account access failed - Status: ${response.status}`);

        return {
          success: false,
          error: `HTTP ${response.status}`,
          responseTime,
          statusCode: response.status
        };
      }
    } catch (error: any) {
      const responseTime = Date.now() - startTime;

      console.log(`❌ Account access failed: ${error.message}`);

      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Response:`, error.response.data);

        return {
          success: false,
          error: error.message,
          responseTime,
          statusCode: error.response.status
        };
      } else {
        return {
          success: false,
          error: error.message,
          responseTime
        };
      }
    }
  }

  /**
   * Run comprehensive API tests
   */
  async runComprehensiveTest(): Promise<void> {
    console.log('\n🚀 Starting comprehensive SimpleFX API tests...\n');

    // Test primary authentication
    const primaryAuth = await this.testPrimaryAuthentication();

    // Test secondary authentication
    const secondaryAuth = await this.testSecondaryAuthentication();

    // If primary auth succeeded, test account access
    if (primaryAuth.success && primaryAuth.token) {
      await this.validateBearerToken(primaryAuth.token);
      await this.testAccountAccess('3028761', 'real', primaryAuth.token);
    }

    // If secondary auth succeeded, test account access
    if (secondaryAuth.success && secondaryAuth.token) {
      await this.validateBearerToken(secondaryAuth.token);
      await this.testAccountAccess('3979937', 'real', secondaryAuth.token);
    }

    console.log('\n📋 Test Summary:');
    console.log(`Primary API: ${primaryAuth.success ? '✅ Success' : '❌ Failed'} (${primaryAuth.responseTime}ms)`);
    console.log(`Secondary API: ${secondaryAuth.success ? '✅ Success' : '❌ Failed'} (${secondaryAuth.responseTime}ms)`);

    if (!primaryAuth.success && !secondaryAuth.success) {
      console.log('\n⚠️  Both API credentials failed. Check:');
      console.log('1. API keys and secrets are correct');
      console.log('2. Server IP is whitelisted with SimpleFX');
      console.log('3. Network connectivity to SimpleFX servers');
      console.log('4. CloudFront/CDN blocking issues');
    }
  }
}

export class CurlCommandGenerator {
  private baseURL = config.SIMPLEFX_API_URL;

  /**
   * Generate curl command for authentication
   */
  generateAuthCommand(apiKey: string, secret: string, label: string = ''): string {
    return `# ${label} Authentication
curl -X POST "${this.baseURL}/auth/key" \\
  -H "Content-Type: application/json" \\
  -H "User-Agent: WingTradeBot/1.0" \\
  -d '{
    "clientId": "${apiKey}",
    "clientSecret": "${secret}"
  }' \\
  --connect-timeout 10 \\
  --max-time 30 \\
  -v`;
  }

  /**
   * Generate curl command for account access
   */
  generateAccountCommand(loginNumber: string, reality: string, token: string): string {
    return `# Account Access Test
curl -X GET "${this.baseURL}/accounts/${loginNumber}?reality=${reality}" \\
  -H "Authorization: Bearer ${token}" \\
  -H "Content-Type: application/json" \\
  --connect-timeout 10 \\
  --max-time 30 \\
  -v`;
  }

  /**
   * Generate curl command for accounts list
   */
  generateAccountsListCommand(token: string): string {
    return `# List All Accounts
curl -X GET "${this.baseURL}/accounts" \\
  -H "Authorization: Bearer ${token}" \\
  -H "Content-Type: application/json" \\
  --connect-timeout 10 \\
  --max-time 30 \\
  -v`;
  }

  /**
   * Generate all curl commands for testing
   */
  generateAllCommands(): string[] {
    const commands: string[] = [];

    // Primary API authentication
    commands.push(this.generateAuthCommand(
      config.SIMPLEFX_API_KEY,
      config.SIMPLEFX_API_SECRET,
      'Primary API'
    ));

    // Secondary API authentication
    commands.push(this.generateAuthCommand(
      config.SIMPLEFX_API_KEY2,
      config.SIMPLEFX_API_SECRET2,
      'Secondary API'
    ));

    // Account access commands (with placeholder tokens)
    commands.push(this.generateAccountCommand(
      '3028761',
      'real',
      'YOUR_PRIMARY_TOKEN_HERE'
    ));

    commands.push(this.generateAccountCommand(
      '3979937',
      'real',
      'YOUR_SECONDARY_TOKEN_HERE'
    ));

    // Accounts list commands
    commands.push(this.generateAccountsListCommand('YOUR_TOKEN_HERE'));

    return commands;
  }

  /**
   * Print all curl commands to console
   */
  printAllCommands(): void {
    console.log('\n📋 SimpleFX API Testing - Curl Commands\n');
    console.log('='.repeat(60));

    const commands = this.generateAllCommands();

    commands.forEach((command, index) => {
      console.log(`\n${index + 1}. ${command}\n`);
      console.log('-'.repeat(60));
    });

    console.log('\n💡 Usage Instructions:');
    console.log('1. Run authentication commands first to get bearer tokens');
    console.log('2. Replace YOUR_TOKEN_HERE with actual tokens from step 1');
    console.log('3. Check response status codes and error messages');
    console.log('4. Look for 403 errors indicating IP blocking');
    console.log('5. Look for 401 errors indicating credential issues');
  }

  /**
   * Generate a quick test script
   */
  generateTestScript(): string {
    return `#!/bin/bash
# SimpleFX API Quick Test Script
# Generated on ${new Date().toISOString()}

echo "🚀 Testing SimpleFX API Authentication..."

# Test Primary API
echo "Testing Primary API..."
PRIMARY_RESPONSE=$(curl -s -X POST "${this.baseURL}/auth/key" \\
  -H "Content-Type: application/json" \\
  -H "User-Agent: WingTradeBot/1.0" \\
  -d '{
    "clientId": "${config.SIMPLEFX_API_KEY}",
    "clientSecret": "${config.SIMPLEFX_API_SECRET}"
  }' \\
  --connect-timeout 10 \\
  --max-time 30 \\
  -w "HTTPSTATUS:%{http_code}")

HTTP_STATUS=$(echo $PRIMARY_RESPONSE | tr -d '\\n' | sed -e 's/.*HTTPSTATUS://')
RESPONSE_BODY=$(echo $PRIMARY_RESPONSE | sed -e 's/HTTPSTATUS:.*//')

echo "Primary API Status: $HTTP_STATUS"
echo "Primary API Response: $RESPONSE_BODY"

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Primary API authentication successful"
    PRIMARY_TOKEN=$(echo $RESPONSE_BODY | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo "Token: \${PRIMARY_TOKEN:0:20}..."
else
    echo "❌ Primary API authentication failed"
fi

echo ""

# Test Secondary API
echo "Testing Secondary API..."
SECONDARY_RESPONSE=$(curl -s -X POST "${this.baseURL}/auth/key" \\
  -H "Content-Type: application/json" \\
  -H "User-Agent: WingTradeBot/1.0" \\
  -d '{
    "clientId": "${config.SIMPLEFX_API_KEY2}",
    "clientSecret": "${config.SIMPLEFX_API_SECRET2}"
  }' \\
  --connect-timeout 10 \\
  --max-time 30 \\
  -w "HTTPSTATUS:%{http_code}")

HTTP_STATUS=$(echo $SECONDARY_RESPONSE | tr -d '\\n' | sed -e 's/.*HTTPSTATUS://')
RESPONSE_BODY=$(echo $SECONDARY_RESPONSE | sed -e 's/HTTPSTATUS:.*//')

echo "Secondary API Status: $HTTP_STATUS"
echo "Secondary API Response: $RESPONSE_BODY"

if [ $HTTP_STATUS -eq 200 ]; then
    echo "✅ Secondary API authentication successful"
    SECONDARY_TOKEN=$(echo $RESPONSE_BODY | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo "Token: \${SECONDARY_TOKEN:0:20}..."
else
    echo "❌ Secondary API authentication failed"
fi

echo ""
echo "🏁 Test completed. Check the status codes above:"
echo "- 200: Success"
echo "- 401: Invalid credentials"
echo "- 403: IP blocked or forbidden"
echo "- 500: Server error"
echo "- Connection errors: Network/DNS issues"
`;
  }
}

// Utility function to run API tests from command line
export async function runAPITests(): Promise<void> {
  const tester = new SimpleFXAPITester();
  await tester.runComprehensiveTest();
}

// Utility function to generate curl commands
export function generateCurlCommands(): void {
  const generator = new CurlCommandGenerator();
  generator.printAllCommands();
}

// Utility function to create test script file
export function createTestScript(): void {
  const generator = new CurlCommandGenerator();
  const script = generator.generateTestScript();

  console.log('\n📝 Test script generated. Save this as test-api.sh:');
  console.log('='.repeat(60));
  console.log(script);
  console.log('='.repeat(60));
  console.log('\n💡 To use: chmod +x test-api.sh && ./test-api.sh');
}