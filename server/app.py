"""
FastAPI application for the Insurance Claims Adjudication Environment.

Endpoints:
    - POST /reset: Reset the environment with a task
    - POST /step: Execute a claims adjudication action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions
    - GET /health: Health check

Usage:
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core"
    ) from e

try:
    from ..models import ClaimsAction, ClaimsObservation
    from .claims_env_environment import ClaimsEnvironment
except (ImportError, ModuleNotFoundError):
    from models import ClaimsAction, ClaimsObservation
    from server.claims_env_environment import ClaimsEnvironment


app = create_app(
    ClaimsEnvironment,
    ClaimsAction,
    ClaimsObservation,
    env_name="claims_env",
    max_concurrent_envs=100,
)


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
