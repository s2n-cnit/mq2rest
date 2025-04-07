from typing import Dict, List

from fastapi import FastAPI, HTTPException
from model import Book

app = FastAPI()

books: Dict[int, Book] = {}  # In-memory "database" (for demonstration)
book_id_counter = 1


@app.post("/books/", response_model=Book, status_code=201)
async def create_book(book: Book):
    global book_id_counter
    book_id = book_id_counter
    books[book_id] = book
    book_id_counter += 1
    return book


@app.get("/books/{book_id}", response_model=Book)
async def read_book(book_id: int):
    if book_id not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    return books[book_id]


@app.get("/books/", response_model=List[Book])
async def read_books():
    return list(books.values())


@app.put("/books/{book_id}", response_model=Book)
async def update_book(book_id: int, updated_book: Book):
    if book_id not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    books[book_id] = updated_book
    return updated_book


@app.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: int):
    if book_id not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    del books[book_id]
