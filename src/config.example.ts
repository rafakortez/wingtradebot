/**
 * Configuration Example File
 * 
 * Copy this file to config.ts and fill in your actual values.
 * NEVER commit config.ts to the repository - it contains sensitive data.
 * 
 * All sensitive values should come from environment variables.
 */

export const config = {
    PORT: parseInt(process.env.PORT || '443'),
    DEBUG_LEVEL: process.env.DEBUG_LEVEL || 'normal', // Options: 'normal', 'verbose'
    SERVER_IP: process.env.SERVER_IP || 'your_server_ip',
    ALLOWED_IPS: [
        // Add your allowed IP addresses here
        '127.0.0.1',
        '::ffff:127.0.0.1',
        '::1'
    ],

    // SimpleFX API Configuration
    SIMPLEFX_API_KEY: process.env.SIMPLEFX_API_KEY || '',
    SIMPLEFX_API_SECRET: process.env.SIMPLEFX_API_SECRET || '',
    SIMPLEFX_API_KEY2: process.env.SIMPLEFX_API_KEY2 || '',
    SIMPLEFX_API_SECRET2: process.env.SIMPLEFX_API_SECRET2 || '',
    SIMPLEFX_API_URL: 'https://rest.simplefx.com/api/v3',
    SIMPLEFX_QUOTES_URL: 'https://web-quotes-core.simplefx.com',

    // Circuit breaker parameters
    CIRCUIT_BREAKER: {
        FAILURE_THRESHOLD: 5,
        RESET_TIMEOUT: 60000, // 1 minute in milliseconds
        HALF_OPEN_TIMEOUT: 30000 // 30 seconds in milliseconds
    },

    // Rate limiting parameters
    RATE_LIMIT: {
        MAX_REQUESTS: 10,
        TIME_WINDOW: 60000 // 1 minute in milliseconds
    },

    // Bybit API Configuration (optional)
    BYBIT_API_KEY: process.env.BYBIT_API_KEY || '',
    BYBIT_API_SECRET: process.env.BYBIT_API_SECRET || '',
    BYBIT_TESTNET: process.env.BYBIT_TESTNET === 'true',
    BYBIT: {
        API_KEY: process.env.BYBIT_API_KEY || '',
        API_SECRET: process.env.BYBIT_API_SECRET || '',
        TESTNET: process.env.BYBIT_TESTNET === 'true',
    },

    // Status authentication
    STATUS_AUTH: {
        USERNAME: process.env.STATUS_AUTH_USERNAME || 'admin',
        PASSWORD: process.env.STATUS_AUTH_PASSWORD || ''
    },
    STATUS_AUTH2: {
        USERNAME: process.env.STATUS_AUTH2_USERNAME || 'admin',
        PASSWORD: process.env.STATUS_AUTH2_PASSWORD || ''
    }
};

// Account numbers
export const DEFAULT_ACCOUNT_NUMBER = process.env.DEFAULT_ACCOUNT_NUMBER || '';
export const DEFAULT_ACCOUNT_NUMBER2 = process.env.DEFAULT_ACCOUNT_NUMBER2 || '';

// Account configuration
export const SECONDARY_API_ACCOUNTS = [DEFAULT_ACCOUNT_NUMBER2]; // Accounts that use the secondary API
export const ALL_MONITORED_ACCOUNTS = [DEFAULT_ACCOUNT_NUMBER, DEFAULT_ACCOUNT_NUMBER2]; // All accounts to monitor

/**
 * Validates that all required environment variables are set
 * Call this function at application startup
 */
export function validateEnvironmentVariables(): void {
    const requiredVars = [
        'SIMPLEFX_API_KEY',
        'SIMPLEFX_API_SECRET',
        'SIMPLEFX_API_KEY2',
        'SIMPLEFX_API_SECRET2',
        'STATUS_AUTH_PASSWORD',
        'STATUS_AUTH2_PASSWORD',
        'DEFAULT_ACCOUNT_NUMBER',
        'DEFAULT_ACCOUNT_NUMBER2'
    ];

    const missingVars = requiredVars.filter(varName => !process.env[varName]);

    if (missingVars.length > 0) {
        console.error('❌ Missing required environment variables:');
        missingVars.forEach(varName => {
            console.error(`   - ${varName}`);
        });
        console.error('\n💡 Please check your .env file or environment configuration.');
        console.error('📋 See .env.example for required variables and their format.');
        console.error('📋 Copy src/config.example.ts to src/config.ts and configure with your values.');
        process.exit(1);
    }

    console.log('✅ All required environment variables are configured.');
}


