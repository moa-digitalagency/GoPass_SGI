# SGI-GP - Référence API REST

Cette documentation détaille les endpoints de l'API REST de SGI-GP, utilisée par l'application mobile (Scanner/POS) et le frontend web.

**Base URL :** `/api`
**Authentification :** Cookie de Session (Flask-Login). Tous les appels nécessitent d'être authentifié.

---

## 1. Utilisateur & Session

### `GET /api/me`
Retourne les informations de l'utilisateur connecté.
*   **Réponse (200 OK) :**
    ```json
    {
        "id": 1,
        "username": "agent01",
        "role": "agent",
        "location": "FIH",
        "first_name": "Jean",
        "last_name": "Dupont"
    }
    ```

---

## 2. Vols & Aéroports

### `GET /api/airports`
Liste les aéroports disponibles (Codes IATA).
*   **Réponse (200 OK) :**
    ```json
    [
        {"code": "FIH", "name": "N'Djili International"},
        {"code": "FBM", "name": "Lubumbashi International"}
    ]
    ```

### `GET /api/flights`
Recherche des vols pour une date et un aéroport donnés.
*   **Paramètres :**
    *   `airport_code` (Requis) : Code IATA (ex: FIH).
    *   `date` (Optionnel) : Date YYYY-MM-DD.
*   **Réponse (200 OK) :**
    ```json
    [
        {
            "id": 101,
            "flight_number": "AF123",
            "airline": "Air France",
            "departure_time": "2023-10-27T20:00:00",
            "status": "scheduled"
        }
    ]
    ```

### `POST /api/external/verify-flight`
Vérifie l'existence d'un vol auprès de l'API globale (AviationStack) et retourne son prix théorique.
*   **Body :**
    ```json
    {
        "flight_number": "SN351",
        "flight_date": "2023-10-27"
    }
    ```
*   **Réponse (200 OK) :**
    ```json
    {
        "found": true,
        "flight_data": { ... },
        "pricing": {
            "type": "INTERNATIONAL",
            "amount": 50.0,
            "currency": "USD"
        }
    }
    ```

---

## 3. Opérations Terrain (Scanner & POS)

### `POST /api/scan`
Valide un GoPass (QR Code) pour un vol spécifique.
*   **Body :**
    ```json
    {
        "token": "hash_sha256_du_qr_code",
        "flight_id": 101,
        "location": "GATE-01"
    }
    ```
*   **Réponse (200 OK - Succès) :**
    ```json
    {
        "status": "success",
        "code": "VALID",
        "message": "VALIDE",
        "color": "green",
        "data": {
            "passenger": "M. TEST",
            "passport": "A1234567"
        }
    }
    ```
*   **Réponse (Erreur - Déjà Scanné) :**
    ```json
    {
        "status": "error",
        "code": "ALREADY_SCANNED",
        "color": "red",
        "data": {
            "original_scan": {
                "scan_date": "2023-10-27 18:30:00",
                "scanned_by": "agent02"
            }
        }
    }
    ```

### `POST /api/sales/cash-drop`
Enregistre un dépôt d'espèces (Clôture de caisse agent).
*   **Body :**
    ```json
    {
        "agent_id": 1,
        "amount": 5000.0,
        "notes": "Fermeture poste 1"
    }
    ```
*   **Réponse (200 OK) :** `{"message": "Deposit recorded", "id": 55}`

---

## 4. Administration

### `POST /api/settings/general`
Met à jour la configuration globale (nécessite rôle Admin).
*   **Body :** `{"region": "CD", "tax_rate": 0.16}`
*   **Réponse :** `{"message": "Paramètres mis à jour"}`

### `POST /api/payment/toggle/<provider>`
Active ou désactive une passerelle de paiement (ex: STRIPE, MPESA).
*   **Paramètres URL :** `provider` (STRIPE, MPESA, ORANGE).
