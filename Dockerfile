FROM python:3.10-slim

# Create non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements first for better caching
COPY --chown=user requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user . /app

# Expose port 7860 (HF Spaces requirement)
EXPOSE 7860

# Run the health check server (which starts the bot in background)
CMD ["python", "app.py"]
