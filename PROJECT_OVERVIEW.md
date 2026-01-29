# TenaWork: AI-Powered Healthcare Job Platform

## 1. Project Description

**TenaWork** is a specialized, AI-driven job-matching platform designed exclusively for the healthcare industry. Its mission is to intelligently connect qualified health professionals with relevant health institutions, moving beyond traditional keyword-based job boards to provide a curated, high-quality matchmaking experience.

The platform's core value lies in its **bidirectional recommendation engine**. It saves time for both job seekers and employers by presenting a limited, highly relevant list of opportunities and candidates.

### Key Differentiators:
*   **AI-Powered Curation:** TenaWork uses a sophisticated hybrid AI model to analyze user profiles and job descriptions. Instead of overwhelming users with choices, it provides a curated feed: the **Top 5 most relevant jobs** for professionals and the **Top 10 most suitable candidates** for employers.
*   **Healthcare Niche Focus:** The matching algorithm is tailored to the nuances of the healthcare sector, considering factors like professional licenses, institution types, and specific health priorities, ensuring more accurate and meaningful matches.
*   **Verified Employer Ecosystem:** To ensure platform quality and safety, all employer accounts are vetted and approved by a platform administrator before they are allowed to post jobs.

### Target Audience:
*   **Health Professionals (Candidates):** Doctors, nurses, specialists, technicians, and other healthcare workers seeking employment opportunities.
*   **Health Institutions (Employers):** Hospitals, clinics, private practices, and other healthcare organizations looking to hire talent.

---

## 2. AI Matching Engine: Architecture & Workflow

The heart of TenaWork's intelligence is its AI system. This system is composed of two main parts: a deep learning **AI Model** that understands language, and a fast **Database Search Function** that finds matches.

### The Two Roles of "AI"

It's helpful to think of the AI system as a team of two specialists:

1.  **The "Translator" (The AI Model):** This is a deep learning model (e.g., from an API like OpenRouter or a self-hosted open-source model). Its only job is to read human language—like a job description or a professional's bio—and translate it into a meaningful list of numbers called a **vector** or an **embedding**. This process is the core "intelligent" act. The model understands context and semantics, so it knows that "ER experience" and "emergency room background" mean similar things and gives them similar vectors. This translation is handled by our **AI Engine (Python/Flask) service**.

2.  **The "Retriever" (The Database):** Once every job and profile has been translated into a vector, finding matches is a mathematical problem: "Find the vectors that are closest to this one." This is not a thinking task; it's a high-speed search task. We use a specialized database extension (like `pgvector` for PostgreSQL) that can perform this "nearest neighbor" search incredibly quickly.

### How it Works in Practice

#### A. Generating and Storing Vectors (The "Write Path")

This happens whenever a new job is posted or a profile is updated.

1.  A user saves a job or profile on the **Frontend**.
2.  The data is sent to the **Backend API**, which saves the text (title, description, etc.) into the main database.
3.  The **Backend** then calls the **AI Engine**'s `/generate-embedding` endpoint, sending the new text.
4.  The **AI Engine** takes the text, uses the **AI Model (The "Translator")** to convert it into a vector.
5.  The **AI Engine** returns this vector to the **Backend**.
6.  The **Backend** saves this vector into a special column in the database right next to the text it represents.

#### B. Searching for Recommendations (The "Read Path")

This happens when a user wants to see their recommendations.

1.  A user visits the "Recommended Jobs" page on the **Frontend**.
2.  The **Backend API** gets the request and fetches the user's pre-calculated `profile_vector` from the database.
3.  The **Backend** then calls the **AI Engine**'s `/recommend-jobs` endpoint, sending **only the user's vector**.
4.  **This is the key step:** The **AI Engine** receives the vector and now acts as the "Retriever." It connects to the database and executes a highly-efficient query. This query asks the database directly: `"Find the 5 job IDs whose vectors are mathematically closest to the profile vector I'm providing."`
5.  The database does the high-speed search and returns the 5 best matching `job_id`s to the **AI Engine**.
6.  The **AI Engine** returns this list of IDs to the **Backend**.
7.  The **Backend** fetches the full details for those 5 jobs and sends them to the **Frontend** to be displayed.

This two-step process (AI translates, Database retrieves) creates a powerful, scalable, and maintainable system for semantic search.

---

## 3. Detailed User Workflows

### A. The Health Professional (Candidate) Journey

The workflow for a candidate is focused on ease of use and discovering relevant opportunities.

1.  **Onboarding & Profile Creation:**
    *   The user registers for a "Professional" account.
    *   They are guided through a profile-building process to input:
        *   Basic personal information and a professional headline/bio.
        *   Structured **Education** history (multiple entries allowed).
        *   Structured **Work Experience** history (multiple entries allowed).
        *   A section to upload their **Resume** file.

2.  **AI-Powered Job Discovery:**
    *   Upon navigating to the "Browse Jobs" page, the candidate is **not** shown a generic list.
    *   Instead, the AI engine analyzes their complete profile in real-time and presents them with a personalized feed of the **Top 5 most relevant jobs** currently available on the platform.

3.  **Application Process:**
    *   The candidate clicks on a job to view its detailed description.
    *   If interested, they click "Apply," which opens a simple form where they can write a **Cover Letter**.
    *   Upon submission, an `Application` record is created.

4.  **Application Tracking:**
    *   The candidate can navigate to their "My Applications" dashboard at any time.
    *   This dashboard displays a list of every job they have applied for and the real-time status of each application:
        *   **Pending:** The application has been submitted, but the employer has not yet viewed it.
        *   **Viewed:** The employer has seen the application in their list of candidates.
        *   **Shortlisted:** The employer has marked the candidate as a person of interest.

### B. The Employer/Recruiter Journey

The workflow for an employer is designed for efficient and high-quality talent discovery.

1.  **Onboarding & Verification:**
    *   The user registers for an "Employer" account.
    *   They fill out their company profile with details like company name, description, location, and logo.
    *   **Crucially, their account enters a `Pending Approval` state.** They cannot post jobs yet. Their dashboard displays a message indicating their profile is under review.

2.  **Job Posting (Post-Approval):**
    *   Once a Platform Administrator approves their account, the "Post a Job" functionality is unlocked.
    *   The employer fills out a detailed form describing the job role, requirements, salary, location, etc.

3.  **Instant AI Recommendations:**
    *   Immediately after the job is posted, the employer is redirected to a results page.
    *   This page displays the **Top 10 most suitable candidates** from the platform's user base, as determined by the AI matching engine. This allows employers to be proactive and contact strong candidates without waiting for applications to come in.

4.  **Applicant Management:**
    *   From their dashboard, the employer can select a job post to view the list of candidates who have applied directly.
    *   The act of viewing this list automatically updates the status of new applications from `Pending` to `Viewed`.
    *   The employer can review each applicant's full profile (including their resume) and cover letter.

5.  **Shortlisting:**
    *   While reviewing applicants, the employer can click a "Shortlist" button on promising candidates. This updates the application's status and provides a clear signal to both the employer and the candidate.

### C. The Platform Administrator Journey

The administrator's workflow is focused on maintaining platform quality and oversight.

1.  **Employer Verification:**
    *   The admin logs into a secure dashboard.
    *   The dashboard has a section listing all employers with a `Pending Approval` status.
    *   The admin can review each company profile and click "Approve" or "Reject" to control their access to the platform.

2.  **Platform Monitoring:**
    *   The admin dashboard displays high-level analytics, such as:
        *   Total number of registered professionals.
        *   Total number of approved employers.
        *   Total number of active job posts.
        *   Total number of applications submitted.