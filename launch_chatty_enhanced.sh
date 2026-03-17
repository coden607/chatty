#!/bin/bash
# CHATTY Enhanced Launcher
# Automatically uses the new integrated systems

echo "🚀 CHATTY Enhanced System Launcher"
echo "======================================"

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "🔧 Activating virtual environment..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo "❌ Virtual environment not found at .venv/"
        exit 1
    fi
fi

# Use the virtual environment's Python
PYTHON_CMD="${VIRTUAL_ENV}/bin/python3"

echo "🔍 Running system validation..."
${PYTHON_CMD} CHATTY_SYSTEM_VALIDATOR.py
VALIDATION_STATUS=$?

if [ $VALIDATION_STATUS -eq 2 ]; then
    echo "❌ System validation failed critically"
    echo "Please check the validation report in generated_content/system_validation_report.json"
    exit 1
elif [ $VALIDATION_STATUS -eq 1 ]; then
    echo "⚠️ System validation shows warnings"
    echo "Continuing with degraded functionality..."
fi

# Start the system with enhanced integration
echo "🚀 Starting CHATTY with enhanced integration..."
export CHATTY_REAL_DATA_MODE=true
export CHATTY_GUARDRAILS=true
export CHATTY_MODEL_FAILOVER=true

# Run the main automation system
${PYTHON_CMD} START_COMPLETE_AUTOMATION.py "$@"
