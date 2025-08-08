
import click
from main import run_analysis, run_manuscript_generation
from api import app
import uvicorn

@click.group()
def cli():
    """Blog Analyzer CLI"""
    pass

@cli.command()
def analyze():
    """Analyzes text files and saves the results to MongoDB."""
    click.echo("Starting analysis...")
    run_analysis()
    click.echo("Analysis finished and data saved to MongoDB.")

@cli.command()
@click.option('--keywords', required=True, help='Keywords for manuscript generation.')
@click.option('--user-instructions', default="", help='User instructions for manuscript generation.')
def generate(keywords, user_instructions):
    """Generates a manuscript based on the latest analysis data."""
    click.echo(f"Generating manuscript with keywords: {keywords}")
    # Note: This is a simplified version. In a real scenario, you'd fetch
    # the necessary data from MongoDB here, similar to how the API does.
    # For this example, we'll call a modified run_manuscript_generation.
    # You might need to adjust run_manuscript_generation to not require
    # all parameters passed directly if they can be fetched inside the function.
    
    # This is a placeholder for the actual logic to get data from MongoDB
    from mongodb_service import MongoDBService
    db_service = MongoDBService()
    analysis_data = db_service.get_latest_analysis_data()
    db_service.close_connection()

    if not analysis_data:
        click.echo("No analysis data found in MongoDB. Please run 'analyze' first.")
        return

    unique_words = analysis_data.get("unique_words", [])
    sentences = analysis_data.get("sentences", [])
    expressions = analysis_data.get("expressions", {})
    parameters = analysis_data.get("parameters", {})

    manuscript = run_manuscript_generation(
        unique_words=unique_words,
        sentences=sentences,
        expressions=expressions,
        parameters=parameters,
        user_instructions=user_instructions
    )
    click.echo("Generated Manuscript:")
    click.echo(manuscript)

@cli.command()
def serve():
    """Runs the FastAPI web server."""
    click.echo("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    cli()
