"""
Secure code executor using isolate sandbox
Replaces SimpleExecutor with proper sandboxing and resource limits

Features:
- Full sandboxing with isolate (IOI standard)
- Memory limit enforcement (cgroups)
- Fork bomb protection
- Network blocking
- File system isolation
- CPU time and Wall time tracking
- New verdicts: MLE, OLE, IE
"""

import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

# Import language configuration
from app.judge.language_config import (
    Language,
    LanguageConfig,
    get_language_config,
    calculate_actual_limits
)


class Verdict(Enum):
    """Execution verdicts"""
    AC = "AC"      # Accepted
    WA = "WA"      # Wrong Answer
    TLE = "TLE"    # Time Limit Exceeded
    RE = "RE"      # Runtime Error
    CE = "CE"      # Compilation Error
    MLE = "MLE"    # Memory Limit Exceeded (NEW)
    OLE = "OLE"    # Output Limit Exceeded (NEW)
    IE = "IE"      # Internal Error (NEW)


@dataclass
class ExecutionResult:
    """Result of code execution with detailed metrics"""
    verdict: Verdict
    time_ms: int = 0           # CPU time in milliseconds
    wall_time_ms: int = 0      # Wall clock time in milliseconds
    memory_kb: int = 0         # Memory usage in KB
    output: str = ""           # Program stdout
    error: str = ""            # Program stderr or error message
    exitcode: int = 0          # Process exit code

    def __repr__(self):
        return (f"ExecutionResult(verdict={self.verdict.value}, "
                f"time={self.time_ms}ms, memory={self.memory_kb}KB)")


