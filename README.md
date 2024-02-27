# back-end

Usaremos Python 3.10.x

## Lanzar

```bash
uvicorn deck_king.main:app --reload
```

## Instalar dependencias

Aconsejable usar un entorno virtual.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Instalar PostgreSQL (Ubuntu) (soy noob) (opcional)

Instalar PostgreSQL:

```bash
sudo apt install postgresql postgresql-contrib
```

Iniciar servicio de PostgreSQL:

```bash
sudo systemctl start postgresql.service
```

Crear base de datos:

```bash
sudo -u postgres psql postgres
postgres=# CREATE DATABASE DECKKINGDB;
```

Para cambiar la password de postgres:

```bash
sudo -u postgres psql postgres
postgres=# \password postgres
```
