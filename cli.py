import click
import sys
import ollama
from agent_interface import GraphRAGAgent
from memory import save_chat_turn, get_chat_history, get_current_repo_name

def print_cli_history():
    """Reads the active JSON repo history file and prints it to the console."""
    repo_name = get_current_repo_name()
    history = get_chat_history()
    if not history:
        click.echo(f"\n[INFO] No recorded chat history found for repository: '{repo_name}'")
        return
        
    click.echo(f"\n📜 --- CHAT HISTORY LOGS FOR REPO: {repo_name.upper()} ---")
    click.echo("─" * 60)
    for turn in history:
        click.echo(f"[{turn['timestamp']}] ({turn['interface']})")
        click.echo(f"👤 User: {turn['user']}")
        click.echo(click.style(f"🤖 AI:   {turn['assistant']}", fg=(0, 255, 70)))
        click.echo("─" * 60)

@click.command()
@click.option('--db', default='./pnsv_vector_db', help='Path to vector database')
@click.option('--model', default='llama3', help='Ollama model to use')
@click.option('--limit', default=5, help='Number of context chunks to retrieve')
@click.option('--verbose', is_flag=True, help='Show retrieved context blocks')
@click.option('--chistory', is_flag=True, help='Show chat history for the active repo')
def main(db, model, limit, verbose, chistory):
    """Agent-PNSV — AST-driven GraphRAG code intelligence shell.

    Interactive shell for querying indexed codebases using structural
    code understanding. Requires Ollama running locally.

    \b
    Commands:
      exit, quit, q    Exit the shell
      Ctrl+C           Interrupt and exit
    """
    if chistory:
        print_cli_history()
        sys.exit(0)

    active_repo = get_current_repo_name()
    click.echo(f"agent-pnsv v0.1.0  |  db: {db}  |  model: {model}  |  active_repo: {active_repo}")
    click.echo("─" * 60)

    try:
        agent = GraphRAGAgent(db_path=db)
    except Exception as e:
        click.echo(f"error: failed to initialize agent — {e}", err=True)
        sys.exit(1)

    click.echo("ready.\n")

    while True:
        try:
            query = click.prompt("pnsv", prompt_suffix=" > ")
        except (KeyboardInterrupt, EOFError):
            click.echo("\nexiting.")
            sys.exit(0)

        query = query.strip()

        if not query:
            continue

        if query.lower() in ('exit', 'quit', 'q'):
            click.echo("exiting.")
            sys.exit(0)

        # retrieve context
        try:
            results, context = agent.retrieve_context(query, limit=limit)
        except Exception as e:
            click.echo(f"error: retrieval failed — {e}", err=True)
            continue

        if results is None:
            click.echo("no matching context found in indexed codebase.")
            continue

        # show context blocks if verbose
        if verbose:
            click.echo("\n── retrieved context ─────────────────────────────────")
            click.echo(context)
            click.echo("──────────────────────────────────────────────────────\n")

        # build prompt
        _, full_prompt = agent.generate_prompt(query)

        # run inference
        try:
            stream = ollama.generate(model=model, prompt=full_prompt, stream=True)

            click.echo()  # newline before response
            response_text = ""
            for chunk in stream:
                chunk_text = chunk['response']
                response_text += chunk_text
                click.echo(
                    click.style(chunk_text, fg=(0, 255, 70)),
                    nl=False
                )
            click.echo("\n")
            
            # Save interaction history linked to active repo identity
            save_chat_turn("CLI", query, response_text)

        except Exception as e:
            if "connect" in str(e).lower():
                click.echo("error: ollama is not running. start with: ollama serve", err=True)
            else:
                click.echo(f"error: inference failed — {e}", err=True)

if __name__ == "__main__":
    main()