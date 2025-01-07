import requests

BASE_URL = "http://localhost:8080/librairy/books"

def test_get_all_books():
    """Test pour récupérer tous les livres"""
    response = requests.get(BASE_URL)
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Vérifie que la réponse est une liste

def test_create_book():
    """Test pour créer un nouveau livre"""
    new_book = {
        "titre": "Le Petit Prince",
        "auteur": "Antoine de Saint-Exupéry",
        "price": 10.99
    }
    response = requests.post(BASE_URL, json=new_book)
    assert response.status_code == 204  # Vérifie que l'ajout a été réussi

    # Vérifie que le livre a été ajouté
    all_books = requests.get(BASE_URL).json()
    assert any(book["titre"] == "Le Petit Prince" for book in all_books)

def test_update_book():
    """Test pour mettre à jour un livre existant"""
    # Créer un livre
    new_book = {
        "titre": "Original Title",
        "auteur": "Original Author",
        "price": 20.0
    }
    create_response = requests.post(BASE_URL, json=new_book)
    assert create_response.status_code == 204

    # Récupérer l'ID du livre créé
    all_books = requests.get(BASE_URL).json()
    created_book = next(book for book in all_books if book["titre"] == "Original Title")
    book_id = created_book["id"]

    # Mettre à jour le livre
    updated_book = {
        "titre": "Updated Title",
        "auteur": "Updated Author",
        "price": 25.0
    }
    update_response = requests.patch(f"{BASE_URL}/{book_id}", json=updated_book)
    assert update_response.status_code == 204

    # Vérifie que le livre a été mis à jour
    updated_books = requests.get(BASE_URL).json()
    updated_book_in_db = next(book for book in updated_books if book["id"] == book_id)
    assert updated_book_in_db["titre"] == "Updated Title"
    assert updated_book_in_db["auteur"] == "Updated Author"

def test_delete_book():
    """Test pour supprimer un livre"""
    # Créer un livre
    new_book = {
        "titre": "Book to Delete",
        "auteur": "Author",
        "price": 15.0
    }
    create_response = requests.post(BASE_URL, json=new_book)
    assert create_response.status_code == 204

    # Récupérer l'ID du livre créé
    all_books = requests.get(BASE_URL).json()
    created_book = next(book for book in all_books if book["titre"] == "Book to Delete")
    book_id = created_book["id"]

    # Supprimer le livre
    delete_response = requests.delete(f"{BASE_URL}/{book_id}")
    assert delete_response.status_code == 204

    # Vérifie que le livre a été supprimé
    updated_books = requests.get(BASE_URL).json()
    assert not any(book["id"] == book_id for book in updated_books)