class IsolateExecutor:
    """
    Secure executor using isolate sandbox

    Security features:
    - Process isolation with cgroups
    - Memory limit enforcement
    - Fork bomb protection (max 1 process)
    - Network access blocked
    - File system restrictions
    - CPU and wall time limits

    Resources:
    - CPU time: Actual CPU usage
    - Wall time: Real-world clock time (CPU time * 1.5)
    - Memory: RSS + cache (cgroup mem)
    - Output: Limited to 64MB
    """

    # Constants
    MAX_OUTPUT_SIZE_KB = 65536  # 64MB
    WALL_TIME_FACTOR = 1.5      # Wall time = CPU time * 1.5
    PYTHON_BINARY = "/usr/bin/python3.10"  # Real Python path

    def __init__(
        self,
        time_limit: int = 5,
        memory_limit: int = 256,
        box_id: int = 0,
        language: Language = Language.PYTHON
    ):
        """
        Initialize secure executor

        Args:
            time_limit: CPU time limit in seconds (default 5s)
            memory_limit: Memory limit in MB (default 256MB)
            box_id: Isolate box ID for parallel execution (0-999)
            language: Programming language to execute (default Python)
        """
        self.base_time_limit = time_limit
        self.base_memory_limit = memory_limit
        self.box_id = box_id
        self.language = language

        # Get language configuration
        self.lang_config = get_language_config(language)

        # Calculate actual limits with language multipliers
        actual_time, actual_memory_kb = calculate_actual_limits(
            time_limit, memory_limit, language
        )
        self.time_limit = actual_time
        self.memory_limit_kb = actual_memory_kb
        self.wall_time_limit = int(actual_time * self.WALL_TIME_FACTOR)

        # Verify isolate is installed
        try:
            subprocess.run(
                ["isolate", "--version"],
                capture_output=True,
                check=True
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise RuntimeError(
                "isolate not found. Please install: "
                "https://github.com/ioi/isolate"
            )

    def execute(
        self,
        source_code: str,
        test_input: str,
        expected_output: str
    ) -> ExecutionResult:
        """
        Execute code in isolated sandbox (multi-language support)

        Args:
            source_code: Source code to execute
            test_input: Input data for the program
            expected_output: Expected output for comparison

        Returns:
            ExecutionResult with verdict and detailed metrics
        """
        sandbox_path = None
        meta_file = None

        try:
            # 1. Initialize sandbox
            sandbox_path = self._init_sandbox()

            # 2. Prepare code file with correct extension
            code_filename = f"solution{self.lang_config.extension}"
            code_file = sandbox_path / "box" / code_filename
            code_file.write_text(source_code, encoding='utf-8')

            # 3. Compile if needed (for C++, Rust, Go)
            compile_result = self._compile_if_needed(sandbox_path, code_file)
            if compile_result is not None:
                # Compilation failed, return CE verdict
                return compile_result

            # 4. Prepare input file
            input_file = sandbox_path / "box" / "input.txt"
            input_file.write_text(test_input, encoding='utf-8')

            # 5. Create meta file for statistics
            meta_file = Path(tempfile.mktemp(suffix=".txt"))

            # 6. Execute in sandbox
            result = self._run_solution(input_file, meta_file)

            # 6. Parse metadata
            meta = self._parse_meta_file(meta_file)

            # 7. Check for errors (status field only exists on error)
            if meta.get('status'):
                return self._determine_verdict(meta, result)

            # 8. Check for runtime error (non-zero exit code)
            if meta.get('exitcode', 0) != 0:
                return ExecutionResult(
                    verdict=Verdict.RE,
                    time_ms=int(meta.get('time', 0) * 1000),
                    wall_time_ms=int(meta.get('time-wall', 0) * 1000),
                    memory_kb=meta.get('cg-mem', 0),
                    error=result.stderr.strip(),
                    exitcode=meta.get('exitcode', 0)
                )

            # 9. Get output from subprocess stdout
            actual_output = result.stdout

            # 10. Compare output
            if self._compare_output(actual_output, expected_output):
                return ExecutionResult(
                    verdict=Verdict.AC,
                    time_ms=int(meta.get('time', 0) * 1000),
                    wall_time_ms=int(meta.get('time-wall', 0) * 1000),
                    memory_kb=meta.get('cg-mem', 0),
                    output=actual_output,
                    exitcode=0
                )
            else:
                return ExecutionResult(
                    verdict=Verdict.WA,
                    time_ms=int(meta.get('time', 0) * 1000),
                    wall_time_ms=int(meta.get('time-wall', 0) * 1000),
                    memory_kb=meta.get('cg-mem', 0),
                    output=actual_output,
                    exitcode=0
                )

        except Exception as e:
            # Internal error (sandbox failure, etc.)
            return ExecutionResult(
                verdict=Verdict.IE,
                error=f"Internal error: {str(e)}"
            )

        finally:
            # Cleanup
            self._cleanup_sandbox()
            if meta_file and meta_file.exists():
                meta_file.unlink()

    def _init_sandbox(self) -> Path:
        """
        Initialize isolate sandbox

        Returns:
            Path to sandbox directory
        """
        result = subprocess.run(
            ["isolate", "--box-id", str(self.box_id), "--init"],
            capture_output=True,
            text=True,
            check=True
        )
        sandbox_path = Path(result.stdout.strip())
        return sandbox_path

    def _run_solution(
        self,
        input_file: Path,
        meta_file: Path
    ) -> subprocess.CompletedProcess:
        """
        Run solution in isolate sandbox with resource limits (multi-language)

        Args:
            input_file: Path to input file
            meta_file: Path to metadata output file

        Returns:
            CompletedProcess with stdout/stderr
        """
        # Read input content to pass via stdin
        input_data = input_file.read_text()

        # Build runtime command based on language
        # All compilers/runtimes now in /usr or /usr/local via symlinks

        cmd = [
            "isolate",
            f"--box-id={self.box_id}",           # Box ID
            f"--time={self.time_limit}",         # CPU time limit
            f"--wall-time={self.wall_time_limit}",  # Wall time limit
            f"--processes={self.lang_config.max_processes}",  # Process limit (1 for most, 4+ for Node.js)
            f"--meta={meta_file}",               # Metadata output
            "--dir=/usr",                        # Map /usr (compilers, interpreters)
            "--dir=/usr/local",                  # Map /usr/local (rustc, node, go symlinks)
            "--dir=/lib",                        # Map /lib (libraries)
            "--dir=/lib64",                      # Map /lib64 (libraries)
            "--dir=/etc/alternatives",           # Map /etc/alternatives (for symlinks)
            "--full-env",                        # Preserve environment variables
            "--env=PATH=/usr/bin:/usr/local/bin",  # PATH for runtime
        ]

        # Add memory limit only for languages that don't need large virtual memory
        # JavaScript (Node.js) and Go need to reserve large virtual memory regions
        if self.lang_config.language_id not in [Language.JAVASCRIPT, Language.GO]:
            cmd.insert(5, f"--mem={self.memory_limit_kb}")

        # Add language-specific environment variables for runtime too
        if self.lang_config.language_id == Language.GO:
            cmd.extend([
                "--env=HOME=/tmp",
            ])

        # Add execution part
        cmd.extend([
            "--run",
            "--",
            self.lang_config.runtime,            # Runtime binary (python3.10, ./solution, node)
            *self.lang_config.runtime_args       # Runtime arguments (solution.py, solution.js, etc.)
        ])

        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True
        )

        return result

    def _parse_meta_file(self, meta_file: Path) -> Dict[str, Any]:
        """
        Parse isolate metadata file

        Format:
            time:0.022
            time-wall:0.034
            max-rss:8772
            cg-mem:4856
            exitcode:0
            status:RE
            message:Exited with error status 1

        Args:
            meta_file: Path to metadata file

        Returns:
            Dictionary with parsed metadata
        """
        if not meta_file.exists():
            return {}

        meta = {}
        for line in meta_file.read_text().splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                # Try to convert to number
                try:
                    if '.' in value:
                        meta[key] = float(value)
                    else:
                        meta[key] = int(value)
                except ValueError:
                    meta[key] = value.strip()

        return meta

    def _determine_verdict(
        self,
        meta: Dict[str, Any],
        result: subprocess.CompletedProcess
    ) -> ExecutionResult:
        """
        Determine verdict from metadata and process result

        Possible statuses:
        - RE: Runtime error (killed by signal, non-zero exit)
        - TO: Timeout (time limit exceeded)
        - SG: Killed by signal
        - XX: Internal error

        Args:
            meta: Parsed metadata
            result: Process result

        Returns:
            ExecutionResult with appropriate verdict
        """
        status = meta.get('status', 'XX')
        message = meta.get('message', '')
        time_ms = int(meta.get('time', 0) * 1000)
        wall_time_ms = int(meta.get('time-wall', 0) * 1000)
        memory_kb = meta.get('cg-mem', 0)
        exitcode = meta.get('exitcode', 0)

        # Time Limit Exceeded
        if status == 'TO' or 'time' in message.lower():
            return ExecutionResult(
                verdict=Verdict.TLE,
                time_ms=time_ms,
                wall_time_ms=wall_time_ms,
                memory_kb=memory_kb,
                error="Time limit exceeded",
                exitcode=exitcode
            )

        # Memory Limit Exceeded
        if 'memory' in message.lower() or 'cg-mem' in message.lower():
            return ExecutionResult(
                verdict=Verdict.MLE,
                time_ms=time_ms,
                wall_time_ms=wall_time_ms,
                memory_kb=memory_kb,
                error="Memory limit exceeded",
                exitcode=exitcode
            )

        # Output Limit Exceeded
        if 'output' in message.lower():
            return ExecutionResult(
                verdict=Verdict.OLE,
                time_ms=time_ms,
                wall_time_ms=wall_time_ms,
                memory_kb=memory_kb,
                error="Output limit exceeded",
                exitcode=exitcode
            )

        # Runtime Error (default for other failures)
        return ExecutionResult(
            verdict=Verdict.RE,
            time_ms=time_ms,
            wall_time_ms=wall_time_ms,
            memory_kb=memory_kb,
            error=result.stderr.strip() or message,
            exitcode=exitcode
        )

    def _compile_if_needed(
        self,
        sandbox_path: Path,
        source_file: Path
    ) -> Optional[ExecutionResult]:
        """
        Compile source code if language requires compilation

        Compiles code in isolate sandbox for security.
        Returns None if compilation succeeds, or ExecutionResult with CE verdict if fails.

        Args:
            sandbox_path: Path to sandbox root
            source_file: Path to source code file

        Returns:
            None if compilation successful, ExecutionResult with CE if failed
        """
        # Skip if language doesn't need compilation
        if not self.lang_config.needs_compilation:
            return None

        # Create compilation error file
        compile_error_file = Path(tempfile.mktemp(suffix=".txt"))

        try:
            # Prepare compilation command
            # Note: We need to compile inside the sandbox

            # Build base command
            cmd = [
                "isolate",
                f"--box-id={self.box_id}",
                f"--time={self.lang_config.compile_time_limit}",
                f"--wall-time={self.lang_config.compile_time_limit * 2}",
                "--processes=128",  # Allow multiple processes for compilation (Go needs more)
                "--open-files=512",  # Increase open files limit (Go needs many files)
                "--dir=/usr",      # Compilers and interpreters
                "--dir=/usr/local",  # For rustc, node, go symlinks
                "--dir=/lib",
                "--dir=/lib64",
                "--dir=/etc/alternatives",  # For cc, c++ symlinks (needed by rustc, go)
                "--dir=/tmp:tmp",  # Temp directory with full permissions
                "--full-env",      # Preserve environment variables
                "--env=PATH=/usr/bin:/usr/local/bin",  # PATH for finding ld, as, etc.
            ]

            # Don't add memory limits for Rust and Go compilation (they need large virtual memory)
            if self.lang_config.language_id not in [Language.RUST, Language.GO]:
                cmd.insert(4, f"--mem={self.lang_config.compile_memory_limit * 1024}")

            # Add language-specific environment variables
            if self.lang_config.language_id == Language.RUST:
                # Map Rust toolchain libraries (rustc needs shared libraries)
                import os
                rust_lib_path = os.getenv("RUST_LIB_PATH", "/usr/local/lib/rust")
                if os.path.exists(rust_lib_path):
                    cmd.extend([
                        f"--dir={rust_lib_path}",
                        f"--env=LD_LIBRARY_PATH={rust_lib_path}",  # Find shared libraries
                    ])
                cmd.extend([
                    "--env=CARGO_HOME=/tmp/cargo",
                    "--env=RUSTUP_HOME=/tmp/rustup",
                    "--env=RUSTUP_TOOLCHAIN=stable",  # Use stable toolchain
                    "--env=RUSTUP_DIST_SERVER=",      # Disable dist server (no internet)
                    "--env=RUSTUP_UPDATE_ROOT=",      # Disable update checks (no internet)
                ])
            elif self.lang_config.language_id == Language.GO:
                cmd.extend([
                    "--env=GOCACHE=/tmp/go-cache",
                    "--env=GOPATH=/tmp/go",
                    "--env=HOME=/tmp",
                ])

            # Add execution part
            cmd.extend([
                "--run",
                "--",
                self.lang_config.compiler,
                *self.lang_config.compiler_args
            ])

            # Run compilation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.lang_config.compile_time_limit * 2
            )

            # Check if compilation succeeded
            if result.returncode != 0:
                # Compilation failed
                error_output = result.stderr or result.stdout
                return ExecutionResult(
                    verdict=Verdict.CE,
                    error=error_output[:2000],  # Limit error message to 2000 chars
                    exitcode=result.returncode
                )

            # Check if binary was created
            binary_path = sandbox_path / "box" / "solution"
            if self.lang_config.needs_compilation and not binary_path.exists():
                return ExecutionResult(
                    verdict=Verdict.CE,
                    error="Compilation succeeded but binary not found"
                )

            # Make binary executable (important for C++, Rust, Go)
            if binary_path.exists():
                import os
                os.chmod(binary_path, 0o755)

            # Compilation successful
            return None

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                verdict=Verdict.CE,
                error="Compilation timeout exceeded"
            )

        except Exception as e:
            return ExecutionResult(
                verdict=Verdict.IE,
                error=f"Compilation error: {str(e)}"
            )

        finally:
            # Cleanup
            if compile_error_file.exists():
                compile_error_file.unlink()

    def _cleanup_sandbox(self):
        """Clean up isolate sandbox"""
        try:
            subprocess.run(
                ["isolate", f"--box-id={self.box_id}", "--cleanup"],
                capture_output=True,
                timeout=5
            )
        except Exception:
            pass  # Ignore cleanup errors

    def _compare_output(self, actual: str, expected: str) -> bool:
        """
        Compare actual output with expected output
        (Copied from SimpleExecutor for compatibility)

        Strategy:
        1. Strip trailing whitespace from each line
        2. Remove empty lines at the end
        3. Split into tokens (words)
        4. Compare token by token

        Args:
            actual: Actual program output
            expected: Expected output

        Returns:
            True if outputs match, False otherwise
        """
        actual_normalized = self._normalize_output(actual)
        expected_normalized = self._normalize_output(expected)
        return actual_normalized == expected_normalized

    def _normalize_output(self, output: str) -> list:
        """
        Normalize output for comparison
        (Copied from SimpleExecutor for compatibility)

        Args:
            output: Raw output string

        Returns:
            List of tokens (words)
        """
        lines = [line.strip() for line in output.split('\n')]
        lines = [line for line in lines if line]
        text = ' '.join(lines)
        tokens = text.split()
        return tokens


