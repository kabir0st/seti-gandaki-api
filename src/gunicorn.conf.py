import multiprocessing

workers = multiprocessing.cpu_count() * 2
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8989"

# Set a timeout (to prevent stuck workers)
timeout = 60  # Seconds before a worker is killed if unresponsive

max_requests = 1000
max_requests_jitter = 50
# Graceful timeout before killing a worker
graceful_timeout = 30

# Log level (optional)
loglevel = "info"

reload = True  # Auto-restart workers on code changes (useful in development)
