"""
Language Configuration for Multi-Language Judge Support

Defines supported languages and their compilation/execution configurations.
Each language has specific settings for:
- Compilation (if needed)
- Runtime execution
- Time multipliers (language speed differences)
- Memory grace (interpreter/runtime overhead)

Supported Languages (MVP):
1. Python 3.10 (interpreted)
2. C++17 (compiled)
3. Rust 2021 (compiled)
4. JavaScript/Node.js (interpreted)
5. Go 1.20+ (compiled)

Configuration is loaded from environment variables for portability.
See .env.example for all available settings.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, try manual loading
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)


class Language(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    CPP = "cpp"
    RUST = "rust"
    JAVASCRIPT = "javascript"
    GO = "go"


@dataclass
class LanguageConfig:
    """
    Configuration for a programming language

    Attributes:
        name: Display name of the language
        language_id: Language enum value
        extension: File extension (e.g., ".py", ".cpp")

        # Compilation settings (None if interpreted)
        needs_compilation: Whether language needs compilation step
        compiler: Compiler binary path (e.g., "g++", "rustc")
        compiler_args: Arguments for compiler
        compile_time_limit: Max compilation time in seconds
        compile_memory_limit: Max compilation memory in MB

        # Runtime settings
        runtime: Runtime binary path (e.g., "python3", "./solution")
        runtime_args: Arguments for runtime
        max_processes: Max processes allowed (1 for most, 4+ for Node.js)

        # Resource multipliers (relative to C++)
        time_multiplier: CPU time multiplier (1.0 = baseline, 3.0 = 3x slower)
        memory_grace_kb: Extra memory allowed for runtime overhead

        # Metadata
        version_command: Command to check version (for debugging)
    """

    # Basic info
    name: str
    language_id: Language
    extension: str

    # Compilation
    needs_compilation: bool
    compiler: Optional[str] = None
    compiler_args: List[str] = None
    compile_time_limit: int = 30  # seconds
    compile_memory_limit: int = 1024  # MB

    # Runtime
    runtime: str = None
    runtime_args: List[str] = None
    max_processes: int = 1  # Most languages need only 1, Node.js needs more

    # Resource multipliers
    time_multiplier: float = 1.0
    memory_grace_kb: int = 0

    # Metadata
    version_command: str = None

    def __post_init__(self):
        """Initialize default empty lists"""
        if self.compiler_args is None:
            self.compiler_args = []
        if self.runtime_args is None:
            self.runtime_args = []


# ============================================
# HELPER FUNCTIONS FOR ENV VARIABLES
# ============================================

def get_env(key: str, default: str) -> str:
    """Get environment variable with default"""
    return os.getenv(key, default)


def get_env_int(key: str, default: int) -> int:
    """Get integer environment variable with default"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    """Get float environment variable with default"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


# ============================================
# LANGUAGE CONFIGURATIONS
# ============================================

PYTHON_CONFIG = LanguageConfig(
    name="Python 3.10",
    language_id=Language.PYTHON,
    extension=".py",

    # No compilation needed
    needs_compilation=False,

    # Runtime: Python interpreter (from env)
    runtime=get_env("PYTHON_BINARY", "/usr/bin/python3.10"),
    runtime_args=["solution.py"],

    # Resource multipliers (from env)
    time_multiplier=get_env_float("TIME_MULTIPLIER_PYTHON", 3.0),
    memory_grace_kb=get_env_int("MEMORY_GRACE_PYTHON_KB", 768),

    # Version check
    version_command="python3 --version"
)

CPP_CONFIG = LanguageConfig(
    name="C++17 (g++)",
    language_id=Language.CPP,
    extension=".cpp",

    # Compilation with g++ (from env)
    needs_compilation=True,
    compiler=get_env("CPP_COMPILER", "/usr/bin/g++"),
    compiler_args=[
        "-std=c++17",           # C++17 standard
        "-O2",                  # Optimization level 2
        "-Wall",                # All warnings
        "-Wextra",              # Extra warnings
        "-o", "solution",       # Output binary
        "solution.cpp"          # Source file
    ],
    compile_time_limit=get_env_int("CPP_COMPILE_TIMEOUT", 30),
    compile_memory_limit=get_env_int("CPP_COMPILE_MEMORY_MB", 1024),

    # Runtime: Execute binary directly
    runtime="./solution",
    runtime_args=[],

    # Resource multipliers (from env)
    time_multiplier=get_env_float("TIME_MULTIPLIER_CPP", 1.0),
    memory_grace_kb=get_env_int("MEMORY_GRACE_CPP_KB", 64),

    # Version check
    version_command="g++ --version"
)

