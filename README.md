# Matcher

A simple matchmaking Flask application. It asks a series of questions and suggests a best match based on the answers.

## Deploying with Docker

To build and run the application using Docker, run the following command:

```bash
docker-compose up
```

The application will be available at [http://localhost:5000](http://localhost:5000).

## Development

The provided `docker-compose.yml` is configured for development with live reloading. Any changes made to the `app` directory or `data.json` on your host machine will be reflected in the running container.

To run the application locally without Docker, follow these steps:

1.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the Flask application:
    ```bash
    export FLASK_APP=app/main.py
    export FLASK_ENV=development
    export ADMIN_PASSWORD=changeme
    flask run
    ```

## Testing

There are currently no automated tests for this application. To add tests, you can use a testing framework like `pytest`.

1.  Install pytest:
    ```bash
    pip install pytest
    ```

2.  Create a `tests` directory and add your test files (e.g., `tests/test_app.py`).
