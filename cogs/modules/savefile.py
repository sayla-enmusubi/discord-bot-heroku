import os
import aiohttp

class SaveFile:
    def __init__(self):
        print

    async def download_file(self, url, dst_path):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    with open(dst_path, 'wb') as local_file:
                        web_file = await r.read()
                        local_file.write(web_file)
                        return dst_path

    def download_file_to_dir(self, url, dst_dir):
        return self.download_file(url, os.path.join(dst_dir, os.path.basename(url.replace(':large',''))))