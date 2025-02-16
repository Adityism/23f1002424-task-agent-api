# app.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from tasksA import *
from tasksB import *
import requests
from dotenv import load_dotenv
import os
import re
import httpx
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

load_dotenv()

@app.get("/ask")
def ask(prompt: str):
    result = get_completions(prompt)
    return result

openai_api_chat = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
openai_api_key = os.getenv("AIPROXY_TOKEN")

headers = {
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json",
}

function_definitions_llm = [
    {
        "name": "A1",
        "description": "Run a Python script from a given URL, passing an email as the argument.",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "pattern": r"[\w\.-]+@[\w\.-]+\.\w+"}
            },
            "required": ["email"]
        }
    },
    {
        "name": "A2",
        "description": "Format a markdown file using a specified version of Prettier.",
        "parameters": {
            "type": "object",
            "properties": {
                "prettier_version": {"type": "string", "pattern": r"prettier@\d+\.\d+\.\d+"},
                "filename": {"type": "string", "pattern": r".*/(.*\.md)"}
            },
            "required": ["prettier_version", "filename"]
        }
    },
    {
        "name": "A3",
        "description": "Count the number of occurrences of a specific weekday in a date file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"data/.*dates.*\.txt"},
                "targetfile": {"type": "string", "pattern": r"data/.*/(.*\.txt)"},
                "weekday": {"type": "integer", "pattern": r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"}
            },
            "required": ["filename", "targetfile", "weekday"]
        }
    },
    {
        "name": "A4",
        "description": "Sort a JSON contacts file and save the sorted version to a target file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"data/.*\.json"},
                "targetfile": {"type": "string", "pattern": r"data/.*\.json"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "A5",
        "description": "Retrieve the most recent log files from a directory and save their content to an output file.",
        "parameters": {
            "type": "object",
            "properties": {
                "log_dir_path": {"type": "string", "pattern": r"data/logs", "default": "data/logs"},
                "output_file_path": {"type": "string", "pattern": r"data/.*\.txt", "default": "data/logs-recent.txt"},
                "num_files": {"type": "integer", "minimum": 1, "default": 10}
            },
            "required": ["log_dir_path", "output_file_path", "num_files"]
        }
    },
    {
        "name": "A6",
        "description": "Generate an index of documents from a directory and save it as a JSON file.",
        "parameters": {
            "type": "object",
            "properties": {
                "doc_dir_path": {"type": "string", "pattern": r"data/docs", "default": "data/docs"},
                "output_file_path": {"type": "string", "pattern": r"data/.*\.json", "default": "data/docs/index.json"}
            },
            "required": ["doc_dir_path", "output_file_path"]
        }
    },
    {
        "name": "A7",
        "description": "Extract the sender's email address from a text file and save it to an output file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"data/.*\.txt", "default": "data/email.txt"},
                "output_file": {"type": "string", "pattern": r"data/.*\.txt", "default": "data/email-sender.txt"}
            },
            "required": ["filename", "output_file"]
        }
    },
    {
        "name": "A8",
        "description": "Generate an image representation of credit card details from a text file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"data/.*\.txt", "default": "data/credit-card.txt"},
                "image_path": {"type": "string", "pattern": r"data/.*\.png", "default": "data/credit_card.png"}
            },
            "required": ["filename", "image_path"]
        }
    },
    {
        "name": "A9",
        "description": "Find similar comments from a text file and save them to an output file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"data/.*\.txt", "default": "data/comments.txt"},
                "output_filename": {"type": "string", "pattern": r"data/.*\.txt", "default": "data/comments-similar.txt"}
            },
            "required": ["filename", "output_filename"]
        }
    },
    {
        "name": "A10",
        "description": "Identify high-value (gold) ticket sales from a database and save them to a text file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"data/.*\.db", "default": "data/ticket-sales.db"},
                "output_filename": {"type": "string", "pattern": r"data/.*\.txt", "default": "data/ticket-sales-gold.txt"},
                "query": {"type": "string", "pattern": "SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'"}
            },
            "required": ["filename", "output_filename", "query"]
        }
    }
]

def get_completions(prompt: str):
    with httpx.Client(timeout=20) as client:
        response = client.post(
            openai_api_chat,
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a function classifier that extracts structured parameters from queries."},
                    {"role": "user", "content": prompt}
                ],
                "tools": [{"type": "function", "function": function} for function in function_definitions_llm],
                "tool_choice": "auto"
            }
        )
    return response.json()["choices"][0]["message"]["tool_calls"][0]["function"]

@app.post("/run")
async def run_task(task: str):
    try:
        response = get_completions(task)
        task_code = response['name']
        arguments = response['arguments']

        if task_code == "A1":
            A1(**json.loads(arguments))
        elif task_code == "A2":
            A2(**json.loads(arguments))
        elif task_code == "A3":
            A3(**json.loads(arguments))
        elif task_code == "A4":
            A4(**json.loads(arguments))
        elif task_code == "A5":
            A5(**json.loads(arguments))
        elif task_code == "A6":
            A6(**json.loads(arguments))
        elif task_code == "A7":
            A7(**json.loads(arguments))
        elif task_code == "A8":
            A8(**json.loads(arguments))
        elif task_code == "A9":
            A9(**json.loads(arguments))
        elif task_code == "A10":
            A10(**json.loads(arguments))

        return {"message": f"{task_code} Task '{task}' executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/read", response_class=PlainTextResponse)
async def read_file(path: str = Query(..., description="File path to read")):
    try:
        if path.startswith('/data/'):
            path = path[1:]  # Remove leading slash
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
