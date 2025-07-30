# Boxd Out

## Commands

`uv sync`
- update dependencies

`uv add X / uv add --dev X`
- add X to dependencies (dev or not)

`uv run django-admin startproject boxd-out .`
- create django project

`uv run manage.py runserver`
- run development server

## DB updates

`uv run manage.py makemigrations`
- create a new migration file (kinda like git commit)

`uv run manage.py migrate`
- apply migrations to remote db (kinda like git push)

`uv run manage.py generate_token --username myusername --secret-word mysecret`
- generate a new token

