init:
	poetry install

run:
	poetry run python main.py

format:
	poetry run black *.py

export:
	poetry export -f requirements.txt > requirements.txt

deploy:
	export
	git push heroku master
