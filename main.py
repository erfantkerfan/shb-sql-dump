import subprocess
from dotenv import load_dotenv
import os
from minio import Minio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def dump(host: str,port: str, user: str, password: str, backup_file: str):
    command = f"mariadb-dump -h {host} -u {user} -P {port} -p{password} --all-databases > {backup_file}"
    logging.info(command)
    result = subprocess.run(command, shell=True, check=False, text=True, capture_output=True)
    logging.info(f'Return stream of SQL dump: {result.stderr}')
    logging.info(f'Return code of SQL dump: {result.returncode}')
    
    if result.returncode != 0:
        raise Exception("dump failed")  

def upload_s3(host: str, port: str, user: str, password: str,bucket: str, file: str):
    client = Minio(
        f"{host}:{port}",
        access_key=f"{user}",
        secret_key=f"{password}",
        secure=False
    )
    result = client.fput_object(
        f"{bucket}", f"{file}", f"{file}",
    )

def send_email(sender_email, sender_password, recipient_email, subject, body):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP(os.getenv('MAIL_HOST'), int(os.getenv('MAIL_PORT'))) as server:
        server.send_message(message)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    load_dotenv()
    MAIL_USER = os.getenv('MAIL_USER')
    MAIL_TARGET = os.getenv('MAIL_TARGET')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    try:
        dump(os.getenv('MYSQL_HOST'),   
                os.getenv('MYSQL_PORT'),
                os.getenv('MYSQL_USER'),
                os.getenv('MYSQL_PASSWORD'),
                os.getenv('MYSQL_DUMP_FILE')
        )
        upload_s3(os.getenv('MINIO_HOST'),
                os.getenv('MINIO_PORT'),
                os.getenv('MINIO_USER'),
                os.getenv('MINIO_PASSWORD'),
                os.getenv('MINIO_BUCKET'),
                os.getenv('MYSQL_DUMP_FILE')
        )
    except Exception as e:
        logging.error(e     )
        send_email(f'{MAIL_USER}', f'{MAIL_PASSWORD}', f'{MAIL_TARGET}', 'sql backup failed!', 'blah blah')
    else:
        send_email(f'{MAIL_USER}', f'{MAIL_PASSWORD}', f'{MAIL_TARGET}', 'sql backup done', 'blah blah')
