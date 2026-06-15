import click
import sys
import time
from agent_interface import GraphRAGAgent

PNSV_BANNER = """
\033[38;5;46m██████╗ ███╗   ██╗███████╗██╗   ██╗     \033[38;5;46m[ SYSTEM INITIALIZATION DETECTED ]
\033[38;5;46m██╔══██╗████╗  ██║██╔════╝██║   ██║     \033[38;5;10m===================================
\033[38;5;51m██████╔╝██╔██╗ ██║███████╗██║   ██║     \033[38;5;220mPNSV CORE ACTIVE // LINKING VECTORS
\033[38;5;51m██╔═══╝ ██║╚██╗██║╚════██║╚██╗ ██╔╝     \033[38;5;244m_..""````"".._
\033[38;5;198m██║     ██║ ╚████║███████║ ╚████╔╝    \033[38;5;242m.-'                  '-.
\033[38;5;198m╚═╝     ╚═╝  ╚═══╝╚══════╝  ╚═══╝     \033[38;5;201m  `""--.._____..--""`
"""

@click.command()
def main():
    """🤖 Agent PNSV: Continuous Interactive Code Assistant Shell."""
    # Print the custom neon cyberpunk banner layout
    print(PNSV_BANNER)
    click.echo(click.style("=== [⚡] WELCOME TO AGENT PNSV MATRIX DECK ===", fg="magenta", bold=True))
    click.echo(click.style("SYSTEM RUN LEVEL: ACCESS DEEP RETRIEVAL SHELL. TYPE 'exit' TO REBOOT VIRTUAL TERMINAL.\n", fg="green", dim=True))
    
    click.echo(click.style("⚙️  [CONNECTING] Sifting relational database vectors...", fg="yellow"))
    try:
        agent = GraphRAGAgent()
    except Exception as e:
        click.echo(click.style(f"\n[CRITICAL ERROR] Core terminal failure: {e}", fg="red", bold=True))
        return

    click.echo(click.style("🔑 [LINK ESTABLISHED] Storage clusters locked in memory memory.\n", fg="green", bold=True))

    while True:
        try:
            # Custom terminal loop indicator sequence
            query = click.prompt(click.style("┌───(cyber-root㉿pnsv-agent)-[~]\n└─$ ", fg="red", bold=True), prompt_suffix="")
        except (KeyboardInterrupt, EOFError):
            click.echo(click.style("\n\n[🛑] Disconnecting node safely. Goodbye operator.", fg="yellow"))
            sys.exit(0)
        
        query_clean = query.strip().lower()
        if query_clean in ['exit', 'quit', 'q']:
            click.echo(click.style("\n[🛑] Terminal core killed safely. Goodbye operator.\n", fg="yellow"))
            sys.exit(0)
            
        if not query.strip():
            continue
            
        click.echo(click.style("✨ [COMPUTING] Mapping syntax trees & context boundaries...", fg="magenta"))
        
        try:
            context, full_prompt = agent.generate_prompt(query)
            
            # Print the data boundary blocks
            print(click.style("\n📥 [EXTRACTED MATRIX BLOCK]", fg="cyan", bold=True))
            print(click.style("-" * 50, fg="cyan"))
            print(click.style(context, fg="white", dim=True))
            print(click.style("-" * 50, fg="cyan"))
            
            import ollama
            click.echo(click.style("🧠 [DEEP THINKING] Fetching token matrices from Llama3 core...", fg="yellow"))
            print(click.style("🤖 RESPONSE_STREAM >> ", fg="green", bold=True), end="", flush=True)
            
            # Real-time character streaming pipeline
            stream = ollama.generate(model='llama3', prompt=full_prompt, stream=True)
            for chunk in stream:
                print(click.style(chunk['response'], fg="green"), end="", flush=True)
            print("\n")
            
        except Exception as e:
            # Check if ollama connection specifically failed
            if "ConnectionRefusedError" in str(e) or "Failed to connect" in str(e):
                click.echo(click.style("\n⚠️  [DAEMON OFFLINE] Local Ollama backend core did not respond.", fg="red", bold=True))
            else:
                click.echo(click.style(f"\n❌ [EXECUTION FAULT] Pipeline exception triggered: {e}", fg="red"))

if __name__ == "__main__":
    main()