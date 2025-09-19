// Additional vulnerable code for comprehensive security testing
const crypto = require('crypto');
const http = require('http');

class SecurityVulnerabilities {
    constructor() {
        this.secretKey = "hardcoded-secret-2023"; // Another hardcoded secret
    }

    // Vulnerability: Weak encryption
    encryptData(data) {
        const cipher = crypto.createCipher('des', this.secretKey); // Weak algorithm
        let encrypted = cipher.update(data, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        return encrypted;
    }

    // Vulnerability: Insecure HTTP request
    makeRequest(url) {
        return new Promise((resolve, reject) => {
            http.get(url, (res) => { // Using HTTP instead of HTTPS
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                res.on('end', () => {
                    resolve(data);
                });
            }).on('error', reject);
        });
    }

    // Vulnerability: Command injection
    executeCommand(userCommand) {
        const { exec } = require('child_process');
        exec(`ls -la ${userCommand}`, (error, stdout, stderr) => { // Command injection risk
            console.log(stdout);
        });
    }

    // Vulnerability: Unsafe object access
    getProperty(obj, path) {
        return path.split('.').reduce((current, prop) => {
            return current[prop]; // No validation - can access __proto__
        }, obj);
    }

    // Vulnerability: Information disclosure
    logSensitiveData(user) {
        console.log(`User login: ${JSON.stringify(user)}`); // May log sensitive data
    }
}

// Vulnerability: Global variable pollution
global.ADMIN_MODE = true;
process.env.SECRET_TOKEN = "exposed-token-123";

// Export the vulnerable class
module.exports = SecurityVulnerabilities;