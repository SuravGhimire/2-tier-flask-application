# Flask + MySQL: Docker Networking Lab

A small two-tier application designed to practice Docker networking. The Flask web application runs in one container and MySQL runs in another. Both containers join a user-created Docker bridge network and communicate using the MySQL container name.

## 1. What we are building

```text
                 Your browser
             http://localhost:5000
                       |
                       | published port 5000
                       v
        +----------------------------------+
        |       Custom Docker network     |
        |          app-network            |
        |                                  |
        |  +----------------+              |
        |  | Flask container|              |
        |  | flask-container|              |
        |  | TCP :5000      |              |
        |  +-------+--------+              |
        |          |                       |
        |          | MySQL connection      |
        |          | mysql-container:3306  |
        |          v                       |
        |  +----------------+              |
        |  | MySQL container|              |
        |  | mysql-container|              |
        |  | TCP :3306      |              |
        |  +-------+--------+              |
        +----------|-----------------------+
                   |
                   v
            Docker volume
              mysql-data
```

The browser talks to Flask through the published host port. Flask talks to MySQL over the private Docker network. MySQL does not need a published host port for this application to work.

## 2. Project structure

```text
flask-mysql-docker-lab/
├── app.py
├── templates/
│   └── index.html
├── Dockerfile
├── requirements.txt
├── .dockerignore
└── README.md
```

## 3. What happens when the application runs?

1. Docker creates a custom bridge network named `app-network`.
2. Docker creates a named volume called `mysql-data` to persist database files.
3. A MySQL container starts on `app-network` with the name `mysql-container`.
4. A Flask image is built from the Dockerfile.
5. A Flask container starts on the same `app-network`.
6. Flask uses `MYSQL_HOST=mysql-container` to find MySQL through Docker's embedded DNS.
7. You open the web page, submit a message, and Flask inserts it into MySQL.
8. You can inspect the network and test connectivity from inside the containers.

## 4. Prerequisites

Install Docker Engine or Docker Desktop. Verify the installation:

```bash
docker --version
docker info
```

Run the following commands from the project root directory.

## 5. Step 1 — Create a custom Docker network

```bash
docker network create \
  --driver bridge \
  --subnet 172.25.0.0/16 \
  app-network
```

What these options mean:

- `docker network create`: creates a Docker network.
- `--driver bridge`: uses Docker's built-in bridge network driver.
- `--subnet`: assigns a custom IP address range.
- `app-network`: the network name.

Inspect it:

```bash
docker network ls
docker network inspect app-network
```

Note: This is a custom network using Docker's built-in `bridge` driver. You are creating a network, not implementing a new network-driver plugin.

## 6. Step 2 — Start the MySQL container

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

## 7. Step 3 — Build the Flask image

```bash
docker build -t flask-network-lab:1.0 .
```

Check the image:

```bash
docker images
```

## 8. Step 4 — Run the Flask container

```bash
docker run -d \
  --name flask-container \
  --network app-network \
  -p 5000:5000 \
  -e MYSQL_HOST=mysql-container \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=app_password \
  -e MYSQL_DB=flask_messages \
  flask-network-lab:1.0
```

Important:

- `--network app-network` connects Flask to the same network as MySQL.
- `-p 5000:5000` publishes Flask's port to your host.
- `MYSQL_HOST=mysql-container` uses the MySQL container name as its hostname.
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

## 10. Step 6 — Verify Docker networking

List networks:

```bash
docker network ls
```

Inspect the custom network:

```bash
docker network inspect app-network
```

Look for both `flask-container` and `mysql-container` in the `Containers` section. They should both have IP addresses in the configured subnet.

Test DNS resolution from Flask:

```bash
docker exec flask-container python -c \
"import socket; print(socket.gethostbyname('mysql-container'))"
```

You can also test the MySQL TCP port from Flask using Python:

```bash
docker exec flask-container python -c \
"import socket; s=socket.create_connection(('mysql-container',3306),timeout=5); print('MySQL TCP connection successful'); s.close()"
```

These tests verify name resolution and TCP reachability. The application itself verifies that the database credentials work.

## 11. Step 7 — Verify that messages are stored in MySQL

Connect to MySQL from inside its container:

```bash
docker exec -it mysql-container \
  mysql -u app_user -p flask_messages
```

Enter the password:

```text
app_password
```

Run:

```sql
SHOW TABLES;
SELECT * FROM messages;
EXIT;
```

## 12. Step 8 — Understand network isolation

Now let's see what happens when Flask and MySQL are not on the same network.

Create a second test network:

```bash
docker network create isolated-network
```

Disconnect Flask from the original network:

```bash
docker network disconnect app-network flask-container
```

Connect Flask to the isolated network:

```bash
docker network connect isolated-network flask-container
```

Try DNS resolution:

```bash
docker exec flask-container python -c \
"import socket; print(socket.gethostbyname('mysql-container'))"
```

It should fail because Flask and MySQL no longer share a network.

Restore the original setup:

```bash
docker network disconnect isolated-network flask-container
docker network connect app-network flask-container
```

Try the DNS test again. It should now work.

You can remove the extra network:

```bash
docker network rm isolated-network
```

## 13. Step 9 — Cleanup

Stop and remove the containers:

```bash
docker rm -f flask-container mysql-container
```

Remove the custom network:

```bash
docker network rm app-network
```

Remove the database volume only if you also want to delete all persisted database data:

```bash
docker volume rm mysql-data
```

## 14. Important Docker networking concepts

| Concept | What you learn |
|---|---|
| Bridge driver | Connects containers on a Docker bridge network |
| Custom bridge network | Provides isolated container networking |
| Container DNS | Containers can resolve each other by name |
| Port publishing | Makes a container port accessible from the host |
| Internal port | Allows container-to-container communication |
| Docker volume | Persists MySQL data beyond the container lifecycle |
| Network inspection | Shows connected containers and their IP addresses |

## 15. Practice challenges

Try these yourself after completing the project:

- [ ] Create the network without specifying a subnet and inspect the assigned subnet.
- [ ] Run both containers and inspect their IP addresses.
- [ ] Change `MYSQL_HOST` to an incorrect hostname and observe the error.
- [ ] Remove Flask from `app-network` and test database connectivity.
- [ ] Reconnect Flask and verify that the application works again.
- [ ] Stop and recreate MySQL while retaining the `mysql-data` volume.
- [ ] Remove and recreate the Flask container without rebuilding its image.
- [ ] Run a second Flask container on the same network and observe how it can also reach MySQL.
- [ ] Try connecting to MySQL from your host without publishing port 3306, and compare that with container-to-container access.

## 16. Expected final result

You should end up with:

- One custom bridge network: `app-network`.
- One Flask container: `flask-container`.
- One MySQL container: `mysql-container`.
- One Docker volume: `mysql-data`.
- A working Flask application at `http://localhost:5000`.
- Successful DNS resolution from Flask to MySQL using `mysql-container`.

**The key lesson:** Containers do not need to expose their ports to the host to communicate with each other. When they share a user-defined Docker bridge network, they can communicate using container names through Docker's embedded DNS.
