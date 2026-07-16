import json
import os
import zipfile
from io import StringIO

from core.logging_config import get_logger
logger = get_logger(__name__)
from pyproj import Transformer, CRS
import pyproj
import re

import xmltodict
import gpxpy
import gpxpy.gpx
import xml.etree.ElementTree as ET
import re



def msk66_to_wgs84(x, y, zone=1):
    crs_wgs84 = CRS("EPSG:4326")
    # crs_msk = CRS("EPSG:6336601")

    proj_msk66_zone11 = (
        "EPSG:28411"
    )
    # Создаем преобразователь
    # МСК-66 использует эллипсоид Красовского
    msksk42_svrd_zone1_proj4 = (
        "+proj=tmerc +lat_0=0 +lon_0=60.05 +k=1.0 "
        "+x_0=1500000 +y_0=-5911057.63 "
        "+ellps=krass +towgs84=23.57,-140.95,-79.8,0,0.35,0.79,-0.22 +units=m +no_defs"
    )
    msksk42_svrd_zone1 = pyproj.CRS(msksk42_svrd_zone1_proj4)
    transformer = Transformer.from_crs(
        msksk42_svrd_zone1,
        "EPSG:4326"
    )

    # Преобразуем координаты
    lon, lat = transformer.transform(x, y)
    print(lon, lat)
    return [lon, lat]


class GlrService:
    path_to_zip: str
    save_path: str
    temp_dir: str
    glr_file_name: str
    path_to_glr: str

    def __init__(self, path_to_zip, temp_dir="./temp", save_path=None, glr_file_name="Vypiska is glr.xml.xml"):
        self.path_to_zip = path_to_zip
        self.save_path = save_path
        self.temp_dir = temp_dir
        self.glr_file_name = glr_file_name

    def unpack_zip(self):
        with zipfile.ZipFile(self.path_to_zip, "r") as zip_re:
            zip_re.extract(self.glr_file_name, self.temp_dir)
            self.path_to_glr = os.path.join(self.temp_dir, self.glr_file_name)

    def parse_xml(self) -> list:
        result_list = []
        tree = ET.parse(self.path_to_glr)

        # получаем UTF-8 bytes
        xml_bytes = ET.tostring(tree.getroot(), encoding="utf-8")

        # безопасно декодируем
        xml_str = xml_bytes.decode("utf-8", errors="strict")

        # убираем namespace
        xml_str = re.sub(r"</(ns\d+):", "</", xml_str)
        xml_str = re.sub(r"<(ns\d+):", "<", xml_str)

        # сохраняем (если действительно нужно)
        self.path_to_glr = os.path.join(self.temp_dir, "cleared.xml")
        with open(self.path_to_glr, "w", encoding="utf-8") as f:
            f.write(xml_str)

        xml_data = xml_str
        # print(xml_data)
        # Convert XML data to a Python dictionary
        spatials_elements = xmltodict.parse(xml_data)['stateForestRegisterExtractForestTaxingAllocation']['sectionxi'][
                'data'][
                'descriptionLocationBoundary']['contours']['contour']['entitySpatial'][
                'spatialsElements']
        final_list = []
        if isinstance(spatials_elements['spatialsElement'], list):
            logger.info("Найдено несколько контуров, будет создано несколько треков в GPX-файле")
        else:
            logger.info("Найден один контур, будет создан один трек в GPX-файле")
            spatials_elements['spatialsElement'] = [spatials_elements['spatialsElement']]
        
        for spatials_element in spatials_elements['spatialsElement']:
            print(spatials_elements)
            data_dict = spatials_element['ordinates']['ordinate']
            for ordinate in data_dict:
                coords = msk66_to_wgs84(
                    float(ordinate["y"]), float(ordinate["x"]))
                result_list.append(coords)
            final_list.append(result_list)
        return final_list

    def create_gpx_file(self, result_list):
        gpx = gpxpy.gpx.GPX()
        for result in result_list:
        # Создаем трек
            track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(track)

        # Создаем сегмент в треке
            segment = gpxpy.gpx.GPXTrackSegment()
            track.segments.append(segment)
            for lat, lon in result:
                segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
        with open(self.save_path, 'w') as f:
            f.write(gpx.to_xml())

    def parse_glr(self):
        self.unpack_zip()
        result_list = self.parse_xml()
        self.create_gpx_file(result_list)

# if __name__ == '__main__':
#     service = GlrService("./выписка ГЛР кв 29З в 20 С-251201-1666868.zip")
#     service.parse_glr()
def convert(path_to_zip: str, save_path: str) -> None:
    service = GlrService(path_to_zip, save_path=save_path)
    service.parse_glr()
    return None