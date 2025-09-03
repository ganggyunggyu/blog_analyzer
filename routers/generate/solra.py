from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import run_manuscript_generation
from mongodb_service import MongoDBService
from llm.gemini_service import get_gemini_response
from utils.get_category_db_name import get_category_db_name
from typing import Optional
from fastapi.concurrency import run_in_threadpool
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
import os
