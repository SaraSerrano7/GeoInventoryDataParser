import os
import subprocess

import pyproj
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import asyncio
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

        # TODO: Readme.md
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
    folders = [os.path.join('input', folder) for folder in os.listdir('input')]

    zip_files = [folder for folder in folders if folder[-3:] == 'zip']
    # TODO cambiar saved files por zip folder

    for saved_file in zip_files:

        extracted_folder = saved_file[:-4]
        if os.path.exists(extracted_folder):
            print(f"El archivo ya está descomprimido y guardado en: {extracted_folder}")
            extracted_files.append(extracted_folder)
            continue

        # extracted_folder = os.path.join(download_folder, Path(saved_file).stem)
        try:
            with zipfile.ZipFile(saved_file, 'r') as zip_ref:

                file_list = zip_ref.namelist()

                # Check if all files have a common directory prefix
                has_root_folder = False
                if file_list:
                    # Get the first path component of the first file
                    first_component = file_list[0].split('/')[0] if '/' in file_list[0] else ''

                    # Check if all files start with this component and if it's a directory
                    if first_component and all(f.startswith(f"{first_component}/") for f in file_list):
                        has_root_folder = True

            # Extract based on whether there's a root folder
            if has_root_folder:
                # Files already have a root folder, extract directly to download_folder
                with zipfile.ZipFile(saved_file, 'r') as zip_ref:
                    zip_ref.extractall(download_folder)
                    print(f"Archivo {saved_file} descomprimido en {download_folder}")
                    extracted_files.append(os.path.join(download_folder, first_component))

            else:
            # Files don't have a root folder, create one based on the zip filename
                root_folder_name = Path(saved_file).stem
                target_folder = os.path.join(download_folder, root_folder_name)

                # Create the target folder if it doesn't exist
                os.makedirs(target_folder, exist_ok=True)

                # Extract files to the new root folder
                with zipfile.ZipFile(saved_file, 'r') as zip_ref:
                    zip_ref.extractall(target_folder)
                    print(f"Archivo {saved_file} descomprimido en {extracted_folder}")
                    extracted_files.append(extracted_folder)
        except zipfile.BadZipFile as e:
            print(f"Error al descomprimir el archivo {saved_file}: {e}")



async def download_file_by_file():
    download_pages = [1, 2, 3]
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            accept_downloads=True
            # downloads_path=download_folder
        )
        page = await context.new_page()

        dataset_hrefs = []
        for download_page in download_pages:
            # Navigate to the main page
            url = f"https://analisi.transparenciacatalunya.cat/browse?q=sigpac+2024&sortBy=alpha&utf8=%E2%9C%93&page={download_page}&pageSize=44"
            print(f"Navigating to {url}")
            await page.goto(url)

            # Wait for the content to load
            await page.wait_for_load_state("networkidle")

            # Get all dataset links
            dataset_links = await page.query_selector_all('.entry-name-link')


            for link in dataset_links:
                name = await link.inner_text()
                if name == 'Dades de parcel·les d’explotacions (DUN) de Catalunya':
                    continue
                href = await link.get_attribute('href')
                if href:
                    dataset_hrefs.append(href)


        # Visit each dataset page and download zip files
        downloads = []
        for href in dataset_hrefs:
            print(f"Processing dataset: {href}")

            # Navigate to the dataset page
            await page.goto(href)
            await page.wait_for_load_state("networkidle")


            # Find download buttons
            # await page.wait_for_selector('.attachment')
            download_links = await page.query_selector_all('.attachment a')
            for link in download_links:
                target_file = await link.get_attribute('href')
                downloads.append(referer + target_file) if target_file[-7:] == file_extensions.lower() else None

            target_download = downloads[-1] if downloads else None

            # for link in downloads:
            nombre_archivo = target_download.split("=")[-1]
            ruta_destino = os.path.join(download_folder, nombre_archivo)

            if os.path.exists(ruta_destino):
                print(f"El archivo ya está descargado y guardado en: {ruta_destino}")
                saved_files.append(ruta_destino)
                continue

            if not os.path.exists(download_folder):
                os.makedirs(ruta_destino)

            comando = ["wget", target_download, "-O", ruta_destino]

            try:
                subprocess.run(comando, check=True)
                print(f"Archivo descargado y guardado en: {ruta_destino}")
                saved_files.append(ruta_destino)
            except subprocess.CalledProcessError as e:
                print(f"Ocurrió un error al ejecutar wget: {e}")

            # download_buttons = await page.query_selector_all('a.download')

            # for button in download_buttons:
            #     button_text = await button.inner_text()
            #     href = await button.get_attribute('href')
            #
            #     if href and href.endswith('.zip'):
            #         print(f"Found zip file: {href}")
            #
            #         # Click the download button
            #         download_promise = page.wait_for_download()
            #         await button.click()
            #         download = await download_promise
            #
            #         # Save the file
            #         filename = download.suggested_filename
            #         download_path = os.path.join(download_folder, filename)
            #         await download.save_as(download_path)
            #         print(f"Downloaded: {filename}")
            #
            #         # Wait a bit to avoid overwhelming the server
            #         await asyncio.sleep(2)

        # Close the browser
        await browser.close()
        print("Download process completed")


# def download_all_files():
#     pass

# TODO permitir descargar por comarcas
if __name__ == '__main__':
    # download_all_data()
    asyncio.run(download_file_by_file())

    # download_all_files()


    extract_all_data()
    parse_all_data()



