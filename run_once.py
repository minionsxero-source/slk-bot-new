import asyncio
from main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped safely. You can run the scan again with: python run_once.py")
