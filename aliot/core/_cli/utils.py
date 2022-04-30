from rich.console import Console
from rich.style import Style

console = Console()


def print_success(op_name: str = "", success_name: str = "Success"):
    console.print(f"[{success_name} \\(°ω°\\)] {op_name}", style=Style(color="green"))


def print_err(op_name: str = "", error_name: str = "Error"):
    console.print(f"[{error_name} (・_・ ?)] {op_name}", style=Style(color="red"), )


def print_fail(op_name: str = "", failure_name: str = "Failure"):
    console.print(f"[{failure_name} (’-_-)] {op_name}", style=Style(color="orange1"))


def print_warning(op_name: str = "", warning_name: str = "Warning"):
    console.print(f"[{warning_name} (ㆆ_ㆆ)] {op_name}", style=Style(color="yellow"))


def print_info(op_name: str = "", info_name: str = "Info"):
    console.print(f"[{info_name} (^ ▽ ^)] {op_name}", style=Style(color="cyan"))


def print_log(msg: str, color: str):
    console.print(msg, style=Style(color=color))
