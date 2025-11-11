#!/bin/bash
# Script to push code to GitHub with authentication

# Get the GIT_URL from environment (should be in format: https://username:token@github.com/...)
if [ -z "$GIT_URL" ]; then
    echo "ERROR: GIT_URL secret not found"
    exit 1
fi

echo "Pushing main branch to GitHub..."
git push "$GIT_URL" main

echo "Pushing replit-agent branch to GitHub..."
git push "$GIT_URL" replit-agent

echo "Done! Your code is now on GitHub."
