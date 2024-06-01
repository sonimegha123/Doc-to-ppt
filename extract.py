from docx import Document
import os
import json
from io import BytesIO
import tempfile


def extract_items(docx_file):
    img_idx = 0
    tbl_idx = 0
    doc = Document(docx_file)

    tables_data = []
    images = []

    temp_dir = tempfile.mkdtemp()

    # Extract tables and images
    for idx, table in enumerate(doc.tables):
        table_data = []
        for row in table.rows:
            row_data = [cell.text for cell in row.cells]
            table_data.append(row_data)
        tables_data.append(table_data)

        # Save each table as a separate JSON file
        table_filename = f"table_{tbl_idx}.json"
        table_filepath = os.path.join(temp_dir, table_filename)
        with open(table_filepath, 'w') as table_file:
            json.dump(table_data, table_file)
        # print("Tables saved", table_filepath)
        tbl_idx += 1


    for i, rel in enumerate(doc.part.rels.values()):
        if "image" in rel.reltype:
            image = rel.target_part
            images.append(image)

            # Save images to temporary directory
            image_filename = f"image_{img_idx}.png"
            image_filepath = os.path.join(temp_dir, image_filename)
            with open(image_filepath, 'wb') as image_file:
                image_file.write(image.blob)
            # print(f"Image saved: {image_filepath}")
            img_idx += 1
    # print("temp directory", temp_dir)
    return temp_dir

