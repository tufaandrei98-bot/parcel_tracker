# Parcel Tracker API

## 1. Scop

Un API simplu pentru urmarirea coletelor. Fara frontend. Persistenta in SQLite.

## 2. Obiective

* CRUD (Create Read Update Delete) de baza pentru clienti si colete
* Scan timeline pentru fiecare colet
* Validari de status
* Filtrari, sortare, paginare
* Documentatie auto in `/docs` (FastAPI)
* Rulare locala pe `localhost:8000`

## 3. Stack tehnic

* Limbaj: Python 3.11+
* Framework API: FastAPI
* ORM: SQLAlchemy 2.x (sync)
* DB: SQLite (fisier local)

## 4. Model de date

### 4.1 Tabele

* customers

  * id (PK, int)
  * name (str, 1..80)
  * phone (str, optional)
  * created_at (datetime)

* parcels

  * id (PK, int)
  * tracking_code (str, unic, ex: `PRC-2025-000001`)
  * customer_id (FK -> customers.id)
  * status (enum: new, pickup, in_transit, out_for_delivery, delivered, return)
  * weight_kg (float >= 0)
  * addr_from (str)
  * addr_to (str)
  * created_at (datetime)
  * delivered_at (datetime, optional)

* scans

  * id (PK, int)
  * parcel_id (FK -> parcels.id)
  * ts (datetime)
  * location (str)
  * type (enum: pickup, in_transit, out_for_delivery, delivered, return)
  * note (str, optional)

### 4.2 Reguli de status (state machine)

* Tranzitii permise:

  * new -> pickup
  * pickup -> in_transit
  * in_transit -> out_for_delivery | return
  * out_for_delivery -> delivered | return
  * delivered -> [final]
  * return -> [final]


* Dupa `delivered` sau `return` nu se mai pot adauga scan-uri.
* `delivered_at` se seteaza la primul eveniment `delivered`.

## 5. API Endpoints (MVP)

### 5.1 Health

* GET `/health` -> `{"status":"ok"}`

### 5.2 Customers

* POST `/customers`

  * body: `{ "name": "ACME", "phone": "0712345678" }`
  * 201 -> `{ "id": 1, "name": "...", "phone": "...", "created_at": "..." }`
  

* GET `/customers?search=&page=1&size=20&sort=created_at,desc`
  * 200 -> lista de clienti


* GET `/customers/{id}`
* PUT `/customers/{id}` -> update la customer existent
* DELETE `/customers/{id}` -> Response status: 204

### 5.3 Parcels

* POST `/parcels`

  * body:

    ```json
    {
      "customer_id": 1,
      "weight_kg": 2.5,
      "addr_from": "Str A 1, Oras X",
      "addr_to": "Str B 2, Oras Y"
    }
    ```
  * efect: genereaza `tracking_code`, seteaza `status=new`
  * 201 -> parcel (fara scan-uri)


* GET `/parcels?status=&customer_id=&q=&page=1&size=20&sort=created_at,desc`
  * filtre:
    * `status` in {new,pickup,in_transit,out_for_delivery,delivered,return}
    * `q` cauta in tracking_code si adrese


* GET `/parcels/{tracking_code}`
  * 200 -> parcel + sumar (fara scan list, vezi timeline)


* GET `/parcels/{tracking_code}/timeline`
  * 200 -> `{ "tracking_code": "...", "events": [ { "ts": "...", "type": "...", "location": "...", "note": "" } ] }`


### 5.4 Scans

* POST `/parcels/{tracking_code}/scans`
  * body:
    ```json
    { "type": "in_transit", "location": "Hub Nord", "ts": "2025-11-02T10:00:00Z", "note": "plecare" }
    ```
  * validari:
    * `type` tranzitie legala fata de `status` curent
    * daca `type=delivered` seteaza `delivered_at` si `status=delivered`
  * 201 -> scan creat


* GET `/parcels/{tracking_code}/scans`
  * 200 -> lista scan-uri ordonate crescator dupa `ts`

### 5.5 Raport simplu

* GET `/reports/parcels-by-status?from=2025-11-01&to=2025-11-30`

  * 200 -> 
  ```json
  { 
    "new": 3, 
    "pickup": 5, 
    "in_transit": 12, 
    "out_for_delivery": 4,
    "delivered": 20,
    "return": 1
  }
  ```

## 6. Conventii API

* Raspunsuri eroare: format JSON `{ "detail": "message" }`
* Status codes:
  * 200 OK, 201 Created, 204 No Content
  * 400 Bad Request (validari)
  * 404 Not Found
  * 409 Conflict (ex: tracking_code duplicat, tranzitie ilegala)
* Paginare: `page` 1-based, `size` max 100
* Sort: `sort=field,asc|desc` (default `created_at,desc`)
* Timestamps: ISO 8601 UTC (`2025-11-02T09:10:58Z` <- aici `Z` ne informeaza de timezone)

