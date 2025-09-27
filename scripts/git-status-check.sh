#!/bin/bash
# Git status check script for task transitions
# Run this before starting any new task

echo "🔍 === Git Status Check ==="
echo ""

echo "📊 Current Status:"
git status --porcelain
if [ $? -eq 0 ] && [ -z "$(git status --porcelain)" ]; then
    echo "✅ Working tree is clean"
else
    echo "⚠️  Uncommitted changes detected!"
    echo ""
    echo "📁 Detailed status:"
    git status
    echo ""
    echo "💡 Run: git add -A && git commit -m 'Description' before continuing"
    exit 1
fi

echo ""
echo "📝 Recent commits:"
git log --oneline -3

echo ""
echo "🌟 Ready for next task!"