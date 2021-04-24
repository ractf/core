"""Custom workers for use in production or development."""

from uvicorn.workers import UvicornWorker as BaseUvicornWorker


class WSProtoWorker(BaseUvicornWorker):
    """A custom worker to ensure that 'wsproto' is used for production."""

    CONFIG_KWARGS = {"loop": "uvloop", "http": "httptools", "ws": "wsproto"}
