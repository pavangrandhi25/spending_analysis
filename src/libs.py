import io
import os
import re
import cv2
import boto3
import json
import nltk
import atexit
import numpy as np
import plotly.graph_objs as go
import plotly.offline as offline
from PIL import Image
from logger import logger
from db_details import Rds_db
from datetime import datetime
from dotenv import load_dotenv
from nltk.corpus import stopwords  
from sqlalchemy import func,extract
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler
from google.cloud import vision_v1p3beta1 as vision
from flask import Flask, render_template, request,flash,redirect,url_for

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
env_folder_path = os.path.join(parent_dir, 'env_folder')
service_account_file = os.path.join(env_folder_path, 'service_account_api.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_file

app = Flask(__name__)

db_cred=Rds_db().get_db_details()
os.environ['DB_USERNAME'] = db_cred['username']
os.environ['DB_PASSWORD'] = db_cred['password']
os.environ['DB_HOST'] = db_cred['endpoint']
os.environ['DB_PORT'] = db_cred['port']

DB_USER = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)

