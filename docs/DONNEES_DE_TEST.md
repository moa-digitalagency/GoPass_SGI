# Données de Test & QA (Démo)

Ce document répertorie les identifiants et données à utiliser pour valider le parcours d'achat E-GoPass et simuler les paiements.

## 1. Identifiants Super Admin (Démo Locale)
* **Email :** (Celui configuré dans ton .env local, ex: `admin@gopass.demo`)
* **Mot de passe :** (Celui configuré dans ton .env local)
* *Note : Rappel de configurer ces variables dans le .env avant le premier lancement.*

## 2. Simulation Paiement Carte Bancaire (VISA/Mastercard)
| Scénario | Numéro de Carte | Date Exp | CVV | Résultat Attendu |
| :--- | :--- | :--- | :--- | :--- |
| **Paiement Validé** | `4242 4242 4242 4242` | 12/28 | 123 | ✅ Génération du QR Code |
| **Solde Insuffisant** | `4000 0000 0000 0000` | 12/28 | 123 | ❌ Erreur "Refus Bancaire" |
| **Carte Expirée** | `4242 4242 4242 4242` | 01/20 | 123 | ❌ Erreur "Carte Invalide" |

## 3. Simulation Paiement Mobile Money (M-Pesa / Airtel / Orange)
| Scénario | Numéro Téléphone | Opérateur | Résultat Attendu |
| :--- | :--- | :--- | :--- |
| **Paiement Validé** | `099 00 00 000` | Tous | ✅ Génération du QR Code |
| **Échec Technique** | `099 99 99 999` | Tous | ❌ Erreur "Timeout Opérateur" |

## 4. Données de Vol (Pour test validation API)
* **Vol International :** `AF123` (Simulation API : Départ FIH -> Arrivée CDG) -> Prix attendu : **55.00$**
* **Vol Domestique :** `CAA001` (Simulation API : Départ FIH -> Arrivée FBM) -> Prix attendu : **15.00$**
