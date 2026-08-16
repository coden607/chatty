import sys
from unittest.mock import MagicMock

# Mock heavy dependencies
sys.modules["AUTOMATED_REVENUE_ENGINE"] = MagicMock()
sys.modules["AUTOMATED_CUSTOMER_ACQUISITION"] = MagicMock()
sys.modules["START_COMPLETE_AUTOMATION"] = MagicMock()

import uvicorn
from AUTOMATION_API_SERVER import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
