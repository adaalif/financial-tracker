"""
Web UI routes for the Dashboard, Receipt Scanner, History, and Settings.
Integrates with the AI mapping and unified PostgreSQL database pipeline.
"""

import uuid
from collections import defaultdict
from datetime import datetime
from fastapi import APIRouter, File, Form, Request, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.groq_processor import process_image_with_groq
from parser.receipt_parser import parse_and_validate, regex_fallback_extraction, ReceiptData
from cache.receipt_cache import receipt_cache
from utils.logger import get_logger
from database.engine import get_session
from database.models import User, Category, ReceiptTransaction, ReceiptItem, TransactionType

logger = get_logger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def get_current_user(session: AsyncSession = Depends(get_session)) -> User:
    """Simulates multi-tenant logged-in user context"""
    result = await session.exec(select(User))
    user = result.first()
    if not user:
        user = User(email="ceo@finantialtracker.local")
        session.add(user)
        await session.flush()
        
        # Add default categories
        session.add(Category(user_id=user.id, name="Food"))
        session.add(Category(user_id=user.id, name="Transport"))
        session.add(Category(user_id=user.id, name="Groceries"))
        await session.commit()
    return user


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    """Render the main dashboard overview with injected React state."""
    
    # Eagerly load items and their categories to avoid async N+1 lazy-load crashes
    query = (
        select(ReceiptTransaction)
        .where(ReceiptTransaction.user_id == user.id)
        .options(selectinload(ReceiptTransaction.items).selectinload(ReceiptItem.category))
    )
    result = await session.exec(query)
    transactions = result.unique().all()
    
    formatted_receipts = []
    for tx in transactions:
        # User requested the total to be derived rigidly from the actual line items, not the scraped parent total.
        items_payload = []
        true_total_cents = 0
        for i in tx.items:
            items_payload.append({
                "name": i.item_name, 
                "price": i.amount_cents / 100.0, 
                "category": i.category.name.lower() if i.category else "general"
            })
            true_total_cents += i.amount_cents
            
        formatted_receipts.append({
            "merchant": tx.merchant_name,
            "date": tx.created_at.strftime("%Y-%m-%d"),
            "total": true_total_cents / 100.0,
            "currency": tx.currency,
            "category": "mixed", # Default placeholder
            "items": items_payload
        })

    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html",
        context={"receipts": formatted_receipts}
    )