## 7. Validari cheie

* `weight_kg >= 0`
* `name` non-empty
* `tracking_code` unic
* Tranzitii status conforme sectiunii 4.2
* Dupa `delivered`/`return` endpoint-ul de scan va returna 409

## 8. Securitate (MVP)

* Fara auth in MVP

## 9. Operare si mediu

### 9.1 Rulare locala

* Git clone
* Proiect now de pycharm
* Python venv 3.11
* `pip install -r requirements.txt`
* `fastapi dev app/main.py` <- pentru debugging si reload instant
* `fastapi run app/main.py` <- production command
* Docs: `http://127.0.0.1:8000/docs`

### 9.2 Seed data (optional)

* Script simplu care adauga 1-2 customers si 2-3 parcels

### 9.3 Structura directoare propusa

```properties
parcel-tracker/
  app/
    __init__.py
    main.py          # creeaza FastAPI, include routere, startup
    db.py            # engine, SessionLocal, Base, init_db()
    models.py        # clase ORM (Customer, Parcel, Scan)
    schemas.py       # Pydantic I/O (Create/Update/Out)
    deps.py          # dependency get_db() -> Session
    routers/
      __init__.py
      customers.py   # endpoints pentru clienti
      parcels.py     # endpoints pentru colete
      scans.py       # endpoints pentru scan-uri
      reports.py     # endpoint raport sumar
    services/
      __init__.py
      parcels.py     # reguli de status si tranzitii
    utils/
      __init__.py
      codes.py       # generator tracking_code
  requirements.txt
  README.md
```

## 10. Flux (MVP)

Scop: operatorul unui mic curier vrea sa introduca clienti si colete, sa le urmareasca traseul prin scan-uri si sa vada un sumar al livrarilor. Fara frontend. Toate actiunile se fac prin API. Timpul este UTC ISO8601.

### 10.1. Creeaza client

Actor: operator backoffice.
Intent: inregistreaza un client pentru care vor fi trimise colete.
Validari: `name` non-empty, `phone` optional dar valid.

Request:

```http
POST /customers
Content-Type: application/json
```

```json
{ "name": "ACME SRL", "phone": "+40 712 345 678" }
```

Response 201:

```json
{
  "id": 1,
  "name": "ACME SRL",
  "phone": "+40 712 345 678",
  "created_at": "2025-11-02T10:00:00Z"
}
```

Eroare 400 (exemplu):

```json
{ "detail": "name must not be empty" }
```

### 10.2. Creeaza colet pentru client

Actor: operator backoffice.
Intent: adauga un colet ce va intra in fluxul logistic.
Efecte: genereaza `tracking_code` unic, seteaza `status=new`.

Request:

```http
POST /parcels
Content-Type: application/json
```

```json
{
  "customer_id": 1,
  "weight_kg": 2.5,
  "addr_from": "Depozit Nord, Strada A 1, Oras X",
  "addr_to": "Ion Pop, Strada B 2, Oras Y"
}
```

Response 201:

```json
{
  "id": 101,
  "tracking_code": "PRC-2025-000001",
  "customer_id": 1,
  "status": "new",
  "weight_kg": 2.5,
  "addr_from": "Depozit Nord, Strada A 1, Oras X",
  "addr_to": "Ion Pop, Strada B 2, Oras Y",
  "created_at": "2025-11-02T10:05:00Z",
  "delivered_at": null
}
```

Eroare 404:

```json
{ "detail": "customer not found" }
```

### 10.3. Adauga scan-uri pe traseu

Actor: lucratorii din hub/curierii (prin aplicatia interna).
Intent: marcheaza progresul fizic al coletului.
Regula: tranzitii legale doar (vezi state machine). Dupa `delivered`/`return` nu mai accepta scan.

3.1 Pickup din depozit

```http
POST /parcels/PRC-2025-000001/scans
Content-Type: application/json
```

```json
{
  "type": "pickup",
  "location": "Depozit Nord",
  "ts": "2025-11-02T11:00:00Z",
  "note": "preluat de la client"
}
```

Response 201:

```json
{
  "id": 5001,
  "parcel_id": 101,
  "type": "pickup",
  "location": "Depozit Nord",
  "ts": "2025-11-02T11:00:00Z",
  "note": "preluat de la client"
}
```

3.2 Tranzit intre hub-uri

```json
{ "type": "in_transit", "location": "Hub Central", "ts": "2025-11-02T14:30:00Z" }
```

3.3 Iesire la livrare

```json
{ "type": "out_for_delivery", "location": "Oras Y", "ts": "2025-11-03T07:45:00Z" }
```

3.4 Livrat
Regula: seteaza `delivered_at` la prima marcare `delivered`.

