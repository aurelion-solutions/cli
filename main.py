import typer
from al.app.cli import app as app_app
from al.datalake.cli import app as datalake_app
from al.idp.cli import app as idp_app
from al.iga.cli import app as iga_app
from al.inventory.cli import app as inventory_app
from al.logs.cli import app as logs_app
from al.employee_records.cli import app as employee_records_app
from al.employees.cli import app as employees_app
from al.nhi.cli import app as nhi_app
from al.persons.cli import app as persons_app
from al.policy.cli import app as policy_app
from al.reconciliation.cli import app as reconciliation_app
from al.secrets.cli import app as secrets_app

app = typer.Typer()

app.add_typer(app_app, name="app")
app.add_typer(datalake_app, name="datalake")
app.add_typer(employee_records_app, name="employee-records")
app.add_typer(employees_app, name="employees")
app.add_typer(inventory_app, name="inventory")
app.add_typer(nhi_app, name="nhi")
app.add_typer(persons_app, name="persons")
app.add_typer(policy_app, name="policy")
app.add_typer(logs_app, name="logs")
app.add_typer(reconciliation_app, name="reconciliation")
app.add_typer(secrets_app, name="secrets")
app.add_typer(idp_app, name="idp")
app.add_typer(iga_app, name="iga")

if __name__ == "__main__":
    app()
