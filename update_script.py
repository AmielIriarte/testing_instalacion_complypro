import os
import requests
import zipfile
import shutil
import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure .env file is loaded when running the script so os.getenv can read its values
from dotenv import load_dotenv

load_dotenv()


def setup_logging():
    logging.basicConfig(
        filename="update_log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def get_github_release(owner: str, repo: str, token: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "update-script/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # Log detailed info for debugging (status code and response body if available)
        try:
            resp = getattr(e, "response", None)
            status = resp.status_code if resp is not None else None
            body = resp.text if resp is not None else None
            logging.error(
                "get_github_release failed: url=%s status=%s response=%s",
                url,
                status,
                body,
            )
        except Exception:
            logging.exception("Error while logging GitHub response details")
        raise


def download_file(url: str, output_path: str, token: str):
    headers = {"Authorization": f"token {token}"} if token else {}
    with requests.get(
        url, headers=headers, stream=True, timeout=60
    ) as response:  # Added timeout
        if response.status_code == 404:
            # Dejar que el llamador maneje el fallback
            response.raise_for_status()
        response.raise_for_status()
        with open(output_path, "wb") as file:
            shutil.copyfileobj(response.raw, file)


def download_asset_with_api(
    owner: str, repo: str, asset_id: int, output_path: str, token: str
):
    """Download an asset using the GitHub API asset endpoint."""
    headers = {"Accept": "application/octet-stream"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{asset_id}"
    with requests.get(
        url, headers=headers, stream=True, timeout=60
    ) as response:  # Added timeout
        response.raise_for_status()
        with open(output_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)


def extract_zip(zip_path: str, extract_to: str):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Detecta si todo el contenido está dentro de una sola carpeta raíz
        all_names = [
            member.filename
            for member in zip_ref.infolist()
            if member.filename and not member.is_dir()
        ]
        if not all_names:
            return
        common_prefix = os.path.commonprefix(all_names)
        # Ajusta el prefijo para que sea una carpeta completa
        if common_prefix and not common_prefix.endswith("/"):
            common_prefix = os.path.dirname(common_prefix) + "/"

        for member in zip_ref.infolist():
            # Si hay una carpeta raíz común, quítala del path de destino
            rel_path = (
                member.filename[len(common_prefix) :]
                if common_prefix and member.filename.startswith(common_prefix)
                else member.filename
            )
            if not rel_path or rel_path.endswith("/"):
                # Es una carpeta
                dir_path = os.path.join(extract_to, rel_path)
                os.makedirs(dir_path, exist_ok=True)
                continue
            extracted_path = os.path.join(extract_to, rel_path)
            os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
            with zip_ref.open(member) as source, open(extracted_path, "wb") as target:
                shutil.copyfileobj(source, target)


def get_last_processed_release(file_path: str) -> str:
    """Reads the last processed release from a file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return file.read().strip()
    return ""


def save_last_processed_release(file_path: str, release_name: str) -> None:
    """Saves the last processed release to a file."""
    with open(file_path, "w") as file:
        file.write(release_name)


def get_token_from_db(user: str, password: str) -> str:
    """Intenta obtener el token GITHUB_TOKEN_NFE_ALERT desde la tabla updates de la base 'tecnologia'.

    Se asume que la tabla 'updates' tiene una columna 'key' y 'value' o similar; la consulta
    busca la fila donde key = 'GITHUB_TOKEN_NFE_ALERT'.
    """

    # Leer servidor/driver desde entorno o usar valores por defecto
    server = os.getenv("SQLSERVER_SERVER")
    driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")
    if not server:
        raise RuntimeError(
            "SQLSERVER_SERVER no está definido en las variables de entorno"
        )

    # Construir connection string para la base 'tecnologia'
    quoted_driver = quote_plus(driver)
    # Formato: mssql+pyodbc://user:pass@server/tecnologia?driver=Driver+Name
    conn_str = f"mssql+pyodbc://{user}:{quote_plus(password)}@{server}/tecnologia?driver={quoted_driver}"

    engine = create_engine(conn_str, fast_executemany=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = None
    try:
        session = SessionLocal()
        # Leer token desde la tabla token_updates_gh, columna token, id = 1
        sql = text(
            "SELECT TOP 1 token FROM dbo.token_updates_gh WHERE n_bot = 'ComplyPro'"
        )
        result = session.execute(sql).fetchone()
        if result:
            return str(result[0])
        return ""
    finally:
        if session:
            try:
                session.close()
            except Exception:
                pass
        try:
            engine.dispose()
        except Exception:
            pass


def main():
    setup_logging()

    owner = os.getenv("GITHUB_OWNER", "AR-BPS-TaxTech")
    repo = os.getenv("GITHUB_REPO", "nfe_alert")
    # Primero intentamos leer el token desde la variable de entorno
    token = os.getenv("GITHUB_TOKEN_NFE_ALERT", "")

    # Si no está en entorno, intentar leer desde la base de datos usando
    # las credenciales TAX_TECH_USER / TAX_TECH_PASS
    if not token:
        tax_user = os.getenv("TAX_TECH_USER")
        tax_pass = os.getenv("TAX_TECH_PASS")
        if tax_user and tax_pass:
            try:
                logging.info(
                    "Attempting to read GITHUB_TOKEN_NFE_ALERT from DB using TAX_TECH_USER/TAX_TECH_PASS"
                )
                token_from_db = get_token_from_db(tax_user, tax_pass)
                if token_from_db:
                    token = token_from_db
                    logging.info(
                        "Obtained token from DB and will use it for GitHub API requests."
                    )
                else:
                    logging.warning("Token not found in DB 'updates' table.")
            except Exception as e:
                logging.exception(f"Error obtaining token from DB: {e}")
        else:
            logging.info(
                "TAX_TECH_USER/TAX_TECH_PASS not set; skipping DB token lookup."
            )
    last_release_file = "last_release.txt"

    try:
        release = get_github_release(owner, repo, token)
        release_name = release.get("tag_name", "")

        # Check if the release has already been processed
        last_processed_release = get_last_processed_release(last_release_file)
        if release_name == last_processed_release:
            logging.info(
                f"Release {release_name} has already been processed. Skipping download."
            )
            return

        assets = release.get("assets", [])
        asset_names = [asset.get("name", "") for asset in assets]
        logging.info(f"Assets found in latest release: {asset_names}")

        if not assets:
            logging.error("No assets found in the latest release.")
            return

        zip_asset = next(
            (asset for asset in assets if asset.get("name", "").endswith(".zip")), None
        )

        if not zip_asset:
            logging.error("No ZIP file found in the latest release assets.")
            return

        zip_url = zip_asset.get("browser_download_url")
        zip_name = zip_asset.get("name")
        if not zip_url or not zip_name:
            logging.error("ZIP asset is missing download URL or name.")
            return

        zip_path = os.path.join(os.getcwd(), zip_name)

        logging.info(f"Downloading {zip_name} (try API asset endpoint first)...")
        asset_id = zip_asset.get("id")
        download_succeeded = False

        # Attempt API asset download first
        if asset_id:
            logging.info(f"Attempting download via API for asset id {asset_id}...")
            try:
                download_asset_with_api(owner, repo, asset_id, zip_path, token)
                download_succeeded = True
                logging.info("Downloaded asset via API endpoint.")
            except Exception as e:
                logging.warning(f"API asset download failed: {e}")

        # Fallback to browser_download_url if API download fails
        if not download_succeeded:
            logging.info(f"Attempting browser download from {zip_url} ...")
            try:
                download_file(zip_url, zip_path, token)
                download_succeeded = True
                logging.info("Downloaded asset via browser_download_url.")
            except Exception as e:
                logging.warning(f"Browser download failed: {e}")

        if not download_succeeded:
            logging.error("All download methods failed. Aborting update.")
            return

        logging.info(f"Extracting {zip_name}...")
        try:
            extract_zip(zip_path, os.getcwd())
        except zipfile.BadZipFile:
            logging.error("Failed to extract ZIP file. The file may be corrupted.")
            return
        except Exception as e:
            logging.error(f"Unexpected error extracting ZIP: {e}")
            return

        # Delete the ZIP file after extraction
        try:
            os.remove(zip_path)
            logging.info(f"Deleted ZIP file: {zip_name}")
        except Exception as e:
            logging.error(f"Failed to delete ZIP file: {e}")

        # Save the current release as the last processed release
        save_last_processed_release(last_release_file, release_name)

        logging.info("Update completed successfully.")
    except requests.RequestException as e:
        logging.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
