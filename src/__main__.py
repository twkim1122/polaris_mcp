"""Entry point for running as: python -m partner_polaris_mcp"""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from partner_polaris_mcp.server import main

if __name__ == "__main__":
    main()
