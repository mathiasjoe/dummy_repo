# dummy_repo
Dummy repo for å teste action for å få sarif fil i Security tab

## Purpose
This repository is designed to test GitHub Actions security scanning functionality that generates SARIF (Static Analysis Results Interchange Format) files for display in GitHub's Security tab.

## What's included
- **GitHub Actions Workflow**: `.github/workflows/security-scan.yml` runs CodeQL and ESLint security scans
- **Vulnerable Code Samples**: Intentionally insecure JavaScript files to trigger security findings
- **SARIF Generation**: Both CodeQL and ESLint are configured to output SARIF files
- **Security Tab Integration**: Results are automatically uploaded to GitHub's Security tab

## Files
- `vulnerable-app.js` - Contains various security vulnerabilities for testing
- `security-issues.js` - Additional security issues and anti-patterns
- `package.json` - Node.js project configuration with security scanning dependencies
- `eslint.config.js` - ESLint configuration with security rules enabled

## How it works
1. When code is pushed or a PR is created, the GitHub Actions workflow runs
2. CodeQL analyzes the JavaScript code for security vulnerabilities
3. ESLint with security plugins performs additional security checks
4. Both tools generate SARIF files with their findings
5. SARIF files are uploaded to GitHub's Security tab for review

The intentionally vulnerable code will generate multiple security alerts that can be viewed in the repository's Security tab.
