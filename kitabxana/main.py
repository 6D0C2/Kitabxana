# ============================================================
# KITAB İDARƏETMƏ SİSTEMİ - FastAPI Tətbiqi
# Bu fayl bütün API endpoint-ləri və konfiqurasiyanı ehtiva edir
# ============================================================

from fastapi import FastAPI, HTTPException  # FastAPI əsas kitabxana
from fastapi.staticfiles import StaticFiles  # Statik faylları (HTML, CSS, JS) serve etmək üçün
from fastapi.responses import FileResponse   # HTML faylını cavab olaraq göndərmək üçün
from pydantic import BaseModel               # Məlumat modelini doğrulamaq üçün
from typing import Optional                  # İstəyə bağlı sahələr üçün
import json                                  # JSON faylı oxumaq/yazmaq üçün
import os                                    # Fayl yolu əməliyyatları üçün

# ──────────────────────────────────────────────
# FastAPI tətbiqini yaradırıq
# title, description və version Swagger UI-də görünəcək
# ──────────────────────────────────────────────
app = FastAPI(
    title="Kitab İdarəetmə API",
    description="Kitabları əlavə et, oxu, yenilə və sil",
    version="1.0.0"
)

# ──────────────────────────────────────────────
# Statik faylların qovluğunu qeydiyyata alırıq
# Brauzer buradan CSS, JS və HTML fayllarını yükləyəcək
# ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ──────────────────────────────────────────────
# Məlumat saxlama faylının yolu
# Kitablar bu JSON faylında saxlanılacaq
# ──────────────────────────────────────────────
DATA_FILE = "books.json"


# ──────────────────────────────────────────────
# Kitab məlumat modeli (Pydantic ilə)
# Hər kitabın hansı sahələri olacağını burada təyin edirik
# ──────────────────────────────────────────────
class Book(BaseModel):
    title: str                    # Kitabın adı (məcburi)
    author: str                   # Müəllif adı (məcburi)
    year: int                     # Nəşr ili (məcburi)
    genre: Optional[str] = None   # Janr (istəyə bağlı)
    description: Optional[str] = None  # Qısa təsvir (istəyə bağlı)


# ──────────────────────────────────────────────
# Yeniləmə modeli - bütün sahələr istəyə bağlıdır
# Yalnız göndərilən sahələr yenilənəcək
# ──────────────────────────────────────────────
class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None


# ════════════════════════════════════════════════
# YARDIMCI FUNKSİYALAR - Fayl əməliyyatları
# ════════════════════════════════════════════════

def load_books() -> dict:
    """
    JSON faylından kitabları oxuyur.
    Əgər fayl yoxdursa boş dict qaytarır.
    """
    if not os.path.exists(DATA_FILE):
        return {}  # Fayl yoxdursa boş sözlük qaytar
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)  # JSON faylını oxu və Python dict-ə çevir


def save_books(books: dict) -> None:
    """
    Kitabları JSON faylına yazır.
    ensure_ascii=False Azərbaycan hərflərini düzgün saxlayır.
    """
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


def get_next_id(books: dict) -> int:
    """
    Yeni kitab üçün unikal ID yaradır.
    Mövcud ən böyük ID-yə 1 əlavə edir.
    """
    if not books:
        return 1  # Kitab yoxdursa ID-ni 1-dən başlat
    return max(int(k) for k in books.keys()) + 1


# ════════════════════════════════════════════════
# API ENDPOINT-LƏRİ
# ════════════════════════════════════════════════

# ──────────────────────────────────────────────
# 1. Ana Səhifə - HTML interfeysi qaytarır
# Brauzer bu URL-ə daxil olduqda UI yüklənir
# ──────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse("static/index.html")


# ──────────────────────────────────────────────
# 2. Bütün Kitabları Göstər (GET /books)
# Bütün kitabların siyahısını səniyəlik sıra ilə qaytarır
# ──────────────────────────────────────────────
@app.get("/books")
def get_all_books():
    """Bütün kitabların siyahısını qaytarır"""
    books = load_books()  # Fayldan kitabları yüklə
    # Dict-i list-ə çevir ki, JSON cavabı daha rahat olsun
    return [{"id": int(k), **v} for k, v in books.items()]


# ──────────────────────────────────────────────
# 3. Tək Kitab Göstər (GET /books/{id})
# Verilən ID-yə uyğun kitabın məlumatlarını qaytarır
# ──────────────────────────────────────────────
@app.get("/books/{book_id}")
def get_book(book_id: int):
    """ID-yə görə tək kitabın məlumatlarını qaytarır"""
    books = load_books()
    key = str(book_id)  # Dict açarları string olduğu üçün çeviririk

    if key not in books:
        # Kitab tapılmadıqda 404 xətası göndər
        raise HTTPException(status_code=404, detail=f"ID={book_id} olan kitab tapılmadı")

    return {"id": book_id, **books[key]}  # ID-ni məlumata əlavə edərək qaytar


# ──────────────────────────────────────────────
# 4. Yeni Kitab Əlavə Et (POST /books)
# Göndərilən məlumatlarla yeni kitab yaradır
# ──────────────────────────────────────────────
@app.post("/books", status_code=201)
def create_book(book: Book):
    """Yeni kitab yaradır və 201 status kodu ilə qaytarır"""
    books = load_books()
    new_id = get_next_id(books)       # Yeni unikal ID al
    books[str(new_id)] = book.dict()  # Kitabı sözlüyə əlavə et
    save_books(books)                 # Faylı yenilə

    return {"message": "Kitab uğurla əlavə edildi", "id": new_id, **book.dict()}


# ──────────────────────────────────────────────
# 5. Kitabı Yenilə (PUT /books/{id})
# Yalnız göndərilən sahələri yeniləyir (qismən yeniləmə)
# ──────────────────────────────────────────────
@app.put("/books/{book_id}")
def update_book(book_id: int, book_update: BookUpdate):
    """Mövcud kitabın məlumatlarını yeniləyir"""
    books = load_books()
    key = str(book_id)

    if key not in books:
        raise HTTPException(status_code=404, detail=f"ID={book_id} olan kitab tapılmadı")

    # Mövcud kitabı al
    existing = books[key]

    # Yalnız None olmayan sahələri yenilə (göndərilən sahələr)
    update_data = {k: v for k, v in book_update.dict().items() if v is not None}
    existing.update(update_data)  # Köhnə məlumatların üzərinə yaz

    books[key] = existing
    save_books(books)  # Dəyişiklikləri faylda saxla

    return {"message": "Kitab uğurla yeniləndi", "id": book_id, **existing}


# ──────────────────────────────────────────────
# 6. Kitabı Sil (DELETE /books/{id})
# Verilən ID-yə uyğun kitabı silir
# ──────────────────────────────────────────────
@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    """Kitabı verilənlər bazasından silir"""
    books = load_books()
    key = str(book_id)

    if key not in books:
        raise HTTPException(status_code=404, detail=f"ID={book_id} olan kitab tapılmadı")

    deleted_book = books.pop(key)  # Kitabı sil və məlumatını saxla
    save_books(books)              # Dəyişiklikləri faylda yenilə

    return {"message": "Kitab uğurla silindi", "deleted": {"id": book_id, **deleted_book}}
