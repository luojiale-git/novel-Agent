#!/usr/bin/env python
"""灵枢桌面版 - 后端启动脚本"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
        log_level="info",
    )
