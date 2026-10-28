"""
Ingestion job: index the local policy files and the default te.eg pages into Qdrant.

    python -m telecopilot.kb.ingest --all
    docker compose run --rm app python -m telecopilot.kb.ingest --all

Runs outside the API so the API starts in seconds and ingestion failures are visible: the exit code is 1 when any
source fails. Re-running is safe: point ids derive from chunk ids, so chunks are overwritten, not duplicated.
"""

import argparse
import sys
from collections import Counter

from telecopilot.core.logger import configure_logging, get_logger
from telecopilot.kb.ingestion_service import IngestionService
from telecopilot.kb.repositories.qdrant import QdrantVectorRepository
from telecopilot.kb.sparse import SparseEmbeddingModel
from telecopilot.llm.cohere import CohereService

logger = get_logger()


def build_ingestion_service() -> IngestionService:
    # This entry point wires its own objects: kb must not import api.dependencies (layer rule).
    return IngestionService(QdrantVectorRepository(), CohereService(), SparseEmbeddingModel())


def run_all(service: IngestionService) -> int:
    """Ingest every default source; return the process exit code."""
    results = service.ingest_all_default_policies()
    statuses = Counter(result["status"] for result in results)
    logger.info(f"Ingestion finished: {len(results)} sources, {dict(statuses)}")
    for failed in (result for result in results if result["status"] == "FAILED"):
        logger.error(f"FAILED {failed.get('source') or failed.get('source_url')}: {failed['error']}")
    return 1 if statuses["FAILED"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m telecopilot.kb.ingest", description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true", required=True, help="local data/raw files + default te.eg pages")
    parser.parse_args(argv)
    configure_logging()
    return run_all(build_ingestion_service())


if __name__ == "__main__":
    sys.exit(main())
