"""Descarga el dataset original de Kaggle indicado en la practica.

Dataset: Geolocation Data [Longitude Latitude]
Enlace : https://www.kaggle.com/datasets/liewyousheng/geolocation

Requisitos previos:

1. Instalar el cliente:            pip install kaggle
2. Crear el token en Kaggle:      Perfil > Settings > API > Create New Token
3. Copiar kaggle.json a:          C:/Users/<usuario>/.kaggle/kaggle.json

Uso:
    python scripts/descargar_dataset_kaggle.py
    python scripts/descargar_dataset_kaggle.py --destino data/kaggle

El proyecto funciona sin este paso porque incluye ``data/peru_localidades.csv``,
pero descargar el CSV completo permite ejecutar la practica sobre los millones de
registros originales (la app acepta el archivo con el cargador de la barra
lateral o con ``python main.py --csv ...``).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

DATASET_SLUG = "liewyousheng/geolocation"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "data" / "kaggle"


def descargar(destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    comando = [
        sys.executable,
        "-m",
        "kaggle",
        "datasets",
        "download",
        "-d",
        DATASET_SLUG,
        "-p",
        str(destino),
    ]
    print("Ejecutando:", " ".join(comando))
    resultado = subprocess.run(comando, check=False)
    if resultado.returncode != 0:
        print(
            "\nNo se pudo descargar. Verifica que 'pip install kaggle' este hecho y "
            "que kaggle.json exista en ~/.kaggle/.\n"
            f"Alternativa manual: descarga el ZIP desde "
            f"https://www.kaggle.com/datasets/{DATASET_SLUG} y descomprimelo en {destino}."
        )
        return resultado.returncode

    for zip_path in destino.glob("*.zip"):
        print(f"Descomprimiendo {zip_path.name}...")
        with zipfile.ZipFile(zip_path) as archivo:
            archivo.extractall(destino)
        zip_path.unlink()

    csvs = sorted(destino.glob("*.csv"))
    print(f"\nArchivos CSV disponibles en {destino}:")
    for csv in csvs:
        print(f"  - {csv.name} ({csv.stat().st_size / 1_048_576:.1f} MB)")
    if csvs:
        print(f"\nEjemplo de uso: python main.py --csv {csvs[0].relative_to(PROJECT_ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", default=str(DEFAULT_TARGET), help="Carpeta de descarga")
    args = parser.parse_args()
    return descargar(Path(args.destino))


if __name__ == "__main__":
    sys.exit(main())
