"""
Simple code executor for MVP
Uses subprocess with basic timeout
NO sandboxing (pospuesto para V2)
"""

import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional
from enum import Enum


class Verdict(Enum):
    """Execution verdicts"""
    AC = "AC"   # Accepted
    WA = "WA"   # Wrong Answer
    TLE = "TLE" # Time Limit Exceeded
    RE = "RE"   # Runtime Error
    CE = "CE"   # Compilation Error (not used for Python)


class ExecutionResult:
    """Result of code execution"""

    def __init__(
        self,
        verdict: Verdict,
        time_ms: int = 0,
        memory_kb: int = 0,
        output: str = "",
        error: str = ""
    ):
        self.verdict = verdict
        self.time_ms = time_ms
        self.memory_kb = memory_kb
        self.output = output
        self.error = error

    def __repr__(self):
        return f"ExecutionResult(verdict={self.verdict.value}, time={self.time_ms}ms, output='{self.output[:50]}...')"


class SimpleExecutor:
    """
    Simple executor for Python code
    MVP version - basic security only

    Features:
    - Timeout enforcement
    - stdout/stderr capture
    - Basic time measurement
    - String comparison

    Limitations (V2):
    - No memory limits
    - No sandboxing
    - No fork bomb protection
    - Only Python support
    """

    def __init__(self, time_limit: int = 5, memory_limit: int = 256):
        """
        Initialize executor

        Args:
            time_limit: Time limit in seconds (default 5s for MVP)
            memory_limit: Memory limit in MB (not enforced in MVP)
        """
        self.time_limit = time_limit
        self.memory_limit = memory_limit

    def execute(
        self,
        source_code: str,
        test_input: str,
        expected_output: str
    ) -> ExecutionResult:
        """
        Execute Python code against a test case

        Args:
            source_code: Python source code to execute
            test_input: Input data for the program
            expected_output: Expected output for comparison

        Returns:
            ExecutionResult with verdict and metrics
        """

        # Create temporary directory for isolated execution
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write source code to file
            solution_file = tmpdir_path / "solution.py"
            solution_file.write_text(source_code, encoding='utf-8')

            # Write input to file
            input_file = tmpdir_path / "input.txt"
            input_file.write_text(test_input, encoding='utf-8')

            try:
                # Measure execution time
                start_time = time.time()

                # Execute code with timeout
                with open(input_file, 'r') as stdin_file:
                    result = subprocess.run(
                        ["python3", "solution.py"],
                        cwd=tmpdir,
                        stdin=stdin_file,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=self.time_limit,
                        text=True,
                        encoding='utf-8'
                    )

                elapsed_ms = int((time.time() - start_time) * 1000)

                # Check for runtime error (non-zero exit code)
                if result.returncode != 0:
                    return ExecutionResult(
                        verdict=Verdict.RE,
                        time_ms=elapsed_ms,
                        error=result.stderr.strip()
                    )

                # Get actual output
                actual_output = result.stdout

                # Compare output with expected
                if self._compare_output(actual_output, expected_output):
                    return ExecutionResult(
                        verdict=Verdict.AC,
                        time_ms=elapsed_ms,
                        output=actual_output
                    )
                else:
                    return ExecutionResult(
                        verdict=Verdict.WA,
                        time_ms=elapsed_ms,
                        output=actual_output
                    )

            except subprocess.TimeoutExpired:
                # Time limit exceeded
                return ExecutionResult(
                    verdict=Verdict.TLE,
                    time_ms=self.time_limit * 1000,
                    error="Time limit exceeded"
                )

            except Exception as e:
                # Unexpected error
                return ExecutionResult(
                    verdict=Verdict.RE,
                    error=f"Execution error: {str(e)}"
                )

    def _compare_output(self, actual: str, expected: str) -> bool:
        """
        Compare actual output with expected output

        Strategy for MVP:
        1. Strip trailing whitespace from each line
        2. Remove empty lines at the end
        3. Split into tokens (words)
        4. Compare token by token

        This handles:
        - Extra/missing whitespace
        - Extra/missing newlines
        - Trailing spaces

        Future (V2):
        - Custom checkers for floating point comparison
        - Permutation checkers
        - Graph isomorphism

        Args:
            actual: Actual program output
            expected: Expected output

        Returns:
            True if outputs match, False otherwise
        """
        # Normalize outputs
        actual_normalized = self._normalize_output(actual)
        expected_normalized = self._normalize_output(expected)

        # Token-by-token comparison
        return actual_normalized == expected_normalized

    def _normalize_output(self, output: str) -> list:
        """
        Normalize output for comparison

        Args:
            output: Raw output string

        Returns:
            List of tokens (words)
        """
        # Split into lines, strip each line, filter empty lines
        lines = [line.strip() for line in output.split('\n')]
        lines = [line for line in lines if line]

        # Join and split into tokens
        text = ' '.join(lines)
        tokens = text.split()

        return tokens


