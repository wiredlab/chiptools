
run:
	FLASK_ENV=development FLASK_APP=chiptools.py flask run --host=0.0.0.0

bootstrap:
	virtualenv -p python3 venv
	pip install -r requirements.txt
