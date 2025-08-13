from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import run_manuscript_generation
from mongodb_service import MongoDBService
from llm.claude_service import get_claude_response
from llm.gemini_service import get_gemini_response
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from typing import Optional
from fastapi.concurrency import run_in_threadpool
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
import os
