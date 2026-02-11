FROM python:3.13-slim-bookworm

ARG TARGETPLATFORM

ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    build-essential \
    cmake \
    unixodbc \
    unixodbc-dev \
    g++ \
    apt-transport-https \
 && rm -rf /var/lib/apt/lists/*

# Microsoft ODBC repo
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor \
    | tee /usr/share/keyrings/microsoft-prod.gpg > /dev/null && \
    curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
    | tee /etc/apt/sources.list.d/mssql-release.list

# Install SQL Server + Postgres ODBC
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y \
      msodbcsql18 \
      odbc-postgresql \
 && rm -rf /var/lib/apt/lists/*

# MySQL ODBC (manual)
RUN ARCH=$(case ${TARGETPLATFORM:-linux/amd64} in \
      "linux/amd64") echo "x86-64bit" ;; \
      "linux/arm64") echo "aarch64" ;; \
    esac) && \
    curl -L https://dev.mysql.com/get/Downloads/Connector-ODBC/8.3/mysql-connector-odbc-8.3.0-linux-glibc2.28-${ARCH}.tar.gz \
      | tar -xzf - && \
    cp mysql-connector-odbc-8.3.0-linux-glibc2.28-${ARCH}/lib/*.so /usr/local/lib/ && \
    printf "[MySQL ODBC 8.3 Unicode Driver]\nDriver=/usr/local/lib/libmyodbc8w.so\n" >> /etc/odbcinst.ini && \
    printf "[MySQL ODBC 8.3 ANSI Driver]\nDriver=/usr/local/lib/libmyodbc8a.so\n" >> /etc/odbcinst.ini


# Install uv
RUN pip install --no-cache-dir uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

# Python dependencies
WORKDIR /app
COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# App code
COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
