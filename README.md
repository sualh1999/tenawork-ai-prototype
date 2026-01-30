# TenaWork AI Prototype: Healthcare Job Matching Engine

This project develops an AI-powered prototype for job matching in the healthcare sector. It leverages vector embeddings from `FastEmbed` and efficient similarity search with `FAISS` to intelligently align candidate profiles with job requirements. This MVP aims to streamline the recruitment process by automating candidate-job alignment, providing a robust foundation for advanced talent acquisition solutions.

## Features

-   **Candidate Management:** Add, view, and manage candidate profiles.
-   **Intelligent Search:** Utilize vector similarity search to find the best-fit candidates for job descriptions.
-   **Filterable Browsing:** Browse candidates with filters for location, job title (with partial and case-insensitive matching), and willingness to travel.

## Setup and Running

To get this project up and running on your local machine, follow these steps:

### Prerequisites

-   Python 3.9+
-   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sualh1999/tenawork-ai-prototype.git
    cd tenawork-ai-prototype
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Start the FastAPI application:**
    ```bash
    uvicorn main:app --reload
    ```
    The `--reload` flag is optional but recommended for development, as it will automatically restart the server upon code changes.

2.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:8000`.

### Loading Sample Data

Upon first running the application, the database will be empty. You can load sample healthcare candidate data via the button on the home page or by navigating to `/load-sample-data`. This will populate the system with data to allow you to test the search and browse functionalities.
