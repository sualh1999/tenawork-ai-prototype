import time
import json
import math
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

# Import database functions
from database import (
    search_candidates_from_db,
    get_candidate_by_id,
    get_candidate_count,
    add_candidate_to_db,
    init_db,
    get_all_candidates_paginated_and_filtered,
    get_filtered_candidate_count
)

# --- FastAPI App Initialization ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

logger.add("logs/app_{time}.log", rotation="1 day", retention="7 days", level="INFO")

# --- Middleware for Logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs every incoming request and its processing time."""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}{request.url.query}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} | Time: {process_time:.3f}s")
    return response

# --- HTML Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request):
    """
    Serves the main page. Checks if the DB is empty and shows either
    a load data button or the main job search form.
    """
    logger.info("Serving home page (index.html).")
    count = get_candidate_count()
    is_db_empty = count == 0
    logger.info(f"Database contains {count} candidates. Empty: {is_db_empty}")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "is_db_empty": is_db_empty
    })

@app.post("/load-sample-data", response_class=RedirectResponse)
async def load_sample_data():
    """
    Wipes the database and loads sample data from the JSON file.
    """
    logger.info("Received request to load sample data.")
    init_db(wipe=True) # Wipe the DB and FAISS index
    
    try:
        with open("candidates_health.json", 'r') as f:
            sample_data = json.load(f)
        logger.info(f"Loaded {len(sample_data)} profiles from candidates_health.json")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not load sample data file: {e}")
        return RedirectResponse("/", status_code=303)

    for profile in sample_data:
        add_candidate_to_db(profile)
    
    logger.success("Successfully loaded all sample data.")
    return RedirectResponse("/", status_code=303) # Redirect back to home

@app.get("/add-profile", response_class=HTMLResponse)
async def add_profile_form(request: Request):
    """Displays the form to add a new candidate profile."""
    return templates.TemplateResponse("add_profile.html", {"request": request})

@app.post("/add-profile", response_class=RedirectResponse)
async def add_profile_submit(form_data: Request):
    """Handles the submission of the new profile form."""
    data = await form_data.form()
    
    # A simplified parser for the form data. 
    # A real app would have much more robust validation.
    new_profile = {
        "full_name": data.get("full_name"),
        "location": data.get("location"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "willing_to_travel": "willing_to_travel" in data,
        "bio": data.get("bio"),
        "languages_spoken": [lang.strip() for lang in data.get("languages_spoken", "").split(',') if lang.strip()],
        "education": [{
            "institution_name": data.get("institution_name"),
            "degree": data.get("degree"),
            "year": data.get("year")
        }],
        "experience": [{
            "company_name": data.get("company_name"),
            "title": data.get("title"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date")
        }]
    }
    
    logger.info(f"Adding new profile for: {new_profile['full_name']}")
    candidate_id = add_candidate_to_db(new_profile)
    
    # Redirect to the newly created profile page
    return RedirectResponse(f"/candidate/{candidate_id}", status_code=303)

@app.get("/browse", response_class=HTMLResponse)
async def browse_candidates(
    request: Request,
    page: int = 1,
    location: str | None = None,
    title: str | None = None,
    travel: bool | None = None
):
    """Displays a paginated and filterable list of all candidates."""
    page_size = 10
    
    # Get filters from query params
    filters = {
        "location": location,
        "title": title,
        "travel": travel
    }
    
    total_count = get_filtered_candidate_count(**filters)
    total_pages = math.ceil(total_count / page_size)
    
    candidates = get_all_candidates_paginated_and_filtered(
        **filters, page=page, page_size=page_size
    )
    
    # Build a base URL for pagination links that preserves filters
    base_url = f"/browse?1=1"
    if location:
        base_url += f"&location={location}"
    if title:
        base_url += f"&title={title}"
    if travel is not None:
        base_url += f"&travel={travel}"
        
    return templates.TemplateResponse("browse.html", {
        "request": request,
        "candidates": candidates,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "base_url": base_url,
        "filters": filters
    })

@app.post("/search", response_class=HTMLResponse)
async def search_candidates(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(None),
    required_languages: str = Form(None)
):
    """
    Handles the structured job form submission, finds candidates, and displays results.
    """
    # Construct a comprehensive query string from the form fields
    query_parts = [f"Job Title: {title}", f"Job Description: {description}"]
    if location:
        query_parts.append(f"Location: {location}")
    if required_languages:
        query_parts.append(f"Required Languages: {required_languages}")
    
    query_text = ". ".join(query_parts)
    logger.info(f"Received structured search request. Query: '{query_text[:150]}...'")
    
    found_candidates = search_candidates_from_db(query_text, k=5)
    logger.info(f"Found {len(found_candidates)} candidates to display.")
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "candidates": found_candidates,
        "query": query_text
    })

@app.get("/candidate/{candidate_id}", response_class=HTMLResponse)
async def get_candidate_profile(request: Request, candidate_id: int):
    """
    Displays the detailed profile for a single candidate.
    """
    logger.info(f"Fetching profile for candidate_id: {candidate_id}")
    candidate = get_candidate_by_id(candidate_id)
    
    if not candidate:
        logger.warning(f"Candidate with ID {candidate_id} not found.")
    
    return templates.TemplateResponse("candidate.html", {
        "request": request,
        "candidate": candidate
    })
