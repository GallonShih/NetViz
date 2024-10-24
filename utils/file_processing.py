# utils/file_processing.py
import pandas as pd
import io
import base64

def process_uploaded_file(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = pd.read_excel(io.BytesIO(decoded), dtype={'座號': 'str', '順位1': 'str', '順位2': 'str'})
        df.columns = ['st_id', 'order1', 'order2', 'order3']
        df.dropna(inplace=True)
        df = df.astype(int)  # 確保轉換為整數型態
        return df
    except Exception as e:
        print(e)
        return None
