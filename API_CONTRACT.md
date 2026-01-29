# TenaWork API Contract

This document serves as the single source of truth for the APIs used in the TenaWork platform. All teams (Frontend, Backend, AI) should adhere to these contracts to ensure smooth integration.

## Base URL

All API routes are prefixed with `/api`.

## Authentication

Protected routes require a JSON Web Token (JWT) to be passed in the `Authorization` header.

**Format:** `Authorization: Bearer <YOUR_JWT>`

---

## 1. Main Backend API (Node.js)

This is the primary API that the Frontend application will interact with.

### **Authentication**

#### `POST /auth/register/professional`
- **Description:** Registers a new professional user and creates their initial profile, including education and experience. Due to the file upload (resume), this endpoint should expect `multipart/form-data`.
- **Authentication:** Public.
- **Request Body (`multipart/form-data`):**
  The request will contain a `resume` file and a JSON string part (e.g., named `data`) with the following structure:
  ```json
  {
    "full_name": "Dr. Jane Doe",
    "location": "Addis Ababa",
    "willing_to_travel": true,
    "phone": "+251911123456",
    "email": "jane.doe@example.com",
    "password": "a_strong_password",
    "bio": "Experienced pediatrician with a passion for community health.",
    "languages_spoken": ["Amharic", "English", "Oromo"],
    "education": [
      {
        "institution_name": "Addis Ababa University, College of Health Sciences",
        "degree": "Doctor of Medicine",
        "year": "2015"
      }
    ],
    "experience": [
      {
        "company_name": "Black Lion Hospital",
        "title": "General Practitioner",
        "start_date": "2016-01-01",
        "end_date": "2020-12-31"
      }
    ]
  }
  ```
- **Success Response (201):** Logs the user in immediately by providing a JWT.
  ```json
  {
    "token": "xxxxxxxx.yyyyyy.zzzzzz",
    "user": {
      "id": 1,
      "full_name": "Dr. Jane Doe",
      "user_type": "professional"
    }
  }
  ```

#### `POST /auth/register/employer`
- **Description:** Registers a new employer user and their company profile in a single step. The company status will be set to `pending` for admin review.
- **Authentication:** Public.
- **Request Body:**
  ```json
  {
    "company_name": "Nile Technology Solutions",
    "full_name": "Muhammed Ali",
    "position": "CTO",
    "phone": "+251912987654",
    "city": "Addis Ababa",
    "address": "Bole Sub-City, Kebele 03/05",
    "email": "salih.m@nts.com",
    "password": "a_strong_password"
  }
  ```
- **Success Response (201):** Logs the user in, but the frontend should check the profile status and show the "Pending Approval" page.
  ```json
  {
    "token": "xxxxxxxx.yyyyyy.zzzzzz",
    "user": {
      "id": 2,
      "full_name": "Muhammed Ali",
      "user_type": "employer",
      "company_status": "pending"
    }
  }
  ```

