from time import perf_counter

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)


@app.before_request
def start_request_timer():
    g.start_time = perf_counter()


@app.after_request
def record_request_metrics(response):
    endpoint = request.path
    duration = perf_counter() - g.start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    return response


@app.route("/")
def home():
    return jsonify(
        message="Cloud monitoring application is running",
        status="healthy",
    )


@app.route("/health")
def health():
    return jsonify(status="healthy"), 200


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # nosec B104 - required for container access
        port=5000,
    )