```json
{ "type": "delivered", "location": "Oras Y", "ts": "2025-11-03T09:10:00Z", "note": "predat destinatarului" }
```

Eroare 409 la tranzitie ilegala:

```json
{ "detail": "illegal status transition: in_transit -> delivered" }
```

Eroare 409 dupa finalizare:

```json
{ "detail": "parcel is finalized, scans are not allowed" }
```

### 10.4. Vezi istoricul (timeline)

Actor: suport clienti sau operator.
Intent: afiseaza toate evenimentele pentru comunicare cu clientul final.

Request:

```http
GET /parcels/PRC-2025-000001/timeline
```

Response 200:

```json
{
  "tracking_code": "PRC-2025-000001",
  "events": [
    { "ts": "2025-11-02T11:00:00Z", "type": "pickup", "location": "Depozit Nord", "note": "preluat de la client" },
    { "ts": "2025-11-02T14:30:00Z", "type": "in_transit", "location": "Hub Central", "note": null },
    { "ts": "2025-11-03T07:45:00Z", "type": "out_for_delivery", "location": "Oras Y", "note": null },
    { "ts": "2025-11-03T09:10:00Z", "type": "delivered", "location": "Oras Y", "note": "predat destinatarului" }
  ]
}
```

Eroare 404:

```json
{ "detail": "parcel not found" }
```

### 10.5. Sumar operatiuni (raport)

Actor: manager operatiuni.
Intent: intelege volumul pe status intr-un interval dat pentru planificare si SLA.

Request:

```http
GET /reports/parcels-by-status?from=2025-11-01&to=2025-11-03
```

Response 200:

```json
{
  "new": 4,
  "pickup": 6,
  "in_transit": 12,
  "out_for_delivery": 5,
  "delivered": 20,
  "return": 1
}
```

Eroare 400 (interval invalid):

```json
{ "detail": "from must be <= to" }
```

---

## 11. Taskuri de Dezvoltare Sugerate (backlog)


### Ușor
#### 1. Filtrare multi-status pentru colete

   * Descriere: Permiteți endpoint-ului GET /parcels să accepte o listă de statusuri pentru filtrare (de ex. status=in_transit,out_for_delivery). În prezent, acceptă doar un singur status.
   * Indicii:
       * Fișier: app/routers/parcels.py
       * Funcție: list_parcels
       * Logic:
           1. Modificați parametrul status: `Optional[str]` pentru a accepta o listă de string-uri, folosind Query de la FastAPI: status: `Optional[List[str]] = Query(None)`.
           2. FastAPI va transforma automat o interogare de tipul `?status=val1&status=val2` într-o listă Python.
           3. Înlocuiți condiția `models.Parcel.status == status` cu `models.Parcel.status.in_(status)`, unde status va fi acum lista de statusuri.

#### 2. Validare număr de telefon pentru client

   * Descriere: Adăugați o validare simplă pentru câmpul phone la crearea și actualizarea unui client. Formatul acceptat ar trebui să fie un șir de 7-20 de caractere care poate conține cifre, spații, +, (, ).
   * Indicii:
       * Fișier: `app/schemas.py`
       * Clase: `CustomerCreate` și `CustomerUpdate`
       * Logic:
           1. Folosiți `Field` din Pydantic pentru a adăuga o expresie regulată (regex) la câmpul phone.
           2. Adăugați argumentul pattern la Field: `pattern=r'^[0-9 +()-]{7,20}$'`
           3. Pydantic va returna automat o eroare de validare (cod 422) dacă formatul nu corespunde.

#### 3. Paginare și sortare pentru scan-uri

   * Descriere: Endpoint-ul `GET /parcels/{tracking_code}/scans` are o implementare simplistă de paginare și sortare. Înlocuiți-o cu o logică robustă, similară cu cea de la `list_parcels`, folosind SQLAlchemy.
   * Indicii:
       * Fișier: `app/routers/scans.py`
       * Funcție: `list_scans()`
       * Logic:
           1. În loc să preluați `parcel.scans` și să sortați în memorie, creați o interogare `select(models.Scan)`
           2. Filtrați după parcel_id: `stmt = select(models.Scan).where(models.Scan.parcel_id == parcel.id)`
           3. Refolosiți funcțiile `parse_sort` și `apply_sort` (le puteți importa din customers.py sau le puteți muta într-un fișier utilitar) pentru a aplica sortarea pe câmpurile Scan (ex: ts, location).
           4. Aplicați paginarea cu `.offset((page - 1) * size).limit(size)`
           5. Executați interogarea și returnați rezultatele.

---

### Mediu

