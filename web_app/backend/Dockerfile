
# Stage 1: Build Java Bots
FROM maven:3.9-eclipse-temurin-23 AS java-builder

WORKDIR /app

# Copy java project
COPY chess_engine_java /app/chess_engine_java

# Build Java Project
WORKDIR /app/chess_engine_java
RUN mvn clean compile

# Stage 2: Runtime Environment
# Use Java 23 JRE as base since it's harder to install new Java on Python images
FROM eclipse-temurin:23-jre

# Install Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Fix python symlink if necessary (usually python3 is enough, but some scripts might use python)
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Copy Java artifacts from builder stage (libs and compiled classes)
COPY --from=java-builder /app/chess_engine_java/libs /app/chess_engine_java/libs
COPY --from=java-builder /app/chess_engine_java/target/classes /app/chess_engine_java/target/classes

# Copy bots directory (shared logic)
COPY bots /app/bots

# Copy web app backend
COPY web_app/backend /app/web_app/backend

# Install Python dependencies
# We need to break system packages restriction on some newer distros or use venv
# For container simplicity, --break-system-packages is acceptable for simple deployments
WORKDIR /app/web_app/backend
RUN pip3 install --no-cache-dir --break-system-packages fastapi uvicorn chess

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
