import asyncio
import sys
import os

# Добавляем путь к backend в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.elasticsearch_utils import diagnose_index

async def main():
    await diagnose_index()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
