import base64
import json
import os
import pymupdf
import re
from llama_index.core.node_parser import SentenceSplitter
from google.cloud import storage
import requests

json_bucket_name = os.environ.get('JSON_BUCKET_NAME')

def remove_space(text):
    words = text.split()
    clean_text = " ".join(words)
    return clean_text

def get_text(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    
    return text

def create_chunk_json(text):
    content_between_chapters = re.findall(r"(?:^|\n)(Chương \b(?:I{1,3}(?:V?X?)?|VI{0,3}|XI{0,3}V?|XVI{0,3})\b\.?)(.*?)(?=(?:^|\n)(Chương \b(?:I{1,3}(?:V?X?)?|VI{0,3}|XI{0,3}V?|XVI{0,3})\b\.? |$))", text, re.DOTALL)

    chapter_name = []
    all_content_chapter = []

    for content in content_between_chapters:
        chapter_name.append(content[0].strip())
        all_content_chapter.append(content[0] + content[1])
    
    titles = []
    contents = []
    regex_chapter = re.compile(r'(?:^|\n)(Chương \b(?:I{1,3}(?:V?X?)?|VI{0,3}|XI{0,3}V?|XVI{0,3})\b\.?)\s*(.*)')
    regex_rule = re.compile(r'(Điều \d+\.)(.*?)(?=(Điều \d+\. |$))', re.DOTALL)
    for content_chap in all_content_chapter:
        matches_chapter = regex_chapter.findall(content_chap)
        matches_rule = regex_rule.findall(content_chap)
        for match_rule in matches_rule:
            for match_chapter in matches_chapter:
                temp_chapter_title = match_chapter[0] + "\n" + match_chapter[1]
                # chapter_title.append(temp.strip())
            temp_rule_title = match_rule[0] + match_rule[1].split('\n')[0].strip()
            # rule_title.append(temp_title_rule.strip())
            titles.append("Document Title" + "\n" + temp_chapter_title + "\n" + temp_rule_title)
            temp_content_rule = remove_space(" ".join(match_rule[1].split('\n')[1:]).strip())
            contents.append(temp_content_rule)

    chunking_strategy = SentenceSplitter(chunk_size=512, chunk_overlap=64)

    chunk_names, chunk_list = [], []
    for i in range(len(contents)):
        chunk = chunking_strategy.split_text(contents[i])
        chunk_length = len(chunk)
        for _ in range(chunk_length):
            chunk_names.append(titles[i])
        chunk_list += chunk
    
    data = []
    for i in range(len(chunk_names)):
        data.append({'title': chunk_names[i], 'context': chunk_list[i]})

    return data    

# Upload a JSON object to a specified Google Cloud Storage bucket.
def upload_json_to_bucket(json_data, bucket_name, output_filename):
    storage_client = storage.Client()
    json_bucket = storage_client.bucket(bucket_name)
    output_blob = json_bucket.blob(output_filename)

    output_json_path = f"/tmp/{output_filename}"
    with open(output_json_path, "w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)
    
    output_blob.upload_from_filename(output_json_path)
    return output_json_path

# Send a file to a remote API using an HTTP POST request.
def send_file_to_api(file_path):
    api_url = os.environ.get('API_URL')
    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(api_url, files=files)
        if response.status_code != 200:
            print(f"Failed to send file to API. Status code: {response.status_code}")
        else:
            print(f"Successfully sent file to API.")

# Download a blob from Google Cloud Storage to a temporary local path.
def download_blob_to_tmp(blob, file_name):
    temp_path = f"/tmp/{file_name}"
    blob.download_to_filename(temp_path)
    return temp_path

# Combine text content from multiple PDFs in a GCS bucket, excluding a specified file.
def combine_texts_from_pdfs(bucket, exclude_file=None):
    all_text = ""
    blobs = bucket.list_blobs()
    for blob in blobs:
        if blob.name.endswith('.pdf') and blob.name != exclude_file:
            temp_pdf_path = download_blob_to_tmp(blob, blob.name)
            text = get_text(temp_pdf_path)
            all_text += text + "\n"
    return all_text

# Process a PDF file uploaded to a GCS bucket and generate a combined JSON output.
def process_pdf_file(event, context):
    """Triggered by a Pub/Sub message when a file is uploaded."""
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    message_data = json.loads(pubsub_message)

    if 'bucket' not in message_data or 'name' not in message_data:
        print("Missing 'bucket' or 'name' in Pub/Sub message")
        return

    file_name = message_data['name']

    # Only proceed if the file is a PDF
    if not file_name.endswith('.pdf'):
        print(f"File {file_name} is not a PDF. Skipping processing.")
        return

    bucket_name = message_data['bucket']
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download the uploaded PDF file from GCS
    temp_pdf_path = download_blob_to_tmp(blob, file_name)

    # Extract text from the PDF and create a JSON
    text = get_text(temp_pdf_path)
    current_file_json = create_chunk_json(text)

    # Process all other PDFs in the bucket and generate a combined JSON
    all_text = combine_texts_from_pdfs(bucket, exclude_file=file_name)
    other_files_json = create_chunk_json(all_text)

    combined_json = current_file_json + other_files_json

    # Save combined result to 'all.json' in the new bucket
    output_json_path = upload_json_to_bucket(combined_json, json_bucket_name, 'all.json')

    print(f"Processed {file_name} and saved combined result to {json_bucket_name}/all.json")

    # Send the all.json file to the API
    send_file_to_api(output_json_path)

# if __name__ == '__main__':
#     text = get_text('./data/35-2024-qh15.pdf')
#     with open('test.json', "w", encoding="utf-8") as file:
#         json.dump(create_chunk_json(text), file, ensure_ascii=False, indent=4)
    # print(create_chunk_json(text)[0])


    
def delete_pdf_file(event, context):
    try:
        # Decode the Pub/Sub message
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        message_data = json.loads(pubsub_message)

        deleted_file_name = message_data['name']
        bucket_name = message_data['bucket']

        print(f"Deleted file: {deleted_file_name} from bucket: {bucket_name}")

        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

        all_text = combine_texts_from_pdfs(bucket, exclude_file=deleted_file_name)
        updated_json = create_chunk_json(all_text)

        output_json_path = upload_json_to_bucket(updated_json, json_bucket_name, 'all.json')
        
        print(f"Updated {json_bucket_name}/all.json after deleting {deleted_file_name}")
        send_file_to_api(output_json_path)

    except KeyError as e:
        print(f"KeyError - reason: {str(e)}")
    except Exception as e:
        print(f"Error processing file deletion: {str(e)}")