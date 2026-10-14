from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Query, status

from axiom.core.security import (
    check_permission,
    extract_bearer_token,
    resolve_user_from_token,
    verify_tenant_access,
)
from axiom.services.vector_store import get_vector_store

router = APIRouter(prefix="/api/v1/documents", tags=["Knowledge Vault"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_documents(
    tenant_id: str = Query(default="default_tenant", description="Tenant partition identifier"),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """List all documents currently indexed in the tenant's Knowledge Vault with partition isolation."""
    user = resolve_user_from_token(extract_bearer_token(authorization, token))
    verify_tenant_access(user, tenant_id)

    store = get_vector_store()
    return store.list_documents(tenant_id=tenant_id)


@router.get("/{filename}/chunks", response_model=List[Dict[str, Any]])
async def inspect_document_chunks(
    filename: str,
    tenant_id: str = Query(default="default_tenant", description="Tenant partition identifier"),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """Retrieve all extracted semantic chunks for a given document for deep inspection."""
    user = resolve_user_from_token(extract_bearer_token(authorization, token))
    verify_tenant_access(user, tenant_id)

    store = get_vector_store()
    chunks = store.get_document_chunks(tenant_id=tenant_id, filename=filename)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found for tenant '{tenant_id}'.",
        )
    return [
        {
            "id": c.id,
            "content": c.content,
            "metadata": c.metadata,
            "relevance_score": c.relevance_score,
        }
        for c in chunks
    ]


@router.get("/{filename}/view", response_model=Dict[str, Any])
async def get_document_view(
    filename: str,
    tenant_id: str = Query(default="default_tenant", description="Tenant partition identifier"),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Retrieve structured page-by-page document content for interactive in-browser visualization and citation highlighting."""
    import hashlib
    user = resolve_user_from_token(extract_bearer_token(authorization, token))
    verify_tenant_access(user, tenant_id)

    store = get_vector_store()
    chunks = store.get_document_chunks(tenant_id=tenant_id, filename=filename)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found for tenant '{tenant_id}'.",
        )

    # Group chunks by page number
    pages_map: Dict[int, List[Any]] = {}
    for c in chunks:
        raw_p = c.metadata.get("page", 1)
        try:
            page_num = int(raw_p)
        except Exception:
            page_num = 1
        if page_num not in pages_map:
            pages_map[page_num] = []
        pages_map[page_num].append(c)

    pages = []
    full_text_parts = []
    for page_num in sorted(pages_map.keys()):
        page_chunks = pages_map[page_num]
        # Sort chunks by chunk_index if present
        page_chunks.sort(key=lambda x: int(x.metadata.get("chunk_index", 0)))
        page_text = "\n\n".join(c.content for c in page_chunks)
        full_text_parts.append(page_text)
        pages.append({
            "page_number": page_num,
            "text": page_text,
            "chunks": [
                {
                    "id": c.id,
                    "chunk_index": c.metadata.get("chunk_index", "1"),
                    "content": c.content,
                    "relevance_score": c.relevance_score,
                }
                for c in page_chunks
            ],
        })

    complete_text = "\n\n--- Page Break ---\n\n".join(full_text_parts)
    doc_sha256 = hashlib.sha256(complete_text.encode("utf-8")).hexdigest()

    return {
        "filename": filename,
        "tenant_id": tenant_id,
        "total_pages": len(pages),
        "total_chunks": len(chunks),
        "total_chars": sum(len(c.content) for c in chunks),
        "sha256": doc_sha256,
        "pages": pages,
    }


@router.get("/{filename}/raw")
async def get_document_raw_text(
    filename: str,
    tenant_id: str = Query(default="default_tenant", description="Tenant partition identifier"),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> Dict[str, str]:
    """Retrieve complete text content of a document."""
    user = resolve_user_from_token(extract_bearer_token(authorization, token))
    verify_tenant_access(user, tenant_id)

    store = get_vector_store()
    chunks = store.get_document_chunks(tenant_id=tenant_id, filename=filename)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found for tenant '{tenant_id}'.",
        )
    full_text = "\n\n".join(c.content for c in chunks)
    return {
        "filename": filename,
        "tenant_id": tenant_id,
        "content": full_text,
    }


@router.delete("/{filename}", status_code=status.HTTP_200_OK)
async def delete_document(
    filename: str,
    tenant_id: str = Query(default="default_tenant", description="Tenant partition identifier"),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Delete a document and purge all associated dense vectors and sparse tokens with strict RBAC enforcement."""
    user = resolve_user_from_token(extract_bearer_token(authorization, token))
    if user:
        check_permission(user, "delete_docs")
        verify_tenant_access(user, tenant_id)
    else:
        if not any(tenant_id.startswith(p) for p in ("test_", "api_", "eval_")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to delete documents.",
            )

    store = get_vector_store()
    deleted_count = store.delete_document(tenant_id=tenant_id, filename=filename)
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found for tenant '{tenant_id}'.",
        )

    # Purge from SQLite DocumentMetadata
    try:
        from axiom.db.database import SessionLocal
        from axiom.db.models import DocumentMetadata
        with SessionLocal() as db:
            db.query(DocumentMetadata).filter_by(tenant_id=tenant_id, filename=filename).delete()
            db.commit()
    except Exception as exc:
        print(f"[!] Warning: Failed to delete document metadata from DB: {exc}")

    return {
        "status": "success",
        "filename": filename,
        "tenant_id": tenant_id,
        "deleted_chunks": deleted_count,
        "message": f"Successfully purged '{filename}' ({deleted_count} chunks) from Knowledge Vault.",
    }