RUST_CONFIG = LanguageConfig(
    name="Rust 2021",
    language_id=Language.RUST,
    extension=".rs",

    # Compilation with rustc (from env)
    # Use real rustc binary, not rustup wrapper
    needs_compilation=True,
    compiler=get_env("RUST_COMPILER", "/usr/local/rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin/rustc"),
    compiler_args=[
        "-O",                   # Optimize
        "--edition", "2021",    # Rust 2021 edition
        "-C", "linker=/usr/bin/x86_64-linux-gnu-gcc-12",  # Specify linker explicitly
        "-C", "opt-level=2",    # Optimization level
        "-o", "solution",       # Output binary
        "solution.rs"           # Source file
    ],
    compile_time_limit=get_env_int("RUST_COMPILE_TIMEOUT", 60),
    compile_memory_limit=get_env_int("RUST_COMPILE_MEMORY_MB", 4096),  # Increased for rustc

    # Runtime: Execute binary directly
    runtime="./solution",
    runtime_args=[],

    # Resource multipliers (from env)
    time_multiplier=get_env_float("TIME_MULTIPLIER_RUST", 1.0),
    memory_grace_kb=get_env_int("MEMORY_GRACE_RUST_KB", 128),

    # Version check
    version_command="rustc --version"
)

JAVASCRIPT_CONFIG = LanguageConfig(
    name="JavaScript (Node.js)",
    language_id=Language.JAVASCRIPT,
    extension=".js",

    # No compilation needed
    needs_compilation=False,

    # Runtime: Node.js (from env)
    runtime=get_env("NODEJS_BINARY", "/usr/bin/node"),
    runtime_args=["solution.js"],
    max_processes=get_env_int("NODEJS_PROCESSES", 16),  # Node.js needs more threads

    # Resource multipliers (from env)
    time_multiplier=get_env_float("TIME_MULTIPLIER_JAVASCRIPT", 2.0),
    memory_grace_kb=get_env_int("MEMORY_GRACE_JAVASCRIPT_KB", 8192),  # Node.js needs more memory

    # Version check
    version_command="node --version"
)

GO_CONFIG = LanguageConfig(
    name="Go 1.20+",
    language_id=Language.GO,
    extension=".go",

    # Compilation with go build (from env)
    needs_compilation=True,
    compiler=get_env("GO_COMPILER", "/usr/bin/go"),
    compiler_args=[
        "build",
        "-o", "solution",       # Output binary
        "solution.go"           # Source file
    ],
    compile_time_limit=get_env_int("GO_COMPILE_TIMEOUT", 30),
    compile_memory_limit=get_env_int("GO_COMPILE_MEMORY_MB", 2048),  # Increased for go build

    # Runtime: Execute binary directly
    runtime="./solution",
    runtime_args=[],
    max_processes=16,  # Go runtime needs multiple threads for goroutines

    # Resource multipliers (from env)
    time_multiplier=get_env_float("TIME_MULTIPLIER_GO", 1.5),
    memory_grace_kb=get_env_int("MEMORY_GRACE_GO_KB", 8192),  # Go runtime needs more memory

    # Version check
    version_command="go version"
)


# ============================================
# LANGUAGE REGISTRY
# ============================================

# Map language enum to configuration
LANGUAGE_CONFIGS = {
    Language.PYTHON: PYTHON_CONFIG,
    Language.CPP: CPP_CONFIG,
    Language.RUST: RUST_CONFIG,
    Language.JAVASCRIPT: JAVASCRIPT_CONFIG,
    Language.GO: GO_CONFIG,
}

# Map file extension to language
EXTENSION_TO_LANGUAGE = {
    ".py": Language.PYTHON,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".rs": Language.RUST,
    ".js": Language.JAVASCRIPT,
    ".go": Language.GO,
}

