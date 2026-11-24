# Flask + MySQL: Docker Networking Lab

A small two-tier application designed to practice Docker networking. The Flask web application runs in one container and MySQL runs in another. Both containers join a user-created Docker bridge network and communicate using the MySQL container name.




## What Happens When the Application Runs?

1. Docker creates a custom bridge network named `two-tier`.
2. A MySQL container starts with the container name `mysql`.
3. MySQL creates and uses the database named `devops`.
4. Docker builds the Flask image using the `Dockerfile`, naming it `two-tier-backend:latest`.
5. A Flask container starts with the name `flask-container`.
6. Both containers connect to the same custom bridge network, `two-tier`.
7. Flask uses `MYSQL_HOST=mysql` to locate the MySQL container through Docker's embedded DNS.
8. Flask connects to MySQL on its internal port `3306`.
9. You open the web application at `http://localhost:5000`.
10. When you submit a message, Flask inserts it into the MySQL `messages` table.
11. You can inspect the database, Docker network, container logs, and container connectivity.

## Important Docker Networking Concepts

| Concept | What You Learn |
|---|---|
| Bridge driver | Connects containers through a Docker bridge network |
| Custom bridge network | Provides isolated networking between containers |
| Container DNS | Allows containers to find each other using container names |
| Port publishing | Makes a container port accessible from the host |
| Internal port | Allows container-to-container communication without publishing the database port |
| Docker volume | Can persist MySQL data beyond the container lifecycle |
| Network inspection | Shows connected containers and their network IP addresses |

## Docker Network Configuration

This project uses a custom Docker bridge network named `two-tier`.

Inspect the network:

```bash
docker network inspect two-tier
```

The Flask and MySQL containers should both appear under the network's connected containers.

### Container Communication

The Flask application connects to MySQL using:

```bash
MYSQL_HOST=mysql
MYSQL_PORT=3306
```

Here, `mysql` is the MySQL container name.

Docker's embedded DNS resolves this container name to its IP address because both containers are connected to the same user-defined bridge network.

**Important:** The MySQL port `3306` does not need to be published to the host for Flask to communicate with MySQL.

## Expected Final Result

After completing the project, you should have:

- One custom Docker bridge network: `two-tier`.
- One Flask container: `flask-container`.
- One MySQL container: `mysql`.
- One Flask Docker image: `two-tier-backend:latest`.
- One MySQL database: `devops`.
- One MySQL table: `messages`.
- A working Flask application accessible at `http://localhost:5000`.
- Successful container-to-container communication using Docker's embedded DNS.

## Verify the Application

### Check Running Containers

```bash
docker ps
```

### Check the Docker Network

```bash
docker network inspect two-tier
```

### Check Flask Logs

```bash
docker logs flask-container
```

### Access the MySQL Container

```bash
docker exec -it mysql bash
```

Log in to MySQL:

```bash
mysql -u root -p
```

Inspect the database:

```sql
SHOW DATABASES;

USE devops;

SHOW TABLES;

SELECT * FROM messages;
```

Note: This is a custom network using Docker's built-in `bridge` driver. You are creating a network, not implementing a new network-driver plugin.

##  Start the MySQL container

```bash
docker run -d \
  --name mysql-container \
  --network app-network \
  --network-alias mysql-db \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=flask_messages \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=app_password \
  -v mysql-data:/var/lib/mysql \
  mysql:8.4
```

Check its status and logs:

```bash
docker ps
docker logs -f mysql-container
```

Wait until the logs indicate that MySQL is ready for connections. You can also check readiness with:

```bash
docker exec mysql-container \
  mysqladmin ping -h 127.0.0.1 -u root -proot_password
```

The `mysql-data` named volume keeps database files when the container is removed and recreated.


##  Run the Flask container

```bash
docker run -d \
  --name flask-container \
  --network two-tier \
  -p 5000:5000 \
  -e MYSQL_HOST=mysql \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=app_password \
  -e MYSQL_DB=flask_messages \
  flask-network-lab:1.0
```

Important:

- `--network two-tier` connects Flask to the same network as MySQL.
- `-p 5000:5000` publishes Flask's port to your host.
- `MYSQL_HOST=mysql` uses the MySQL container name as its hostname.
- Port `3306` is reachable between containers on the shared network. You do not need `-p 3306:3306` on MySQL.

## 9. Step 5 — Test the application

Open this address in your browser:

```text
http://localhost:5000
```

Submit a message. It should appear in the list after Flask saves it to MySQL.

Test the Flask health endpoint:

```bash
curl http://localhost:5000/health
```

View logs:

```bash
docker logs flask-container
docker logs mysql-container
```



## Key Takeaway

**Containers do not need to expose their ports to the host to communicate with each other.**

When containers share a user-defined Docker bridge network, they can communicate using container names through Docker's embedded DNS.

In this project, the Flask container communicates with the MySQL container using `mysql` as the hostname and `3306` as the internal database port.

This demonstrates the fundamentals of Docker networking and how a two-tier application communicates across separate containers.

## Future Improvement: Persistent MySQL Storage

A named Docker volume can be added to persist MySQL database files even if the MySQL container is removed and recreated.

For example:

```bash
docker volume create mysql-data
```

When creating a new MySQL container, mount the volume:

```bash
-v mysql-data:/var/lib/mysql
```

This is a recommended improvement for the project. The current setup should not be described as using this volume unless you actually create and attach it.
