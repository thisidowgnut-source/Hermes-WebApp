import sys
import pytest

print("=== Running Hermes-WebApp Social Delivery Tests ===", flush=True)

exit_code = pytest.main([
    "tests/test_social_delivery.py",
    "-v",
    "-o", "timeout=0",
    "--capture=no",
])

print(f"=== Pytest Finished with Exit Code: {exit_code} ===", flush=True)
sys.exit(exit_code)
