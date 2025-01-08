import os
import subprocess
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

referer = 'https://analisi.transparenciacatalunya.cat'
url = "https://analisi.transparenciacatalunya.cat/browse?q=sigpac+2024&sortBy=alpha&utf8=%E2%9C%93&page=1&pageSize=20"
download_url = 'https://analisi.transparenciacatalunya.cat/Medi-Rural-Pesca/Dades-de-parcel-les-d-explotacions-DUN-de-Cataluny/si4p-ygat/about_data'
download_folder = "input"
file_extensions = "SHP.zip"
downloads = []

def download_all_data():
    with sync_playwright() as p:
        # pip install playwright
        # ejecutar playwright install
        browser = p.chromium.launch(headless=True)  # Cambia a False para ver el navegador
        page = browser.new_page()

        # page.goto(url)
        #
        # page.wait_for_selector('.header a')
        # links = page.query_selector_all('.header a')
        #
        # page.goto(links[0].get_attribute('href'))

        page.goto(download_url)

        page.wait_for_selector('.attachment')

        download_links = page.query_selector_all('.attachment a')
        for link in download_links:
            downloads.append(referer + link.get_attribute('href')) if link.get_attribute('href')[-7:] == file_extensions else None
        # print(download_links)

        # downloads.append(links[0].get_attribute('href'))

        browser.close()
    # print(links)
    # print(len(links))
    # print(download_links)
    print(downloads)
    # print(len(downloads))

    for link in downloads:
        print(link)
        nombre_archivo = link.split("=")[-1]
        ruta_destino = os.path.join(download_folder, nombre_archivo)

        if not os.path.exists(ruta_destino):
            os.makedirs(ruta_destino)

        comando = ["wget", link, "-O", ruta_destino]

        try:
            # Ejecutamos el comando wget
            subprocess.run(comando, check=True)
            print(f"Archivo descargado y guardado en: {ruta_destino}")
        except subprocess.CalledProcessError as e:
            print(f"Ocurrió un error al ejecutar wget: {e}")

        # TODO descomprimir ficheros

        # local_filename = os.path.join(download_folder, link.split('=')[-1])
        # try:
        #     # Hacer la solicitud GET para descargar el archivo
        #     with requests.get(url) as response:
        #         response.raise_for_status()  # Verifica si hubo un error en la descarga
        #         with open(local_filename, 'wb') as f:
        #             # for chunk in response.iter_content(chunk_size=8192):
        #             f.write(response.content)
        #     print(f"Archivo descargado: {local_filename}")
        # except Exception as e:
        #     print(f"Error al descargar {url}: {e}")




def parse_all_data():
    # install gdal
    # por cada carpeta en input (1 año)
    #   por cada fichero? o solo hay uno?
    #       usar comando gdal para pasar de shp a geojson
    #       guardar geojson en output
    pass

if __name__ == '__main__':
    download_all_data()
    # TODO: env.yml
    parse_all_data()


