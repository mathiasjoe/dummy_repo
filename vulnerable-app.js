// Sample vulnerable JavaScript code for testing security scanning
const express = require('express');
const app = express();

// Vulnerability 1: Using eval() - potential code injection
function processUserInput(userInput) {
    return eval(userInput); // This is dangerous!
}

// Vulnerability 2: SQL injection potential
function getUserData(userId) {
    const query = "SELECT * FROM users WHERE id = " + userId; // SQL injection risk
    return query;
}

// Vulnerability 3: XSS vulnerability
app.get('/user/:name', (req, res) => {
    const userName = req.params.name;
    res.send(`<h1>Welcome ${userName}!</h1>`); // XSS risk - unescaped user input
});

// Vulnerability 4: Hardcoded credentials
const API_KEY = "12345-secret-api-key"; // Hardcoded secret
const PASSWORD = "admin123"; // Hardcoded password

// Vulnerability 5: Insecure random number generation
function generateToken() {
    return Math.random().toString(36); // Weak random number generation
}

// Vulnerability 6: Prototype pollution
function merge(target, source) {
    for (let key in source) {
        target[key] = source[key]; // Prototype pollution risk
    }
    return target;
}

// Vulnerability 7: Path traversal
const fs = require('fs');
app.get('/file/:filename', (req, res) => {
    const filename = req.params.filename;
    fs.readFile(`./uploads/${filename}`, (err, data) => { // Path traversal risk
        if (err) {
            res.status(404).send('File not found');
        } else {
            res.send(data);
        }
    });
});

// Vulnerability 8: Unsafe regex
function validateEmail(email) {
    const regex = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/; // ReDoS potential
    return regex.test(email);
}

module.exports = {
    processUserInput,
    getUserData,
    generateToken,
    merge,
    validateEmail
};