"""OpenTelemetry configuration and initialization."""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from loguru import logger

from src.core.config import settings


def configure_opentelemetry() -> tuple[trace.Tracer, metrics.Meter]:
    """
    Configure OpenTelemetry for tracing and metrics.
    
    Returns:
        Tuple of (Tracer, Meter)
    """
    # Create resource with service information
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": settings.app_version,
        "deployment.environment": settings.environment,
    })
    
    # Configure tracing
    tracer_provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter for traces
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True  # Use TLS in production
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
    
    # Add Jaeger exporter for local development
    if settings.environment == "development":
        jaeger_exporter = JaegerExporter(
            agent_host_name=settings.jaeger_agent_host,
            agent_port=settings.jaeger_agent_port,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    
    trace.set_tracer_provider(tracer_provider)
    
    # Configure metrics
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True
    )
    
    metric_reader = PeriodicExportingMetricReader(
        otlp_metric_exporter,
        export_interval_millis=60000  # Export every 60 seconds
    )
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)
    
    # Get tracer and meter
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)
    
    logger.info(f"OpenTelemetry configured - Service: {settings.otel_service_name}")
    
    return tracer, meter


def instrument_app(app):
    """
    Instrument FastAPI app with OpenTelemetry.
    
    Args:
        app: FastAPI application instance
    """
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument HTTPX client
    HTTPXClientInstrumentor().instrument()
    
    logger.info("FastAPI app instrumented with OpenTelemetry")


# Global tracer and meter instances
tracer: trace.Tracer = None
meter: metrics.Meter = None


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    global tracer
    if tracer is None:
        tracer, _ = configure_opentelemetry()
    return tracer


def get_meter() -> metrics.Meter:
    """Get the global meter instance."""
    global meter
    if meter is None:
        _, meter = configure_opentelemetry()
    return meter
