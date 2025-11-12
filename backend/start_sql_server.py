#!/usr/bin/env python3
"""
Start the SQL API server for semantic layer.

This script starts a PostgreSQL-compatible server that allows
BI tools and SQL clients to connect to the semantic layer.
"""

import asyncio
import sys
import signal
from pathlib import Path

# Add backend app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.sql_api.server import SQLServer
from app.core.logging import setup_logging
import structlog

# Setup logging
setup_logging()
logger = structlog.get_logger()


async def main():
    """Main entry point."""
    # Create SQL server
    server = SQLServer(
        host="0.0.0.0",
        port=5433,  # Use 5433 to avoid conflicts with local PostgreSQL
        database="semantic_layer",
        max_connections=100
    )
    
    # Handle shutdown gracefully
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(server.stop())
        
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        logger.info("Starting SQL API server on port 5433")
        logger.info("Connect using: psql -h localhost -p 5433 -U user -d semantic_layer")
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down SQL server")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass




