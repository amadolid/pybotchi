"""PyBotchi CLI."""

from asyncio import run
from importlib.resources import files
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getmembers, isclass
from multiprocessing import Process, cpu_count
from os import getenv
from pathlib import Path
from signal import SIGINT, SIGTERM, signal
from sys import path as sys_path
from types import FrameType

from click import argument, command, echo, option

from grpc import ssl_server_credentials
from grpc.aio import server as grpc_server

from grpc_tools import protoc

from pybotchi import Action
from pybotchi.utils import uuid


PROCESSES: list[Process] = []


async def serve(
    id: str,
    path: str,
    host: str,
    port: str,
    root_certificates: bytes | None,
    private_key: bytes | None,
    certificate_chain: bytes | None,
    require_client_auth: bool,
) -> None:
    """Serve GRPC."""
    from .pybotchi_pb2_grpc import add_PyBotchiGRPCServicer_to_server
    from .handler import PyBotchiGRPC

    server = grpc_server(
        options=[
            ("grpc.so_reuseport", 1),
        ]
    )
    target_path = Path(path).resolve()
    target_directory = target_path.parent
    target_file = target_path.stem

    spec = spec_from_file_location(target_file, target_path)
    if not spec or spec.loader is None:
        raise ImportError(f"Error occured when importing `{path}`. Loader is missing.")

    if target_directory not in sys_path:
        sys_path.insert(0, str(target_directory))
    module_spec = module_from_spec(spec)
    spec.loader.exec_module(module_spec)

    grpc_handler = PyBotchiGRPC
    for _, member in getmembers(module_spec, isclass):
        if issubclass(member, PyBotchiGRPC):
            grpc_handler = member
            break

    groups: dict[str, dict[str, type[Action]]] = {}
    queue = Action.__subclasses__()
    while queue:
        que = queue.pop()
        if isinstance(_groups := que.__groups__, dict):
            _groups = _groups.get("grpc")

        if _groups:
            for group in _groups:
                group = group.lower()
                if (_group := groups.get(group)) is None:
                    groups[group] = _group = {}

                _group[que.__name__] = que

        queue.extend(que.__subclasses__())

    add_PyBotchiGRPCServicer_to_server(grpc_handler(id, module_spec.__name__, groups), server)

    address = f"{host}:{port}"
    if private_key and certificate_chain:
        server.add_secure_port(
            address,
            ssl_server_credentials(
                [(private_key, certificate_chain)],
                root_certificates,
                require_client_auth,
            ),
        )
    else:
        server.add_insecure_port(address)
    await server.start()

    echo(f"# Agent Path: {path}")
    echo(f"# Agent Handler: {grpc_handler.__name__}")
    echo(f"# gRPC server running on {address}")
    echo("#-------------------------------------------------------#")
    await server.wait_for_termination()


def terminate(sig: int, frame: FrameType | None) -> None:
    """Terminate all processes."""
    for p in PROCESSES:
        p.terminate()


def start(
    id: str,
    path: str,
    host: str,
    port: str,
    root_certificates: bytes | None,
    private_key: bytes | None,
    certificate_chain: bytes | None,
    require_client_auth: bool,
) -> None:
    """Start the server."""
    run(
        serve(
            id,
            path,
            host,
            port,
            root_certificates,
            private_key,
            certificate_chain,
            require_client_auth,
        )
    )


@command()
@argument("path")
@option("--id", "-i", default=None, help="Agent ID")
@option("--host", "-h", default=None, help="Host to bind")
@option("--port", "-p", default=None, help="Port to bind")
@option("--workers", "-w", default=None, help="Number of worker processes")
@option("--root-certificates", "-r", default=None, help="Root certificates path")
@option("--private-key", "-k", default=None, help="Private key path")
@option("--certificate-chain", "-c", default=None, help="Certificate chain path")
@option("--require-client-auth", "-a", default=False, help="Require client auth")
def main(
    path: str,
    id: str | None,
    host: str | None,
    port: str | None,
    workers: str | None,
    root_certificates: str | None,
    private_key: str | None,
    certificate_chain: str | None,
    require_client_auth: bool,
) -> None:
    """Greet someone."""
    id = id or getenv("AGENT_ID") or f"agent_{uuid().hex}"
    host = host or getenv("AGENT_HOST") or "0.0.0.0"
    port = port or getenv("AGENT_PORT") or "50051"
    worker_count = min(int(workers or getenv("AGENT_WORKERS") or "1"), cpu_count())

    if not id.isidentifier():
        raise ValueError(
            f"'{id}' is not a valid Python identifier (must start with a letter/underscore and contain only alphanumeric characters/underscores)."
        )

    echo("#-------------------------------------------------------#")
    echo(f"# Agent ID: {id}")
    echo(f"# Agent Path: {path}")

    if root_certificates:
        echo(f"# Root Certificates: {root_certificates}")
        with open(root_certificates, "rb") as f:
            _root_certificates = f.read()
    else:
        _root_certificates = None

    if private_key:
        echo(f"# Private Key: {private_key}")
        with open(private_key, "rb") as f:
            _private_key = f.read()
    else:
        _private_key = None

    if certificate_chain:
        echo(f"# Certificate Chain: {certificate_chain}")
        with open(certificate_chain, "rb") as f:
            _certificate_chain = f.read()
    else:
        _certificate_chain = None

    echo(f"# Agent Path: {path}")
    echo(f"# Starting {workers} worker(s) on {host}:{port}")
    echo("#-------------------------------------------------------#")

    for _ in range(worker_count):
        p = Process(
            target=start,
            args=(
                id,
                path,
                host,
                port,
                _root_certificates,
                _private_key,
                _certificate_chain,
                require_client_auth,
            ),
        )
        p.start()
        PROCESSES.append(p)

    signal(SIGINT, terminate)
    signal(SIGTERM, terminate)

    for p in PROCESSES:
        p.join()


@command()
def compile() -> None:
    """Compile `pybotchi.proto`."""
    current_dir = Path(__file__).parent
    proto_include = files("grpc_tools").joinpath("_proto")

    protoc.main(
        [
            "",
            f"-I{current_dir}",
            f"-I{proto_include}",
            f"--python_out={current_dir}",
            f"--pyi_out={current_dir}",
            f"--grpc_python_out={current_dir}",
            "pybotchi.proto",  # must be relative to --proto_path
        ]
    )

    file_path = current_dir / "pybotchi_pb2_grpc.py"

    # Read the file content
    content = file_path.read_text(encoding="utf-8")

    # Replace occurrences
    updated_content = content.replace(
        "import pybotchi_pb2 as pybotchi__pb2",
        "from . import pybotchi_pb2 as pybotchi__pb2",
    )

    # Write the updated content back to the file
    file_path.write_text(updated_content, encoding="utf-8")
