"""Axiom Document & Book Ingestion CLI Tool.

Enables batch ingestion of books, PDFs, markdown files, and directories
directly into Axiom's hybrid vector store.

Usage:
    python scripts/ingest_folder.py --path "my_book.pdf"
    python scripts/ingest_folder.py --dir "my_books_folder/" --tenant "my_company"
"""

import argparse
from pathlib import Path
import sys

# Ensure UTF-8 stdout for Windows consoles
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from axiom.services.document_loader import process_document
from axiom.services.vector_store import get_vector_store


def ingest_file(file_path: Path, tenant_id: str, chunk_size: int, chunk_overlap: int) -> int:
    """Ingest a single document file."""
    if not file_path.exists():
        print(f"❌ Error: File not found at '{file_path}'")
        return 0

    print(f"[*] Reading and parsing '{file_path.name}' ({file_path.stat().st_size / 1024:.1f} KB)...")
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    try:
        chunks = process_document(
            file_bytes=file_bytes,
            filename=file_path.name,
            tenant_id=tenant_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    except Exception as exc:
        print(f"❌ Failed to process '{file_path.name}': {exc}")
        return 0

    if not chunks:
        print(f"⚠️ Warning: No readable text extracted from '{file_path.name}'")
        return 0

    store = get_vector_store()
    count = store.ingest_documents(tenant_id=tenant_id, chunks=chunks)
    print(f"✅ Ingested {count} chunks into tenant '{tenant_id}' from '{file_path.name}'")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Axiom Book & Document Ingestion Utility")
    parser.add_argument("--path", type=str, help="Path to a single document or book (.pdf, .txt, .md)")
    parser.add_argument("--dir", type=str, help="Directory containing documents or books to ingest")
    parser.add_argument("--tenant", type=str, default="default_tenant", help="Target tenant ID (default: default_tenant)")
    parser.add_argument("--chunk-size", type=int, default=800, help="Target character size per chunk (default: 800)")
    parser.add_argument("--chunk-overlap", type=int, default=150, help="Overlap between chunks (default: 150)")

    args = parser.parse_args()

    if not args.path and not args.dir:
        parser.print_help()
        print("\n❌ Error: Please specify either --path <file> or --dir <folder>")
        sys.exit(1)

    total_chunks = 0
    total_files = 0

    if args.path:
        p = Path(args.path)
        total_chunks += ingest_file(p, args.tenant, args.chunk_size, args.chunk_overlap)
        total_files += 1

    if args.dir:
        d = Path(args.dir)
        if not d.is_dir():
            print(f"❌ Error: '{d}' is not a directory.")
            sys.exit(1)

        allowed_exts = {".pdf", ".txt", ".md", ".markdown", ".json", ".csv"}
        files = [f for f in d.iterdir() if f.suffix.lower() in allowed_exts]
        print(f"[*] Found {len(files)} eligible documents in '{d}'")

        for f in files:
            chunks_added = ingest_file(f, args.tenant, args.chunk_size, args.chunk_overlap)
            if chunks_added > 0:
                total_chunks += chunks_added
                total_files += 1

    print("\n" + "=" * 60)
    print(f"🎉 Ingestion Complete: {total_files} file(s) indexed -> {total_chunks} total chunks.")
    print(f"Partition Tenant ID: '{args.tenant}'")
    print("=" * 60)


if __name__ == "__main__":
    main()