#### 1. Generare configurabilă pentru tracking_code

   * Descriere: Faceți formatul `tracking_code` mai flexibil. În prezent, este parțial hardcodat. Permiteți configurarea prefixului (ex: COR) și lungimea secvenței numerice prin variabile de mediu.
   * Indicii:
       * Fișiere relevante: `app/utils/codes.py`, `app/services/parcels.py`. Puteți crea și un fișier nou `app/config.py`
       * Logic:
           1. Creați o clasă de setări Pydantic în `app/config.py` care încarcă variabile de mediu (ex: `TRACKING_CODE_PREFIX`, `TRACKING_CODE_PADDING`).
           2. În `app/utils/codes.py`, modificați funcția de generare pentru a utiliza aceste setări.
           3. Logica trebuie să preia ultimul ID al coletului din baza de date și să formateze noul cod pe baza setărilor (ex: `f"{prefix}-{next_id:0{padding}d}"`).
           4. Asigurați-vă că serviciul `create_parcel` din `app/services/parcels.py` folosește noua logică de generare.

#### 2. Actualizare parțială pentru colete

   * Descriere: Implementați un endpoint `PATCH /parcels/{tracking_code}` pentru a permite actualizarea adreselor (`addr_from`, `addr_to`) și a greutății (`weight_kg`). Actualizarea trebuie blocată dacă coletul are un status final
     (`delivered` sau `return`).
   * Indicii:
       * Fișier: `app/routers/parcels.py`
       * Schema: Folosiți schema `ParcelUpdate` din `app/schemas.py`
       * Logic:
           1. Creați un nou endpoint `PATCH` în parcels.py.
           2. Găsiți coletul după tracking_code.
           3. Verificați dacă statusul coletului este delivered sau return. Dacă da, returnați un `HTTPException` cu status `409 Conflict`.
           4. Actualizați câmpurile specificate în payload pe obiectul parcel. Folosiți `payload.dict(exclude_unset=True)` pentru a itera doar peste câmpurile trimise efectiv în request.
           5. Salvați modificările (`db.commit()`) și returnați coletul actualizat.

  ---

### Dificil

#### 1. Implementare API Key pentru securitate

   * Descriere: Adăugați un mecanism simplu de securitate bazat pe un API key. Toate request-urile (cu excepția `/health` și `/docs`) trebuie să includă un header `X-API-Key` cu o valoare predefinită.
   * Indicii:
       * Fișiere: `app/main.py`, și un nou fișier `app/auth.py`.
       * Logic:
           1. Definiți o variabilă de mediu pentru cheia API (ex: `API_KEY`).
           2. În `app/auth.py`, creați o funcție dependency (`get_api_key`) care extrage header-ul `X-API-Key` folosind `APIKeyHeader(name="X-API-Key")`
           3. Funcția trebuie să compare valoarea primită cu cea din variabila de mediu. Dacă lipsește sau este invalidă, aruncați `HTTPException(401, "Invalid API Key")`
           4. În `app/main.py`, adăugați această dependență la nivel global, folosind `app = FastAPI(dependencies=[Depends(get_api_key)])`
           5. Pentru a exclude anumite rute, puteți aplica dependența la nivel de `APIRouter` pentru fiecare modul din `routers/`, în loc de a o aplica global pe app.

#### 2. Teste unitare pentru serviciul de tranziții

   * Descriere: Scrieți teste unitare pentru serviciul `apply_scan_transition` din `app/services/parcels.py` pentru a vă asigura că regulile de tranziție a stărilor sunt respectate corect.
   * Indicii:
       * Tooling: `pytest`. Va trebui să îl adăugați în `requirements.txt`
       * Fișiere: Creați un director `tests/` la rădăcina proiectului și în el un fișier `tests/test_parcel_service.py`
       * Logic:
           1. Configurați o bază de date de testare (poate fi in-memory SQLite).
           2. Folosind `pytest`, scrieți funcții de test pentru fiecare tranziție validă (ex: `test_transition_new_to_pickup`).
           3. În fiecare test, creați un obiect `Parcel` cu o stare inițială, apelați `apply_scan_transition` și verificați (`assert`) că starea finală este cea corectă.
           4. Scrieți teste și pentru tranzițiile ilegale (ex: `new` -> `in_transit`) și verificați că se aruncă excepția corectă folosind `pytest.raises(ValueError)`.

## 12. Criterii de evaluare

* Corectitudine HTTP status codes si body
* Validari si mesaje de eroare clare
* Respectarea tranzitiilor de status
* Filtre, paginare, sort functionale
* Structura proiectului si README cu pasi de rulare
* Calitatea codului: separare concern-uri (routers / services / db)

## 13. Roadmap ulterior

* Autentificare reala cu JWT
* Postgres in loc de SQLite
* Observabilitate: logging structurat, request ID, simple metrics
* Frontend mic pentru vizualizare timeline

## 14. Tests

### Setup
```shell
pip install pytest
```

### Run all tests
```shell
pytest -q
```

### Run a single file or test
```shell
pytest -q tests/test_codes.py::test_build_tracking_code_basic
```

### With coverage (optional)
```shell
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```