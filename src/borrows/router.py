import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import asc, col, desc, func, select

from src.auth.permissions import Permission
from src.borrows import service
from src.borrows.models import BorrowRecord
from src.borrows.schemas import (
    BorrowCreate,
    BorrowQueryParams,
    BorrowRecordPublic,
    BorrowRecordsPublic,
)
from src.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_any_permission,
    require_permission,
)

router = APIRouter(prefix="/borrows", tags=["borrows"])





@router.post(
    "/",
    response_model=BorrowRecordPublic,
    dependencies=[Depends(require_permission(Permission.BORROWS_CREATE))],
)
def borrow_book(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    borrow_in: BorrowCreate,
) -> Any:
    """
    Borrow a book from the library.

    Requires: borrows:create permission (member role by default)

    The current authenticated user becomes the borrower.
    A book can only be borrowed by one user at a time.
    """
    try:
        borrow_record = service.borrow_book(
            session=session,
            book_id=borrow_in.book_id,
            borrower_id=current_user.id,
        )
        return borrow_record
    except service.BookNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except service.BookNotAvailableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{borrow_id}/return",
    response_model=BorrowRecordPublic,
    dependencies=[Depends(require_permission(Permission.BORROWS_RETURN))],
)
def return_book(
    borrow_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Return a borrowed book.

    Requires: borrows:return permission (member role by default)

    Only the user who borrowed the book can return it.
    """
    try:
        borrow_record = service.return_book(
            session=session,
            borrow_record_id=borrow_id,
            returning_user_id=current_user.id,
        )
        return borrow_record
    except service.BorrowRecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except service.BookAlreadyReturnedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except service.NotBorrowerError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get(
    "/me",
    response_model=BorrowRecordsPublic,
    dependencies=[Depends(require_permission(Permission.BORROWS_READ))],
)
def get_my_borrows(
    session: SessionDep,
    current_user: CurrentUser,
    params: BorrowQueryParams = Depends(),
) -> Any:
    """
    Get the current user's borrow records.

    Requires: borrows:read permission (member role by default)

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (max 1000)
    - active_only: If true, only return books currently borrowed (not returned)
    - book_id: Filter by specific book ID
    - sort: Sort field with optional - prefix for descending (default: -borrowed_at for most recent first)
    """
    # Build query - always filter by current user
    query = select(BorrowRecord).where(BorrowRecord.borrower_id == current_user.id)

    # Apply active_only filter
    if params.active_only:
        query = query.where(BorrowRecord.returned_at == None)  # noqa: E711

    # Apply book_id filter
    if params.book_id:
        query = query.where(BorrowRecord.book_id == params.book_id)

    # Count total matching records
    count_query = select(func.count()).select_from(query.subquery())
    count = session.exec(count_query).one()

    # Apply sorting
    sort_column = {
        "borrowed_at": BorrowRecord.borrowed_at,
        "returned_at": BorrowRecord.returned_at,
    }.get(params.sort_field, BorrowRecord.borrowed_at)

    if params.is_descending:
        query = query.order_by(desc(col(sort_column)))
    else:
        query = query.order_by(asc(col(sort_column)))

    # Apply pagination
    query = query.offset(params.skip).limit(params.limit)
    records = session.exec(query).all()

    return BorrowRecordsPublic(data=records, count=count)


@router.get(
    "/",
    response_model=BorrowRecordsPublic,
    dependencies=[Depends(require_permission(Permission.BORROWS_READ_ALL))],
)
def list_all_borrows(
    session: SessionDep,
    _current_user: CurrentUser,
    params: BorrowQueryParams = Depends(),
) -> Any:
    """
    Get all borrow records in the library.

    Requires: borrows:read_all permission (librarian role by default)

    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (max 1000)
    - active_only: If true, only return books currently borrowed (not returned)
    - borrower_id: Filter by borrower user ID
    - book_id: Filter by book ID
    - sort: Sort field with optional - prefix for descending (default: -borrowed_at for most recent first)
    """
    # Build query
    query = select(BorrowRecord)

    # Apply active_only filter
    if params.active_only:
        query = query.where(BorrowRecord.returned_at == None)  # noqa: E711

    # Apply borrower_id filter
    if params.borrower_id:
        query = query.where(BorrowRecord.borrower_id == params.borrower_id)

    # Apply book_id filter
    if params.book_id:
        query = query.where(BorrowRecord.book_id == params.book_id)

    # Count total matching records
    count_query = select(func.count()).select_from(query.subquery())
    count = session.exec(count_query).one()

    # Apply sorting
    sort_column = {
        "borrowed_at": BorrowRecord.borrowed_at,
        "returned_at": BorrowRecord.returned_at,
    }.get(params.sort_field, BorrowRecord.borrowed_at)

    if params.is_descending:
        query = query.order_by(desc(col(sort_column)))
    else:
        query = query.order_by(asc(col(sort_column)))

    # Apply pagination
    query = query.offset(params.skip).limit(params.limit)
    records = session.exec(query).all()

    return BorrowRecordsPublic(data=records, count=count)


@router.get(
    "/{borrow_id}",
    response_model=BorrowRecordPublic,
    dependencies=[Depends(require_any_permission(
        Permission.BORROWS_READ,
        Permission.BORROWS_READ_ALL,
    ))],
)
def get_borrow_record(
    borrow_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get a specific borrow record by ID.

    Requires: borrows:read or borrows:read_all permission

    Users with borrows:read can only view their own borrow records.
    Users with borrows:read_all can view any borrow record.
    """
    from src.auth.permissions import get_user_effective_permissions

    borrow_record = session.get(BorrowRecord, borrow_id)
    if not borrow_record:
        raise HTTPException(status_code=404, detail="Borrow record not found")

    # Check access: user can view if they have read_all OR if it's their record
    user_perms = get_user_effective_permissions(current_user)
    can_read_all = Permission.BORROWS_READ_ALL in user_perms
    is_own_record = borrow_record.borrower_id == current_user.id

    if not can_read_all and not is_own_record:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own borrow records"
        )

    return borrow_record
