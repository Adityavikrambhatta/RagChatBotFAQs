from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from app.config import get_settings
from app.service import RagFaqService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG FAQ chatbot utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build-corpus", help="Build or refresh a corpus from local files")
    build.add_argument("--corpus-name", required=True)
    build.add_argument("--input-dir", required=True)
    build.add_argument("--force-rebuild", action="store_true")

    serve = subparsers.add_parser("serve", help="Run the FastAPI server locally")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    service = RagFaqService(settings)

    if args.command == "build-corpus":
        response = service.build_corpus(
            corpus_name=args.corpus_name,
            input_dir=Path(args.input_dir).expanduser().resolve(),
            force_rebuild=args.force_rebuild,
        )
        print(json.dumps(response.model_dump(), indent=2))
        return

    if args.command == "serve":
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
