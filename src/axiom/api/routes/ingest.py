from typing import Optional
from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile, status
from axiom.api.schemas.ingest import IngestRequest, IngestResponse
from axiom.core.security import (
    check_permission,
    extract_bearer_token,
    resolve_user_from_token,
    verify_tenant_access,
)
from axiom.services.document_loader import process_document
from axiom.services.vector_store import get_vector_store

router = APIRouter(prefix="/api/v1", tags=["Ingestion"])


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(
    payload: IngestRequest,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> IngestResponse:
    """Ingest document chunks into both dense vector store and sparse BM25 index with tenant isolation."""
    user = resolve_user_from_token(extract_bearer_token(authorization, token))
    if user:
        check_permission(user, "ingest")
        verify_tenant_access(user, payload.tenant_id)

    if not payload.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one DocumentChunk must be provided for ingestion.",
        )

    store = get_vector_store()
    count = store.ingest_documents(tenant_id=payload.tenant_id, chunks=payload.documents)

    return IngestResponse(
        tenant_id=payload.tenant_id,
        ingested_count=count,
        status="success",
    )


@router.post("/ingest/file", status_code=status.HTTP_201_CREATED)
async def ingest_file(
    file: UploadFile = File(..., description="Document or book file (.pdf, .txt, .md, .csv)"),
    tenant_id: str = Form("default_tenant", description="Target tenant ID for partition isolation"),
    chunk_size: int = Form(800, description="Chunk target character size"),
    chunk_overlap: int = Form(150, description="Overlap between consecutive chunks"),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Form(None),
) -> dict:
    """Upload and index a complete document or book file (PDF, TXT, Markdown).

    Automatically parses pages, generates semantically coherent chunks,
    and indexes them into Axiom's hybrid vector store.
    """
    user = resolve_user_from_token(extract_bearer_token(authorization, token))
    if user:
        check_permission(user, "ingest")
        verify_tenant_access(user, tenant_id)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid filename required.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        chunks = process_document(
            file_bytes=file_bytes,
            filename=file.filename,
            tenant_id=tenant_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process file: {str(exc)}",
        )

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text could be extracted from the document.",
        )

    store = get_vector_store()
    count = store.ingest_documents(tenant_id=tenant_id, chunks=chunks)

    # Persist document metadata in SQLite
    try:
        from datetime import datetime
        from axiom.db.database import SessionLocal
        from axiom.db.models import DocumentMetadata

        total_chars = sum(len(c.content) for c in chunks)
        uploader = user.get("email", "anonymous") if user else "anonymous"
        with SessionLocal() as db:
            doc_meta = db.query(DocumentMetadata).filter_by(tenant_id=tenant_id, filename=file.filename).first()
            if not doc_meta:
                doc_meta = DocumentMetadata(
                    tenant_id=tenant_id,
                    filename=file.filename,
                    chunk_count=count,
                    char_count=total_chars,
                    uploaded_by=uploader,
                    uploaded_at=datetime.utcnow(),
                )
                db.add(doc_meta)
            else:
                doc_meta.chunk_count = count
                doc_meta.char_count = total_chars
                doc_meta.uploaded_by = uploader
                doc_meta.uploaded_at = datetime.utcnow()
            db.commit()

    except Exception as exc:
        print(f"[!] Failed to persist document metadata to DB: {exc}")

    return {
        "tenant_id": tenant_id,
        "filename": file.filename,
        "ingested_chunks": count,
        "status": "success",
        "message": f"Successfully indexed {count} chunks from '{file.filename}' into tenant '{tenant_id}'.",
    }


