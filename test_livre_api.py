import requests

BASE_URL = "http://localhost:8080/librairy/books"

def test_get_all_books():
    """Test pour récupérer tous les livres"""
    response = requests.get(BASE_URL)
    assert response.status_code == 200, "La commande de récupération a échoué"
    assert isinstance(response.json(), list), "Le résultat n'est pas une liste"

def test_create_book():
    """Test pour créer un nouveau livre"""
    new_book = {
        "titre": "Le Petit Prince",
        "auteur": "Antoine de Saint-Exupéry",
        "price": 10.99
    }
    response = requests.post(BASE_URL, json=new_book)
    assert response.status_code == 204, "La commande de création a échoué"

    # Vérifie que le livre a été ajouté
    all_books = requests.get(BASE_URL).json()
    assert any(book["titre"] == "Le Petit Prince" for book in all_books), "Le livre n'a pas été ajouté dans la base de données"

def test_update_book():
    """Test pour mettre à jour un livre existant"""
    # Créer un livre
    new_book = {
        "titre": "Original Title",
        "auteur": "Original Author",
        "price": 20.0
    }
    create_response = requests.post(BASE_URL, json=new_book)
    assert create_response.status_code == 204, "La création du livre a échoué"

    # Récupérer l'ID du livre créé
    all_books = requests.get(BASE_URL).json()
    created_book = next(book for book in all_books if book["titre"] == "Original Title")
    book_id = created_book["id"]

    # Mettre à jour le livre
    updated_book = {
        "titre": "Update Title",
        "auteur": "Updated Author",
        "price": 25.0
    }
    update_response = requests.patch(f"{BASE_URL}/{book_id}", json=updated_book)
    assert update_response.status_code == 204, "La commande de mise à jour a échoué"

    # Vérifie que le livre a été mis à jour
    updated_books = requests.get(BASE_URL).json()
    updated_book_in_db = next(book for book in updated_books if book["id"] == book_id)
    assert updated_book_in_db["titre"] == "Updated Title" and updated_book_in_db["auteur"] == "Updated Author", "Le livre n'a pas été mis à jour correctement"

def test_delete_book():
    """Test pour supprimer un livre"""
    # Créer un livre
    new_book = {
        "titre": "Book to Delete",
        "auteur": "Author",
        "price": 15.0
    }
    create_response = requests.post(BASE_URL, json=new_book)
    assert create_response.status_code == 204, "La création du livre a échoué"

    # Récupérer l'ID du livre créé
    all_books = requests.get(BASE_URL).json()
    created_book = next(book for book in all_books if book["titre"] == "Book to Delete")
    book_id = created_book["id"]

    # Supprimer le livre
    delete_response = requests.delete(f"{BASE_URL}/{book_id}")
    assert delete_response.status_code == 204, "La commande de suppression a échoué"

    # Vérifie que le livre a été supprimé
    updated_books = requests.get(BASE_URL).json()
    assert not any(book["id"] == book_id for book in updated_books), "Le livre est toujours présent dans la base de données"

def run_tests():
    test_get_all_books()
    test_create_book()
    test_update_book()
    test_delete_book()

if __name__ == "__main__":
    try:
        run_tests()
        print("Tous les tests ont réussi !")
    except AssertionError as e:
        print("Test failed:", e)