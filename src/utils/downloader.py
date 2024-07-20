import pathlib
import time

import requests
from requests.structures import CaseInsensitiveDict

from .logger import SyncLogger
from .network import headers


class Downloader:
    def __init__(self, output_path="files"):
        self.output_path = output_path

    def download(
            self,
            uri: str,
            core_type: str = "",
            mc_version: str = "",
            core_version: str = "",
            retries: int = 3,
    ) -> pathlib.Path:
        """
        :param uri: 下载地址
        :param filename: 指定文件名, 缺省则自动获取
        :return: 下载完成的文件路径
        """
        filename = (core_type + "-" + mc_version + "-" + core_version)
        SyncLogger.info(
            f"Start downloading | {filename}"
        )
        start_time = time.time()
        res = requests.get(uri, headers=headers, stream=True, allow_redirects=True)
        try:
            if res.ok:
                res_headers = res.headers
                content_length = int(res_headers.get("Content-Length", "0"))
                filename = filename + "." + self.get_file_type(res_headers)
                file_path: pathlib.Path = pathlib.Path(
                    self.output_path, core_type, mc_version, filename
                ).absolute()
                SyncLogger.info(
                    f"Downloading | {filename} | File size: {round(content_length / 1000000, 2)} MB"
                )
                for chunk in res.iter_content(chunk_size=4096):
                    file_path.write_bytes(chunk)
                SyncLogger.success(
                    f"Downloaded | {filename} | {(content_length / 1000 / 1000) / (time.time() - start_time):.2f} MB/s | {time.time() - start_time:.2f} s"
                )
                return file_path
            else:
                raise Exception("Request failed")
        except Exception as err:
            retries -= 1
            if retries > 0:
                SyncLogger.warning(f"Download failed | {filename} | {retries} retries left | {err}")
                return self.download(uri, core_type, mc_version, core_version, retries)
            else:
                SyncLogger.error(f"Download failed | {filename} | {err}")
                raise err

    def get_file_type(self, headers: CaseInsensitiveDict[str], default: str = "jar"):
        file_type = default
        try:
            if 'Content-Disposition' in headers and headers['Content-Disposition']:
                dispositions = headers['Content-Disposition'].split(';')
                for disposition in dispositions:
                    if disposition.strip().lower().startswith('filename='):
                        file_name = disposition.split('filename="')[1].split('"')[0]
                        file_type = file_name.split('.')[-1]
        except IndexError:
            pass
        return file_type
