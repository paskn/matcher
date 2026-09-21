# Deploying Matchmaker with Dockge

This guide will walk you through the correct way to deploy the Matchmaker application on your server using Dockge.

## Prerequisites

Before you begin, ensure you have the following installed on your server:

*   **Docker**: [Installation guide](https://docs.docker.com/engine/install/)
*   **Dockge**: [Installation guide](https://dockge.kuma.pet/)

## 1. Clone the Repository into Your Stacks Directory

Dockge works by scanning a directory on your server for stacks (which are defined by `docker-compose.yml` files). The default directory is `/opt/stacks`.

First, you need to clone your Git repository into a new subdirectory inside your Dockge stacks directory.

1.  Open a terminal on your server.
2.  Navigate to your Dockge stacks directory. If you used the default installation, this will be `/opt/stacks`.

    ```bash
    cd /opt/stacks
    ```

3.  Clone your repository into a new directory. The name of this directory will be the name of your stack in Dockge.

    ```bash
    git clone <repository_url> matchmaker
    ```

    Replace `<repository_url>` with the actual URL of your Git repository.

## 2. Scan for the New Stack in Dockge

Now that the files are on your server, you need to tell Dockge to scan for the new stack.

1.  Open your Dockge dashboard (e.g., `http://<your_server_ip>:5001`).
2.  From the main dashboard, click the **Scan Stacks Folder** button.

Dockge will find the `matchmaker` directory you just created and add it as a new stack.

## 3. Start the Stack

1.  The new `matchmaker` stack will now appear in your list of stacks.
2.  Click on the `matchmaker` stack.
3.  You will see the content of your `docker-compose.yml` file.
4.  Click the **Up** button to start the application.

Dockge will now build the Docker image and start the service as defined in your `docker-compose.yml` file.

## 4. Set the Administrator Password

The administrator password is set as an environment variable. You can edit this directly in Dockge.

1.  In your `matchmaker` stack in Dockge, you will see the content of your `docker-compose.yml` file.
2.  Find the `ADMIN_PASSWORD` environment variable and change its value from `changeme` to a strong, secure password.

```yaml
    environment:
      - FLASK_APP=app/main.py
      - FLASK_ENV=production
      - ADMIN_PASSWORD=your_super_secret_password # <-- Change this!
```

3.  Click the **Save** button, and then click **Up** again to restart the stack with the new password.

## 5. Access Your Application

Once deployed and started, you can access the Matchmaker application at `http://<your_server_ip>:5000`.

## Updating the Application

To update the application with the latest changes from your Git repository:

1.  Open a terminal on your server and navigate to the `matchmaker` stack directory.

    ```bash
    cd /opt/stacks/matchmaker
    ```

2.  Pull the latest changes from the repository:

    ```bash
    git pull
    ```

3.  In the Dockge UI, go to your `matchmaker` stack.
4.  Click the **Update** or **Recreate** button to make Dockge rebuild the image with the latest code and restart the service.