# Map string identifier to language (for API)
STRING_TO_LANGUAGE = {
    "python": Language.PYTHON,
    "python3": Language.PYTHON,
    "py": Language.PYTHON,

    "cpp": Language.CPP,
    "c++": Language.CPP,
    "cpp17": Language.CPP,

    "rust": Language.RUST,
    "rs": Language.RUST,

    "javascript": Language.JAVASCRIPT,
    "js": Language.JAVASCRIPT,
    "node": Language.JAVASCRIPT,
    "nodejs": Language.JAVASCRIPT,

    "go": Language.GO,
    "golang": Language.GO,
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_language_config(language: Language) -> LanguageConfig:
    """
    Get configuration for a language

    Args:
        language: Language enum value

    Returns:
        LanguageConfig for the language

    Raises:
        ValueError: If language not supported
    """
    if language not in LANGUAGE_CONFIGS:
        raise ValueError(f"Unsupported language: {language}")
    return LANGUAGE_CONFIGS[language]


def get_language_from_string(language_str: str) -> Language:
    """
    Convert string to Language enum

    Args:
        language_str: Language identifier (e.g., "python", "cpp", "rust")

    Returns:
        Language enum value

    Raises:
        ValueError: If language string not recognized

    Examples:
        >>> get_language_from_string("python")
        Language.PYTHON
        >>> get_language_from_string("c++")
        Language.CPP
    """
    language_str = language_str.lower().strip()
    if language_str not in STRING_TO_LANGUAGE:
        raise ValueError(
            f"Unknown language: {language_str}. "
            f"Supported: {', '.join(STRING_TO_LANGUAGE.keys())}"
        )
    return STRING_TO_LANGUAGE[language_str]


def get_language_from_extension(extension: str) -> Language:
    """
    Detect language from file extension

    Args:
        extension: File extension (e.g., ".py", ".cpp")

    Returns:
        Language enum value

    Raises:
        ValueError: If extension not recognized

    Examples:
        >>> get_language_from_extension(".py")
        Language.PYTHON
        >>> get_language_from_extension(".cpp")
        Language.CPP
    """
    extension = extension.lower().strip()
    if extension not in EXTENSION_TO_LANGUAGE:
        raise ValueError(
            f"Unknown file extension: {extension}. "
            f"Supported: {', '.join(EXTENSION_TO_LANGUAGE.keys())}"
        )
    return EXTENSION_TO_LANGUAGE[extension]


def get_all_languages() -> List[Language]:
    """
    Get list of all supported languages

    Returns:
        List of Language enum values
    """
    return list(LANGUAGE_CONFIGS.keys())


def get_language_display_name(language: Language) -> str:
    """
    Get display name for a language

    Args:
        language: Language enum value

    Returns:
        Display name (e.g., "Python 3.10", "C++17 (g++)")
    """
    config = get_language_config(language)
    return config.name


def calculate_actual_limits(
    base_time_limit: int,
    base_memory_limit: int,
    language: Language
) -> tuple[int, int]:
    """
    Calculate actual resource limits for a language

    Applies language-specific multipliers and grace periods.

    Args:
        base_time_limit: Base time limit in seconds (from problem)
        base_memory_limit: Base memory limit in MB (from problem)
        language: Language enum value

    Returns:
        Tuple of (actual_time_limit_seconds, actual_memory_limit_kb)

    Examples:
        >>> calculate_actual_limits(2, 256, Language.PYTHON)
        (6, 262912)  # 2s * 3.0 = 6s, 256MB + 768KB

        >>> calculate_actual_limits(2, 256, Language.CPP)
        (2, 262208)  # 2s * 1.0 = 2s, 256MB + 64KB
    """
    config = get_language_config(language)

    # Apply time multiplier
    actual_time = int(base_time_limit * config.time_multiplier)

    # Apply memory grace (convert MB to KB first)
    base_memory_kb = base_memory_limit * 1024
    actual_memory_kb = base_memory_kb + config.memory_grace_kb

    return (actual_time, actual_memory_kb)


# ============================================
# VALIDATION
# ============================================

def validate_source_code(source_code: str, language: Language) -> None:
    """
    Validate source code for a language

    Basic validation to catch obvious errors before judging.

    Args:
        source_code: Source code string
        language: Language enum value

    Raises:
        ValueError: If source code is invalid
    """
    # Check size limits (50KB max)
    if len(source_code.encode('utf-8')) > 51200:
        raise ValueError("Source code exceeds 50KB limit")

    # Check not empty
    if not source_code.strip():
        raise ValueError("Source code is empty")

    # Language-specific validation
    config = get_language_config(language)

    # Python: Check for syntax errors (basic)
    if language == Language.PYTHON:
        # Just check it's not completely empty
        if not any(line.strip() for line in source_code.splitlines()):
            raise ValueError("Python code has no statements")

    # C++: Check for main function
    if language == Language.CPP:
        if "int main" not in source_code and "main(" not in source_code:
            raise ValueError("C++ code must have a main() function")

    # Rust: Check for main function
    if language == Language.RUST:
        if "fn main" not in source_code:
            raise ValueError("Rust code must have a main() function")

    # Go: Check for main package and function
    if language == Language.GO:
        if "package main" not in source_code:
            raise ValueError("Go code must be in package main")
        if "func main" not in source_code:
            raise ValueError("Go code must have a main() function")


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    """
    Test language configuration

    Usage:
        python -m app.judge.language_config
    """
    print("=" * 70)
    print("LANGUAGE CONFIGURATION TEST")
    print("=" * 70)

    # Test 1: List all languages
    print("\n[Test 1: All Supported Languages]")
    for lang in get_all_languages():
        config = get_language_config(lang)
        print(f"  - {config.name} ({lang.value})")
        print(f"    Extension: {config.extension}")
        print(f"    Compiled: {config.needs_compilation}")
        print(f"    Time multiplier: {config.time_multiplier}x")
        print(f"    Memory grace: {config.memory_grace_kb}KB")
        print()

    # Test 2: String to language conversion
    print("[Test 2: String to Language Conversion]")
    test_strings = ["python", "cpp", "c++", "rust", "javascript", "node", "go"]
    for s in test_strings:
        try:
            lang = get_language_from_string(s)
            print(f"  '{s}' → {lang.value} ✅")
        except ValueError as e:
            print(f"  '{s}' → ERROR: {e} ❌")

    # Test 3: Extension to language
    print("\n[Test 3: Extension to Language]")
    test_extensions = [".py", ".cpp", ".rs", ".js", ".go"]
    for ext in test_extensions:
        try:
            lang = get_language_from_extension(ext)
            print(f"  '{ext}' → {lang.value} ✅")
        except ValueError as e:
            print(f"  '{ext}' → ERROR: {e} ❌")

    # Test 4: Calculate actual limits
    print("\n[Test 4: Calculate Actual Limits]")
    base_time = 2  # 2 seconds
    base_memory = 256  # 256 MB

    for lang in get_all_languages():
        actual_time, actual_memory_kb = calculate_actual_limits(
            base_time, base_memory, lang
        )
        actual_memory_mb = actual_memory_kb / 1024

        print(f"  {lang.value}:")
        print(f"    Base: {base_time}s, {base_memory}MB")
        print(f"    Actual: {actual_time}s, {actual_memory_mb:.2f}MB")

    # Test 5: Validation
    print("\n[Test 5: Source Code Validation]")
    test_cases = [
        (Language.PYTHON, "print('hello')", True),
        (Language.PYTHON, "", False),
        (Language.CPP, "int main() { return 0; }", True),
        (Language.CPP, "void foo() {}", False),
        (Language.RUST, "fn main() {}", True),
        (Language.RUST, "fn foo() {}", False),
        (Language.GO, "package main\nfunc main() {}", True),
        (Language.GO, "package foo\nfunc main() {}", False),
    ]

    for lang, code, should_pass in test_cases:
        try:
            validate_source_code(code, lang)
            if should_pass:
                print(f"  {lang.value}: PASS ✅")
            else:
                print(f"  {lang.value}: UNEXPECTED PASS ⚠️")
        except ValueError as e:
            if not should_pass:
                print(f"  {lang.value}: FAIL (expected) ✅")
            else:
                print(f"  {lang.value}: UNEXPECTED FAIL: {e} ❌")

    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)
