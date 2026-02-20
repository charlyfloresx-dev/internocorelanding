import pytest
import sys
import os

# Add local and parent paths
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

class TracebackPlugin:
    def pytest_exception_interact(self, node, call, report):
        if report.failed:
            print("\n" + "="*80)
            print(f"FAILURE IN: {node.nodeid}")
            print(f"EXCEPTION: {call.excinfo.type.__name__}: {call.excinfo.value}")
            print("TRACEBACK:")
            import traceback
            traceback.print_tb(call.excinfo.tb)
            print("="*80 + "\n")

if __name__ == "__main__":
    pytest.main(["tests/test_smoke.py", "-v", "-s"], plugins=[TracebackPlugin()])
