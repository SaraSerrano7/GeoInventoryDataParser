import os
import subprocess

import pyproj
from playwright.sync_api import sync_playwright
import zipfile
from pathlib import Path
import geopandas as gpd

referer = 'https://analisi.transparenciacatalunya.cat'
url = "https://analisi.transparenciacatalunya.cat/browse?q=sigpac+2024&sortBy=alpha&utf8=%E2%9C%93&page=1&pageSize=20"
download_url = 'https://analisi.transparenciacatalunya.cat/Medi-Rural-Pesca/Dades-de-parcel-les-d-explotacions-DUN-de-Cataluny/si4p-ygat/about_data'
download_folder = "input"
saved_files = []
extracted_files = []
file_extensions = "SHP.zip"
downloads = []
output_folder = 'output'




def download_all_data():
    with sync_playwright() as p:
        # pip install playwright
        # ejecutar playwright install
        browser = p.chromium.launch(headless=True)  # Cambia a False para ver el navegador
        page = browser.new_page()
        page.goto(download_url)
        page.wait_for_selector('.attachment') #'.header para buscar los links anteriores. paara'
        download_links = page.query_selector_all('.attachment a')
        for link in download_links:
            downloads.append(referer + link.get_attribute('href')) if link.get_attribute('href')[-7:] == file_extensions else None
        browser.close()

    for link in downloads:
        nombre_archivo = link.split("=")[-1]
        ruta_destino = os.path.join(download_folder, nombre_archivo)

        if os.path.exists(ruta_destino):
            print(f"El archivo ya está descargado y guardado en: {ruta_destino}")
            saved_files.append(ruta_destino)
            continue

        if not os.path.exists(download_folder):
            os.makedirs(ruta_destino)

        comando = ["wget", link, "-O", ruta_destino]

        try:
            subprocess.run(comando, check=True)
            print(f"Archivo descargado y guardado en: {ruta_destino}")
            saved_files.append(ruta_destino)
        except subprocess.CalledProcessError as e:
            print(f"Ocurrió un error al ejecutar wget: {e}")


def parse_all_data():
    os.environ['PROJ_LIB'] = f'{pyproj.datadir.get_data_dir()}'
    for file in extracted_files:
        carpeta_salida_geojson = os.path.join(output_folder, Path(file).stem)
        # carpeta_shapefile -> carpeta descomprimida -> file
        # carpeta_salida -> carpeta_salida_geojson

        if not os.path.exists(carpeta_salida_geojson):
            os.makedirs(carpeta_salida_geojson)

            # Listamos todos los archivos .shp en la carpeta
        for archivo in Path(file).glob("*.shp"):
            # Leer el shapefile con geopandas
            try:

                # Construir la ruta del archivo GeoJSON de salida
                geojson_salida = os.path.join(carpeta_salida_geojson, f"{archivo.stem}.geojson")

                if os.path.exists(str(geojson_salida)):
                    print(f"El archivo {str(geojson_salida)} ya existe.")
                    continue

                gdf = gpd.read_file(str(archivo))
                # sudo apt get install libproj-dev



                # Guardar como GeoJSON
                gdf.to_file(geojson_salida, driver="GeoJSON")
                print(f"Shapefile convertido a GeoJSON: {geojson_salida}")
            except Exception as e:
                print(f"Error al convertir {archivo}: {e}")
        #         TODO: mantener fiona en 1.9.6 y geopandas en 0.14.4
        # TODO instalar apt get libproj-dev
        # TODO playwright install
        # TODO conda install -c conda-forge geopandas=0.14.4

        # TODO warning:
        # 1.6 GB each zip
        # 6.7 GB each extracted zip
        # ETA: 15 min aprox for each conversion
        # 6.1 GB each conversion

        # install gdal
        # por cada carpeta en input (1 año)
        #   por cada fichero? o solo hay uno?
        #       usar comando gdal para pasar de shp a geojson
        #       guardar geojson en output



def extract_all_data():
    for saved_file in saved_files:

        extracted_folder = saved_file[:-4]
        if os.path.exists(extracted_folder):
            print(f"El archivo ya está descomprimido y guardado en: {extracted_folder}")
            extracted_files.append(extracted_folder)
            continue

        # extracted_folder = os.path.join(download_folder, Path(saved_file).stem)
        try:
            with zipfile.ZipFile(saved_file, 'r') as zip_ref:
                zip_ref.extractall(download_folder)
                print(f"Archivo {saved_file} descomprimido en {extracted_folder}")
                extracted_files.append(extracted_folder)
        except zipfile.BadZipFile as e:
            print(f"Error al descomprimir el archivo {saved_file}: {e}")

if __name__ == '__main__':
    download_all_data()
    extract_all_data()
    parse_all_data()