#### `POST /auth/login`
- **Description:** Authenticates a user and returns a JWT.
- **Authentication:** Public.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "a_strong_password"
  }
  ```
- **Success Response (200):**
  ```json
  {
    "token": "xxxxxxxx.yyyyyy.zzzzzz",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "user_type": "professional"
    }
  }
  ```

### **Profiles**

#### `GET /profiles/me`
- **Description:** Gets the complete profile of the currently authenticated user.
- **Authentication:** Required.
- **Success Response (200):**
  ```json
  // Example for a professional
  {
    "user_id": 1,
    "full_name": "Dr. Jane Doe",
    "bio": "Experienced pediatrician...",
    "resume_url": "/path/to/resume.pdf",
    "education": [
      { "id": 1, "institution_name": "Medical University", "degree": "MD" }
    ],
    "experience": [
      { "id": 1, "company_name": "City Hospital", "job_title": "Pediatrician" }
    ]
  }
  ```

#### `PUT /profiles/me`
- **Description:** Updates the profile of the currently authenticated user.
- **Authentication:** Required.
- **Request Body:** (Send only the fields to be updated)
  ```json
  {
    "full_name": "Dr. Jane Doe",
    "bio": "Experienced pediatrician with 10 years of practice."
  }
  ```
- **Success Response (200):** Returns the updated profile object.

### **Jobs**

#### `POST /jobs`
- **Description:** (Employer) Creates a new job posting. The backend will then asynchronously trigger the AI recommendation process.
- **Authentication:** Required (Employer, approved account).
- **Request Body:**
  ```json
  {
    "title": "Senior Nurse",
    "description": "We are looking for a senior nurse with extensive experience in a fast-paced hospital environment...",
    "location": "Addis Ababa",
    "salary_range": "40,000 - 50,000 ETB",
    "employment_type": "Full Time", // "Full Time" or "Part Time"
    "years_of_experience_required": 5,
    "required_languages": ["Amharic", "English"]
  }
  ```
- **Success Response (201):** Returns the newly created job object.
  ```json
  {
    "id": 123,
    "employer_id": 2,
    "title": "Senior Nurse",
    "description": "We are looking for a senior nurse...",
    // ...other fields
  }
  ```

#### `GET /jobs/:id/recommendations`
- **Description:** (Employer) Gets the Top 10 AI-recommended candidates for a specific job they posted.
- **Authentication:** Required (Employer who owns the job).
- **Success Response (200):**
  ```json
  {
    "job_id": 123,
    "recommendations": [
      {
        "candidate": {
          "user_id": 45,
          "full_name": "John Smith"
        },
        "match_score": 0.92
      }
      // ... up to 10 candidates
    ]
  }
  ```

#### `GET /jobs/recommended`
- **Description:** (Professional) Gets the Top 5 AI-recommended jobs for the authenticated user.
- **Authentication:** Required (Professional).
- **Success Response (200):** An array of job objects.
  ```json
  [
    {
      "id": 456,
      "title": "Pediatric Nurse",
      "company_name": "General Hospital",
      "match_score": 0.95
    }
    // ... up to 5 jobs
  ]
  ```

### **Applications**

#### `POST /jobs/:id/apply`
- **Description:** (Professional) Applies for a job.
- **Authentication:** Required (Professional).
- **Request Body:**
  ```json
  {
    "cover_letter": "I am very interested in this position..."
  }
  ```
- **Success Response (201):**
  ```json
  {
    "message": "Application submitted successfully.",
    "application_id": 789
  }
  ```

#### `GET /applications/me`
- **Description:** (Professional) Gets a list of all applications submitted by the user.
- **Authentication:** Required (Professional).
- **Success Response (200):**
  ```json
  [
    {
      "application_id": 789,
      "job": { "id": 123, "title": "Senior Nurse" },
      "status": "viewed",
      "applied_at": "2024-01-01T12:00:00Z"
    }
  ]
  ```

#### `GET /jobs/:id/applicants`
- **Description:** (Employer) Gets the list of professionals who have applied to a specific job.
- **Authentication:** Required (Employer who owns the job).
- **Success Response (200):** An array of application objects, including candidate info.

### **Admin**

#### `GET /admin/employers/pending`
- **Description:** Gets a list of all employers awaiting approval.
- **Authentication:** Required (Admin).
- **Success Response (200):** An array of employer profile objects.

#### `PUT /admin/employers/:id/status`
- **Description:** Approves or rejects an employer's profile.
- **Authentication:** Required (Admin).
- **Request Body:**
  ```json
  { "status": "approved" } // or "rejected"
  ```
- **Success Response (200):**
  ```json
  { "message": "Employer status updated successfully." }
  ```

---

## 2. AI Engine API (Python/Flask)

This is a specialized, internal API. The **Backend** is its only client.

### `POST /generate-embedding`
- **Description:** Takes a piece of text and returns its vector representation.
- **Request Body:**
  ```json
  {
    "text": "A piece of text from a job description or user profile."
  }
  ```
- **Success Response (200):**
  ```json
  {
    "vector": [0.012, -0.234, ..., 0.567] // Array of floats
  }
  ```

### `POST /recommend-candidates`
- **Description:** Takes a job's vector and a list of candidate IDs to rank, and returns the top matches.
- **Request Body:**
  ```json
  {
    "job_vector": [0.012, -0.234, ..., 0.567],
    "candidate_ids": [45, 78, 92, 101]
  }
  ```
- **Success Response (200):**
  ```json
  {
    "recommendations": [
      { "id": 92, "score": 0.95 },
      { "id": 45, "score": 0.89 }
    ]
  }
  ```

### `POST /recommend-jobs`
- **Description:** Takes a professional's profile vector and returns the top matching job IDs.
- **Request Body:**
  ```json
  {
    "profile_vector": [0.345, -0.678, ..., 0.123]
  }
  ```
- **Success Response (200):**
  ```json
  {
    "recommendations": [
      { "id": 789, "score": 0.98 },
      { "id": 123, "score": 0.91 }
    ]
  }
  ```
