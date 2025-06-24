import subprocess
import json

EXIFTOOL_PATH = r"C:\Users\akshi\Downloads\exiftool-13.31_64\exiftool-13.31_64\exiftool.exe"

def extract_deep_metadata(image_path):
    metadata = {}
    try:
        result = subprocess.run(
            [EXIFTOOL_PATH, "-j", image_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            data = json.loads(result.stdout)[0]
            keys_to_show = [
                'FileName',
                'FileType',
                'FileModifyDate',
                'FileSize',
                'CreateDate',
                'ModifyDate',
                'Software',
                'CreatorTool',
                'MetadataDate',
                'HistorySoftwareAgent',
                'HistoryWhen',
                'ProfileDescription'
            ]
            for key in keys_to_show:
                if key in data:
                    metadata[key] = data[key]
        else:
            metadata['Error'] = result.stderr.strip()
    except Exception as e:
        metadata['Error'] = str(e)
    return metadata