# Example usage and testing
if __name__ == "__main__":
    """
    Test the SimpleExecutor with various cases
    """

    print("=" * 60)
    print("Testing SimpleExecutor")
    print("=" * 60)

    executor = SimpleExecutor(time_limit=2)

    # Test 1: Correct answer (AC)
    print("\n[Test 1: Accepted]")
    code_ac = """
n = int(input())
print(n * 2)
"""
    result = executor.execute(code_ac, "5\n", "10\n")
    print(f"Verdict: {result.verdict.value}")
    print(f"Time: {result.time_ms}ms")
    assert result.verdict == Verdict.AC, "Expected AC"

    # Test 2: Wrong answer (WA)
    print("\n[Test 2: Wrong Answer]")
    result = executor.execute(code_ac, "5\n", "15\n")
    print(f"Verdict: {result.verdict.value}")
    print(f"Expected: 15, Got: {result.output.strip()}")
    assert result.verdict == Verdict.WA, "Expected WA"

    # Test 3: Time limit exceeded (TLE)
    print("\n[Test 3: Time Limit Exceeded]")
    code_tle = """
while True:
    pass
"""
    result = executor.execute(code_tle, "", "")
    print(f"Verdict: {result.verdict.value}")
    print(f"Time: {result.time_ms}ms (limit: {executor.time_limit * 1000}ms)")
    assert result.verdict == Verdict.TLE, "Expected TLE"

    # Test 4: Runtime error (RE)
    print("\n[Test 4: Runtime Error]")
    code_re = """
x = 1 / 0
"""
    result = executor.execute(code_re, "", "")
    print(f"Verdict: {result.verdict.value}")
    print(f"Error: {result.error[:100]}")
    assert result.verdict == Verdict.RE, "Expected RE"

    # Test 5: Whitespace handling (AC)
    print("\n[Test 5: Whitespace Handling]")
    code_ws = """
print("Hello   World")
print("Test")
"""
    # Extra spaces and newlines should be ignored
    result = executor.execute(code_ws, "", "Hello World\nTest\n")
    print(f"Verdict: {result.verdict.value}")
    assert result.verdict == Verdict.AC, "Expected AC (whitespace normalized)"

    # Test 6: Multi-line output (AC)
    print("\n[Test 6: Multi-line Output]")
    code_multi = """
for i in range(1, 4):
    print(i)
"""
    result = executor.execute(code_multi, "", "1\n2\n3\n")
    print(f"Verdict: {result.verdict.value}")
    assert result.verdict == Verdict.AC, "Expected AC"

    # Test 7: Reading input (AC)
    print("\n[Test 7: Reading Input]")
    code_input = """
a, b = map(int, input().split())
print(a + b)
"""
    result = executor.execute(code_input, "3 5\n", "8\n")
    print(f"Verdict: {result.verdict.value}")
    assert result.verdict == Verdict.AC, "Expected AC"

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
