# GHOST FIVE // SPECTRAL CORE // VECTIS
# Serves the Mission Readiness demo application powered by the VECTIS engine.

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import ipaddress
import json
import mimetypes
import threading
import webbrowser
from typing import Any

from vectis import __version__
from vectis.compiler import compile_program
from vectis.parser import parse
from vectis.runtime import Runtime


def _jsonable(value: Any) -> Any:
    """Convert runtime dataclasses and enums into JSON safe structures."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _jsonable(item)
            for key, item in asdict(value).items()
        }
    if isinstance(value, dict):
        return {
            str(key): _jsonable(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _is_loopback(host: str) -> bool:
    """Return whether a bind target is local to the current system."""
    if host in {"", "localhost"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _validated_text(value: str, label: str) -> str:
    """Validate text that will be represented by the current string grammar."""
    clean = value.strip()
    if not clean:
        raise ValueError(f"{label} must not be empty")
    if len(clean) > 120:
        raise ValueError(f"{label} must be 120 characters or fewer")
    if any(character in clean for character in ('"', "\\", "\r", "\n")):
        raise ValueError(
            f"{label} cannot contain quotes, backslashes, or line breaks"
        )
    return clean


def build_readiness_source(
    *,
    mission: str,
    operator: str,
    ready: bool,
    quality: int,
    risk: int,
) -> str:
    """Build a validated demonstration mission from structured form input."""
    if not 0 <= quality <= 100:
        raise ValueError("quality must be between 0 and 100")
    if not 0 <= risk <= 100:
        raise ValueError("risk must be between 0 and 100")
    mission_text = json.dumps(
        _validated_text(mission, "mission")
    )
    operator_text = json.dumps(
        _validated_text(operator, "operator")
    )
    ready_text = "true" if ready else "false"

    return (
        f"mission {mission_text} {{\n"
        f"    source operator {operator_text};\n"
        f"    source ready {ready_text};\n"
        f"    source quality {quality};\n"
        f"    source risk {risk};\n"
        "    let approved ready && quality >= 80 && risk <= 35;\n"
        '    let status if_else(approved, "AUTHORIZED", "REVIEW");\n'
        "\n"
        "    assert quality >= 0 && quality <= 100;\n"
        "    assert risk >= 0 && risk <= 100;\n"
        "\n"
        "    when approved {\n"
        '        publish concat("OPERATOR ", operator, " // ", status);\n'
        "    } otherwise {\n"
        '        publish concat("OPERATOR ", operator, " // REVIEW");\n'
        "    }\n"
        "}\n"
    )


def run_readiness(
    *,
    mission: str,
    operator: str,
    ready: bool,
    quality: int,
    risk: int,
) -> dict[str, object]:
    """Compile and execute the demonstration mission through VECTIS."""
    source = build_readiness_source(
        mission=mission,
        operator=operator,
        ready=ready,
        quality=quality,
        risk=risk,
    )
    program = parse(source, file="<mission-readiness-demo>")
    compiled = compile_program(program)
    if compiled.graph is None:
        return {
            "source": source,
            "diagnostics": [
                item.to_dict()
                for item in compiled.diagnostics
            ],
            "graph": None,
            "runtime": None,
        }

    runtime = Runtime(compiled.graph).execute()
    return {
        "source": source,
        "diagnostics": [
            item.to_dict()
            for item in compiled.diagnostics
        ],
        "graph": compiled.graph.to_dict(),
        "runtime": _jsonable(runtime),
    }


class DemoHandler(BaseHTTPRequestHandler):
    """Serve the branded demo UI and its VECTIS execution endpoint."""

    server_version = "VECTISDemo/0.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, status: int, payload: object) -> None:
        body = json.dumps(
            _jsonable(payload),
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 64_000:
            raise ValueError(
                "request body must be between 1 byte and 64 KB"
            )
        payload = json.loads(
            self.rfile.read(length).decode("utf-8")
        )
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json(
                200,
                {
                    "service": "vectis-mission-readiness-demo",
                    "version": __version__,
                    "status": "ok",
                },
            )
            return
        self._serve_asset()

    def do_POST(self) -> None:
        if self.path != "/api/run":
            self._send_json(404, {"error": "unknown API endpoint"})
            return

        try:
            data = self._read_json()
            result = run_readiness(
                mission=str(data.get("mission", "")),
                operator=str(data.get("operator", "")),
                ready=bool(data.get("ready", False)),
                quality=int(data.get("quality", 0)),
                risk=int(data.get("risk", 0)),
            )
            runtime = result.get("runtime")
            status = (
                200
                if isinstance(runtime, dict)
                and runtime.get("success") is True
                else 422
            )
            self._send_json(status, result)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json(400, {"error": str(exc)})

    def _serve_asset(self) -> None:
        relative = (
            "index.html"
            if self.path in {"", "/"}
            else self.path.lstrip("/")
        )
        if ".." in relative.split("/"):
            self._send_json(404, {"error": "not found"})
            return

        root = files("vectis").joinpath("demo_assets")
        target = root.joinpath(relative)
        if not target.is_file():
            self._send_json(404, {"error": "not found"})
            return

        body = target.read_bytes()
        content_type = (
            mimetypes.guess_type(relative)[0]
            or "application/octet-stream"
        )
        if (
            content_type.startswith("text/")
            or content_type == "application/javascript"
        ):
            content_type += "; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def run_demo_app(
    *,
    host: str = "127.0.0.1",
    port: int = 8775,
    open_browser: bool = True,
    allow_remote: bool = False,
) -> None:
    """Launch the Mission Readiness demo application."""
    if not allow_remote and not _is_loopback(host):
        raise ValueError(
            "VECTIS Demo binds to loopback by default; "
            "use --allow-remote for another interface"
        )

    server = ThreadingHTTPServer((host, port), DemoHandler)
    visible_host = (
        "127.0.0.1"
        if host in {"0.0.0.0", "::"}
        else host
    )
    url = f"http://{visible_host}:{server.server_port}/"

    print(f"VECTIS Mission Readiness Demo {__version__}")
    print(f"Listening on {url}")
    print("Press Ctrl+C to stop.")

    if open_browser:
        threading.Timer(
            0.25,
            lambda: webbrowser.open(url),
        ).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
