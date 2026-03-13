# Aurelion CLI

Aurelion CLI (`al`) is the command line interface for interacting with Aurelion platform services.

It provides a unified interface for multiple platform products such as:

- IGA (Identity Governance & Administration)
- IDP (Identity Provider)
- Future modules such as DCAP, SWG, XDR

The CLI acts as a thin client that communicates with Aurelion backend services over HTTP APIs.

---

# Installation

The project requires Python 3.12+.

Install dependencies:

pip install -e .

or with uv:

uv sync

After installation the CLI command becomes available as:

al

---

# Basic Usage

The CLI is structured by product and domain.

General command format:

al <product> <domain> <action>

Examples:

al iga applications list  
al idp auth login  
al app create --name <name> --connector-type <type> [--config <json>]  
al app delete --app-id <uuid>  
al app reconcile run --app-id <uuid>

---

# Command Structure

Example hierarchy:

al  
├── app  
│   ├── create  
│   ├── delete  
│   └── reconcile  
│       └── run  
├── secrets  
│   ├── list  
│   ├── create  
│   ├── get  
│   ├── delete  
│   └── provider  
│       ├── list  
│       ├── create  
│       ├── get  
│       └── delete  
├── iga  
│   └── applications  
│       └── list  
└── idp  
    └── auth  
        └── login  

Each product provides its own command tree.

---

# Architecture

The CLI is built using Typer.

Key principles:

- Thin client — all business logic lives in backend services  
- Plugin architecture — products register their own CLI modules  
- Communication with backend via HTTP APIs  
- Modular command structure

High-level architecture:

CLI (Typer)  
→ API client  
→ Aurelion backend services

---

# Project Structure

Typical project layout:

aurelion-cli/  
├── al/  
│   ├── main.py  
│   ├── client.py  
│   ├── plugins.py  
│   ├── app/  
│   │   └── cli.py  
│   ├── iga/  
│   │   └── cli.py  
│   └── idp/  
│       └── cli.py  
├── pyproject.toml  
└── README.md  

`main.py` loads and registers CLI plugins.

Each product exposes its own Typer application.

---

# Adding a New Product

To add a new product CLI module:

1. Create a directory inside `al/`.

Example:

al/dcap/

2. Create `cli.py` inside it.

3. Expose a Typer application named `app`.

Example:

import typer

app = typer.Typer()

@app.command()
def example():
    print("dcap command")

The plugin loader will automatically register the module.

The command will become available as:

al dcap example

---

# Development

Run CLI locally:

python -m al.main

Example:

python -m al.main iga applications list

---

# Planned Features

- authentication configuration
- environment switching
- CLI profiles
- richer terminal output (tables, progress)
- streaming operations
- administrative platform commands

---

# License

Apache License 2.0 — see `LICENSE`.
