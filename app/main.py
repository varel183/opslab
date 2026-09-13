import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.models import Task
from app.schemas import TaskCreate, TaskRead, TaskUpdate

DbSession = Annotated[Session, Depends(get_db)]

logger = logging.getLogger("opslab")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def configure_tracing() -> None:
    if not settings.otel_traces_endpoint:
        return
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "opslab-api",
                "service.version": settings.app_version,
                "deployment.environment": settings.environment,
            }
        )
    )
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_traces_endpoint))
    )
    trace.set_tracer_provider(provider)


configure_tracing()
tracer = trace.get_tracer("opslab.api")

REQUEST_COUNT = Counter(
    "opslab_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_DURATION = Histogram(
    "opslab_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    started = perf_counter()
    status_code = 500
    path = request.url.path
    with tracer.start_as_current_span(
        f"{request.method} {path}", kind=SpanKind.SERVER
    ) as span:
        try:
            response = await call_next(request)
            status_code = response.status_code
            route = request.scope.get("route")
            path = route.path if route else path
            return response
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            duration = perf_counter() - started
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("http.route", path)
            span.set_attribute("http.response.status_code", status_code)
            if status_code >= 500:
                span.set_status(Status(StatusCode.ERROR))
            context = span.get_span_context()
            trace_id = f"{context.trace_id:032x}" if context.is_valid else "unavailable"
            REQUEST_COUNT.labels(request.method, path, status_code).inc()
            REQUEST_DURATION.labels(request.method, path).observe(duration)
            logger.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "method": request.method,
                        "path": path,
                        "status": status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "trace_id": trace_id,
                        "environment": settings.environment,
                    }
                )
            )


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/demo/slow", tags=["observability"])
async def demo_slow(delay_ms: int = 500) -> dict[str, int | str]:
    delay_ms = min(max(delay_ms, 0), 5000)
    await asyncio.sleep(delay_ms / 1000)
    return {"status": "slow response completed", "delay_ms": delay_ms}


@app.get("/demo/error", tags=["observability"])
def demo_error() -> None:
    logger.error(json.dumps({"event": "demo_error", "reason": "intentional learning demo"}))
    raise HTTPException(status_code=500, detail="Intentional error for observability demo")


@app.get("/ready", tags=["system"])
def ready(db: DbSession) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate, db: DbSession) -> Task:
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskRead], tags=["tasks"])
def list_tasks(db: DbSession) -> list[Task]:
    return list(db.scalars(select(Task).order_by(Task.id)))


def find_task(task_id: int, db: Session) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/tasks/{task_id}", response_model=TaskRead, tags=["tasks"])
def get_task(task_id: int, db: DbSession) -> Task:
    return find_task(task_id, db)


@app.patch("/tasks/{task_id}", response_model=TaskRead, tags=["tasks"])
def update_task(task_id: int, payload: TaskUpdate, db: DbSession) -> Task:
    task = find_task(task_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: int, db: DbSession) -> Response:
    task = find_task(task_id, db)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
