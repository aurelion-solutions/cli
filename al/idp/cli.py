import typer

app = typer.Typer()

auth = typer.Typer()

app.add_typer(auth, name="auth")


@auth.command("login")
def login():
    print("IDP login")