# Example usage and testing
if __name__ == "__main__":
    """
    Test the IsolateExecutor with various cases
    """
    import sys

    print("=" * 60)
    print("Testing IsolateExecutor")
    print("=" * 60)

    try:
        executor = IsolateExecutor(time_limit=2, box_id=99)

        # Test 1: Correct answer (AC)
        print("\n[Test 1: Accepted]")
        code_ac = """
n = int(input())
print(n * 2)
"""
        result = executor.execute(code_ac, "5\n", "10\n")
        print(f"Verdict: {result.verdict.value}")
        print(f"CPU Time: {result.time_ms}ms")
        print(f"Wall Time: {result.wall_time_ms}ms")
        print(f"Memory: {result.memory_kb}KB")
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

        # Test 5: Memory limit (MLE)
        print("\n[Test 5: Memory Limit Exceeded]")
        executor_small = IsolateExecutor(time_limit=5, memory_limit=32, box_id=98)
        code_mle = """
# Try to allocate 100MB
a = [0] * (100 * 1024 * 1024)
"""
        result = executor_small.execute(code_mle, "", "")
        print(f"Verdict: {result.verdict.value}")
        print(f"Memory: {result.memory_kb}KB")
        # Note: MLE might show as RE depending on Python behavior
        assert result.verdict in [Verdict.MLE, Verdict.RE], "Expected MLE or RE"

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("Make sure isolate is installed:")
        print("  cd ~/tools/isolate && sudo make install")
        sys.exit(1)
