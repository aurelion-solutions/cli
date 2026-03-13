import typer

app = typer.Typer()

applications = typer.Typer()

app.add_typer(applications, name="applications")


@applications.command("list")
def list_applications():
    print("IGA applications")
