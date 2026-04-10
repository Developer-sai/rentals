"""
logger.py
Shared colored terminal logger for all backend components.

Colors:
  CYAN    → incoming requests / pipeline start
  BLUE    → agent processing steps
  GREEN   → success / completion
  YELLOW  → warnings / skipped steps
  MAGENTA → LLM calls (Groq / Tavily)
  RED     → errors
  WHITE   → general info
"""
from datetime import datetime

# ANSI color codes
CYAN    = "\033[96m"
BLUE    = "\033[94m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
WHITE   = "\033[97m"
DIM     = "\033[2m"
BOLD    = "\033[1m"
RESET   = "\033[0m"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log(tag: str, message: str, color: str = WHITE):
    print(f"{DIM}[{_ts()}]{RESET} {color}{BOLD}[{tag:^12}]{RESET} {message}")


def log_info(tag: str, message: str):
    log(tag, message, WHITE)

def log_start(tag: str, message: str):
    log(tag, message, CYAN)

def log_step(tag: str, message: str):
    log(tag, message, BLUE)

def log_ok(tag: str, message: str):
    log(tag, f"{GREEN}✓{RESET} {message}", GREEN)

def log_warn(tag: str, message: str):
    log(tag, f"{YELLOW}⚠ {message}{RESET}", YELLOW)

def log_llm(tag: str, message: str):
    log(tag, f"{MAGENTA}⚡ {message}{RESET}", MAGENTA)

def log_err(tag: str, message: str):
    log(tag, f"{RED}✗ {message}{RESET}", RED)

def log_sep():
    print(f"{DIM}{'─' * 72}{RESET}")
