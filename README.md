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

```bash
uv run --with pytest pytest -q
```

## Group assignment

See `doc/sorting-logic.md`.
Every project runs with a size between the page's minimum and maximum.
Closing fails, and the page stays open, if the headcount does not fit.
"Close voting with equal groups" skips the stored sizes.
It sets them to the headcount divided by the number of projects, rounded down and up.
Groups then differ by at most one person.