@router.get("/scan", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse(request=request, name="upload.html")

@router.post("/api/scan", response_class=HTMLResponse)
async def upload_receipt(
    request: Request, 
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            return templates.TemplateResponse(request=request, name="upload.html", context={"error": "No file content received."})

        logger.info("Web upload received", filename=file.filename, size=len(image_bytes))

        receipt_data = None
        raw_json_str = ""

        for attempt in range(3):
            raw_json_str, _ = await process_image_with_groq(image_bytes)
            try:
                receipt_data = parse_and_validate(raw_json_str)
                break
            except (ValueError, ValidationError) as e:
                logger.warning(f"Validation failed on attempt {attempt + 1}", error=str(e))
                if attempt == 2:
                    logger.error("All 3 LLM attempts failed. Falling back to regex.")
                    receipt_data = regex_fallback_extraction(raw_json_str)
                    break

        receipt_id = receipt_cache.generate_id()
        receipt_cache.set(receipt_id, receipt_data.model_dump())

        # Grab categories for the UI dropdowns (only active ones in history)
        cat_query = select(Category.name).join(ReceiptItem, ReceiptItem.category_id == Category.id).where(Category.user_id == user.id).distinct()
        cat_result = await session.exec(cat_query)
        category_names = cat_result.all()

        return templates.TemplateResponse(
            request=request,
            name="preview.html", 
            context={
                "receipt_id": receipt_id,
                "data": receipt_data,
                "custom_tables": category_names,
            }
        )

    except Exception as e:
        logger.error("Upload processing block failed", error=str(e), exc_info=True)
        return templates.TemplateResponse(request=request, name="upload.html", context={"error": f"Failed to process receipt: {str(e)}"})

@router.post("/confirm", response_class=HTMLResponse)
async def confirm_receipt(
    request: Request,
    receipt_id: str = Form(...),
    merchant: str = Form(""),
    date: str = Form(""),
    total: float = Form(0.0),
    currency: str = Form("IDR"),
    item_names: list[str] = Form(default=[]),
    item_prices: list[str] = Form(default=[]),
    item_categories: list[str] = Form(default=[]),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    # Handle missing date safely
    try:
        tx_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.utcnow()
    except ValueError:
        tx_date = datetime.utcnow()

    # Issue Transaction Model
    tx = ReceiptTransaction(
        user_id=user.id,
        merchant_name=merchant,
        total_amount_cents=int(total * 100),
        currency=currency,
        created_at=tx_date
    )
    session.add(tx)
    await session.flush()

    # Store dynamic items with auto-created categories
    for i in range(len(item_names)):
        name = item_names[i].strip()
        if not name:
            continue

        price_val = 0.0
        try:
            price_val = float(item_prices[i])
        except Exception:
            pass

        cat_name = item_categories[i].strip() if i < len(item_categories) else "General"
        cat_id = await resolve_category(session, user, cat_name)

        item = ReceiptItem(
            receipt_id=tx.id,
            user_id=user.id,
            category_id=cat_id,
            item_name=name,
            amount_cents=int(price_val * 100)
        )
        session.add(item)
        
    await session.commit()
    receipt_cache.delete(receipt_id)

    context_data = {
        "merchant": merchant,
        "date": date,
        "total": total,
        "currency": currency,
        "category": "Itemized" if len(item_names) > 0 else "General"
    }

    return templates.TemplateResponse(request=request, name="confirm.html", context={
        "data": context_data,
        "receipt_id": receipt_id
    })

@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    """Unified master data table -- loads ALL items across every category."""
    query = (
        select(ReceiptItem)
        .where(ReceiptItem.user_id == user.id)
        .options(selectinload(ReceiptItem.transaction), selectinload(ReceiptItem.category))
    )
    items_db = await session.exec(query)

    flattened_items = []
    for item in items_db.all():
        flattened_items.append({
            "id": item.id,
            "date": item.transaction.created_at.strftime("%Y-%m-%d"),
            "merchant": item.transaction.merchant_name,
            "category": item.category.name if item.category else "General",
            "currency": item.transaction.currency,
            "item_name": item.item_name,
            "item_price": item.amount_cents / 100.0,
        })

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"items": flattened_items},
    )


# ─── Helper: resolve or create a category by name ───
async def resolve_category(session: AsyncSession, user: User, name: str) -> int:
    """Look up a category by name (case-insensitive). Create it if it does not exist."""
    clean = name.strip()
    if not clean:
        clean = "General"

    result = await session.exec(
        select(Category).where(Category.user_id == user.id, Category.name.ilike(clean))
    )
    cat = result.first()
    if cat:
        return cat.id

    cat = Category(user_id=user.id, name=clean.capitalize())
    session.add(cat)
    await session.flush()
    return cat.id


@router.get("/add", response_class=HTMLResponse)
async def add_page(request: Request, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    """Render the manual expense entry form."""
    cat_query = select(Category.name).join(ReceiptItem, ReceiptItem.category_id == Category.id).where(Category.user_id == user.id).distinct()
    cat_result = await session.exec(cat_query)
    category_names = cat_result.all()
    return templates.TemplateResponse(request=request, name="add.html", context={"categories": category_names})


@router.post("/add", response_class=HTMLResponse)
async def add_manual_entry(
    request: Request,
    merchant: str = Form(""),
    date: str = Form(""),
    currency: str = Form("IDR"),
    item_names: list[str] = Form(default=[]),
    item_prices: list[str] = Form(default=[]),
    item_categories: list[str] = Form(default=[]),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Process the manual multi-item submission and persist to Postgres."""
    try:
        tx_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.utcnow()
    except ValueError:
        tx_date = datetime.utcnow()

    # Compute total from individual item prices
    total_cents = 0
    parsed_items = []
    for i in range(len(item_names)):
        name = item_names[i].strip()
        if not name:
            continue
        price_val = 0.0
        try:
            price_val = float(item_prices[i]) if i < len(item_prices) else 0.0
        except (ValueError, IndexError):
            pass
        cat_name = item_categories[i].strip() if i < len(item_categories) else "General"
        parsed_items.append((name, price_val, cat_name))
        total_cents += int(price_val * 100)

    tx = ReceiptTransaction(
        user_id=user.id,
        merchant_name=merchant.strip(),
        total_amount_cents=total_cents,
        currency=currency.strip() or "IDR",
        created_at=tx_date,
    )
    session.add(tx)
    await session.flush()

    for name, price_val, cat_name in parsed_items:
        cat_id = await resolve_category(session, user, cat_name)
        item = ReceiptItem(
            receipt_id=tx.id,
            user_id=user.id,
            category_id=cat_id,
            item_name=name,
            amount_cents=int(price_val * 100),
        )
        session.add(item)

    await session.commit()
    return RedirectResponse(url="/history", status_code=303)


@router.post("/delete/{item_id}")
async def delete_item(item_id: uuid.UUID, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    """Permanently delete a single ReceiptItem by ID."""
    result = await session.exec(select(ReceiptItem).where(ReceiptItem.id == item_id, ReceiptItem.user_id == user.id))
    item = result.first()
    if item:
        await session.delete(item)
        await session.commit()
    return RedirectResponse(url="/history", status_code=303)


@router.get("/edit/{item_id}", response_class=HTMLResponse)
async def edit_page(item_id: uuid.UUID, request: Request, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    """Render the edit form for an existing ReceiptItem."""
    query = select(ReceiptItem).where(ReceiptItem.id == item_id, ReceiptItem.user_id == user.id).options(selectinload(ReceiptItem.transaction), selectinload(ReceiptItem.category))
    result = await session.exec(query)
    item = result.first()
    
    if not item:
        return RedirectResponse(url="/history", status_code=303)
        
    cat_query = select(Category.name).join(ReceiptItem, ReceiptItem.category_id == Category.id).where(Category.user_id == user.id).distinct()
    cat_result = await session.exec(cat_query)
    category_names = cat_result.all()
    
    context = {
        "item": item,
        "date_str": item.transaction.created_at.strftime("%Y-%m-%d"),
        "price": item.amount_cents / 100.0,
        "categories": category_names
    }
    return templates.TemplateResponse(request=request, name="edit.html", context=context)


@router.post("/edit/{item_id}", response_class=HTMLResponse)
async def process_edit_item(
    item_id: uuid.UUID,
    request: Request,
    merchant: str = Form(""),
    date: str = Form(""),
    currency: str = Form("IDR"),
    item_name: str = Form(""),
    item_price: float = Form(0.0),
    category: str = Form("General"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user)
):
    """Process an update to an existing ReceiptItem and its parent transaction."""
    query = select(ReceiptItem).where(ReceiptItem.id == item_id, ReceiptItem.user_id == user.id).options(selectinload(ReceiptItem.transaction))
    result = await session.exec(query)
    item = result.first()
    
    if item:
        try:
            tx_date = datetime.strptime(date, "%Y-%m-%d") if date else item.transaction.created_at
        except ValueError:
            tx_date = item.transaction.created_at

        # Update parent transaction safely
        tx = item.transaction
        tx.merchant_name = merchant.strip() if merchant.strip() else tx.merchant_name
        tx.currency = currency.strip() if currency.strip() else tx.currency
        tx.created_at = tx_date
        
        # Update child item
        item.item_name = item_name.strip() if item_name.strip() else item.item_name
        item.amount_cents = int(item_price * 100)
        
        # Resolve category
        new_cat_id = await resolve_category(session, user, category)
        item.category_id = new_cat_id
        
        session.add(tx)
        session.add(item)
        await session.commit()

    return RedirectResponse(url="/history", status_code=303)
