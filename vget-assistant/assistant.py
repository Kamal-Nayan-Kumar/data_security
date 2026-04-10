#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog

def get_response(query: str) -> str:
    query = query.lower()
    if "login" in query:
        return "[cyan]vget login[/cyan] [green]authenticates you with the remote vget server using your standard user credentials.[/green]"
    elif "register" in query and "dev" not in query:
        return "[cyan]vget register[/cyan] [green]creates a new standard user account to download packages.[/green]"
    elif "dev-register" in query or ("dev" in query and "register" in query):
        return "[cyan]vget dev-register[/cyan] [green]registers you as a Developer and links your local Ed25519 public key to your identity for signing packages.[/green]"
    elif "publish" in query:
        return "[cyan]vget publish --path <folder> --version <ver>[/cyan] [green]compresses a directory, hashes it, signs it with your private key, and uploads it to the live backend for ML scanning.[/green]"
    elif "install" in query:
        return "[cyan]vget install <pkg_name>[/cyan] [green]downloads the package, verifies the cryptographic signature against the developer's public key, and extracts it to ./installed/[/green]"
    elif "update" in query:
        return "[cyan]vget update <pkg_name>[/cyan] [green]checks for the latest version and upgrades your local installation securely.[/green]"
    elif "help" in query:
        return "[yellow]I am the vget AI Assistant! I can help you understand commands like: login, register, dev-register, publish, install, and update. Just ask![/yellow]"
    else:
        return "[red]I'm not sure how to answer that. Try asking about a specific vget command like 'publish' or 'install'.[/red]"

class VgetAssistant(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    RichLog {
        height: 1fr;
        border: solid green;
    }
    Input {
        dock: bottom;
        border: solid cyan;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        self.chat_log = RichLog(highlight=True, markup=True)
        yield self.chat_log
        yield Input(placeholder="Ask vget-assistant a question...")
        yield Footer()

    def on_mount(self) -> None:
        self.chat_log.write("[bold cyan]Welcome to vget AI Assistant![/bold cyan]")
        self.chat_log.write("[green]Type 'help' to see what I know, or 'exit'/'quit' to shut down.[/green]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        if not user_input:
            return
        
        self.chat_log.write(f"[bold magenta]You:[/bold magenta] {user_input}")
        event.input.value = ""

        if user_input.lower() in ("exit", "quit"):
            self.exit()
            return

        self.chat_log.write("[yellow]Thinking...[/yellow]")
        response = get_response(user_input)
        self.chat_log.write(f"[bold cyan]Assistant:[/bold cyan] {response}")
        self.chat_log.write("")

if __name__ == "__main__":
    app = VgetAssistant()
    app.run()
