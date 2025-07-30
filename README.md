# Boxd Out

A Django REST Framework app to scrape movies from Letterboxd and save them to a PostgreSQL database.  
Initially built with Go in March 2025, I moved to Python to take advantage of the Django ecosystem as my new job role would use this stack. I previously wrote about it here [Rest API with Go](https://michaelsavage.ie/blog/rest-api-with-go).

## Commands

`uv sync`
- update dependencies

`uv add X / uv add --dev X`
- add X to dependencies (dev or not)

`uv run django-admin startproject boxd-out .`
- create django project

`uv run manage.py runserver`
- run development server

## Management commands 

`uv run manage.py generate_key`
- generate a new secret key

`uv run manage.py generate_token --username myusername --secret-word mysecret`
- generate a new token

## DB updates

`uv run manage.py makemigrations`
- create a new migration file (kinda like git commit)

`uv run manage.py migrate`
- apply migrations to remote db (kinda like git push)
