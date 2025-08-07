"""
Centralized logging system for WhisperTux using rich for beautiful CLI output
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Confirm
from rich import box
import sys
from typing import Optional


class WhisperLogger:
    """Centralized logger with rich formatting for consistent CLI output"""
    
    def __init__(self):
        self.console = Console()
        self.error_console = Console(stderr=True)
        
    def info(self, message: str, prefix: str = "INFO"):
        """Log info message with blue styling"""
        text = Text()
        text.append(f"[{prefix}] ", style="bold blue")
        text.append(message)
        self.console.print(text)
    
    def success(self, message: str, prefix: str = "SUCCESS"):
        """Log success message with green styling"""
        text = Text()
        text.append("SUCCESS: ", style="bold green")
        text.append(f"[{prefix}] ", style="bold green")
        text.append(message)
        self.console.print(text)
    
    def warning(self, message: str, prefix: str = "WARNING"):
        """Log warning message with yellow styling"""
        text = Text()
        text.append("WARNING: ", style="bold yellow")
        text.append(f"[{prefix}] ", style="bold yellow")
        text.append(message)
        self.console.print(text)
    
    def error(self, message: str, prefix: str = "ERROR"):
        """Log error message with red styling"""
        text = Text()
        text.append("ERROR: ", style="bold red")
        text.append(f"[{prefix}] ", style="bold red")
        text.append(message)
        self.error_console.print(text)
    
    def step(self, message: str, prefix: str = "STEP"):
        """Log step message with arrow styling"""
        text = Text()
        text.append("→ ", style="bold cyan")
        text.append(f"[{prefix}] ", style="bold cyan")
        text.append(message)
        self.console.print(text)
    
    def debug(self, message: str, prefix: str = "DEBUG"):
        """Log debug message with dim styling"""
        text = Text()
        text.append(f"[{prefix}] ", style="dim")
        text.append(message, style="dim")
        self.console.print(text)
    
    def header(self, title: str, subtitle: Optional[str] = None):
        """Print a formatted header"""
        if subtitle:
            panel_content = f"[bold]{title}[/bold]\n{subtitle}"
        else:
            panel_content = f"[bold]{title}[/bold]"
            
        panel = Panel(
            panel_content,
            box=box.ROUNDED,
            style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def section(self, title: str):
        """Print a section divider"""
        self.console.print(f"\n[bold blue]═══ {title} ═══[/bold blue]")
    
    def table(self, title: str, headers: list, rows: list):
        """Print a formatted table"""
        table = Table(title=title, box=box.SIMPLE_HEAVY)
        
        for header in headers:
            table.add_column(header, style="cyan")
        
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table)
    
    def progress_context(self, description: str = "Processing..."):
        """Context manager for progress spinner"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        )
    
    def ask_confirmation(self, question: str, default: bool = False) -> bool:
        """Ask user for confirmation"""
        return Confirm.ask(question, default=default, console=self.console)
    
    def rule(self, title: str = ""):
        """Print a horizontal rule"""
        self.console.rule(title, style="blue")


# Create global logger instance
logger = WhisperLogger()


# Convenience functions for easy importing
def log_info(message: str, prefix: str = "INFO"):
    logger.info(message, prefix)

def log_success(message: str, prefix: str = "SUCCESS"):
    logger.success(message, prefix)

def log_warning(message: str, prefix: str = "WARNING"):
    logger.warning(message, prefix)

def log_error(message: str, prefix: str = "ERROR"):
    logger.error(message, prefix)

def log_step(message: str, prefix: str = "STEP"):
    logger.step(message, prefix)

def log_debug(message: str, prefix: str = "DEBUG"):
    logger.debug(message, prefix)
