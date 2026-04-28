# AI Website Builder Backend - Complete Function Reference

## Database Functions

### `get_db()`
- **Type:** `async def get_db() -> AsyncGenerator[AsyncConnection, None]`
- **Purpose:** Creates and manages database connection pool for Neon PostgreSQL
- **Returns:** Async database connection

### `execute_user_db_schema()`
- **Type:** `async def execute_user_db_schema(conn_string: str, schema_sql: str) -> Tuple[bool, Optional[str]]`
- **Purpose:** Executes SQL schema on user's Neon database
- **Returns:** `(success: bool, error: Optional[str])`

### `mask_db_connection()`
- **Type:** `def mask_db_connection(conn_string: str) -> str`
- **Purpose:** Masks database connection string for secure logging
- **Returns:** Masked string like `"username@********@host"`

---

## Authentication Functions

### `verify_password()`
- **Type:** `def verify_password(plain_password: str, hashed_password: str) -> bool`
- **Purpose:** Verifies a plain text password against a hashed password
- **Returns:** Boolean (True if password matches)

### `get_password_hash()`
- **Type:** `def get_password_hash(password: str) -> str`
- **Purpose:** Hashes a password using bcrypt
- **Returns:** Hashed password string

### `create_access_token()`
- **Type:** `def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str`
- **Purpose:** Creates JWT access token for authentication
- **Returns:** JWT token string

### `decode_access_token()`
- **Type:** `def decode_access_token(token: str) -> Optional[dict]`
- **Purpose:** Decodes and validates JWT token
- **Returns:** Payload dictionary or None if invalid

---














// Preview Generation Functions






### `generate_preview_internal()`
- **Type:** `async def generate_preview_internal(files: Dict[str, Any], project_name: str) -> Dict[str, Any]`
- **Purpose:** Generates fully interactive HTML preview using AI with dark theme
- **Returns:** `{"success": bool, "preview_html": str, "preview_type": str}`

### `get_preview_html()`
- **Type:** `def get_preview_html(html_content: str) -> str`
- **Purpose:** Wraps HTML fragment in complete document with Tailwind CSS
- **Returns:** Complete HTML document

### `extract_tsx_content()`
- **Type:** `def extract_tsx_content(content: str, route_name: str) -> str`
- **Purpose:** Extracts JSX/HTML from Next.js TypeScript files
- **Returns:** Cleaned HTML content

### `clean_jsx_output()`
- **Type:** `def clean_jsx_output(jsx: str, route_name: str) -> str`
- **Purpose:** Converts JSX to valid HTML
- **Returns:** Cleaned HTML string

### `create_simple_preview()`
- **Type:** `def create_simple_preview(files: Dict[str, Any], project_name: str) -> str`
- **Purpose:** Creates fallback HTML preview when AI generation fails
- **Returns:** Simple HTML document

---











## AI Model Management Functions

### `load_api_keys()`
- **Type:** `def load_api_keys() -> List[Dict]`
- **Purpose:** Loads Gemini API keys from environment variables
- **Returns:** List of API key configurations

### `get_next_key()`
- **Type:** `async def get_next_key(model: str = DEFAULT_MODEL) -> Optional[Dict]`
- **Purpose:** Retrieves next available API key with rate limiting
- **Returns:** API key configuration or None

### `generate_content_with_retry()`
- **Type:** `async def generate_content_with_retry(prompt: str, config: Dict, max_retries: int = 3) -> str`
- **Purpose:** Generates AI content with automatic retry on failure
- **Returns:** Generated text response

### `generate_website_structure()`
- **Type:** `async def generate_website_structure(prompt: str) -> Dict`
- **Purpose:** Generates website structure (pages, navigation) from user prompt
- **Returns:** Website structure dictionary

### `generate_page_content()`
- **Type:** `async def generate_page_content(description: str, structure: Dict) -> str`
- **Purpose:** Generates HTML/CSS content for specific pages
- **Returns:** Page HTML content

---

## File Processing Functions

### `extract_code_from_response()`
- **Type:** `def extract_code_from_response(response: str) -> str`
- **Purpose:** Extracts clean code from AI response (removes markdown)
- **Returns:** Clean code string

### `clean_html_response()`
- **Type:** `def clean_html_response(response: str) -> str`
- **Purpose:** Cleans HTML response from AI (removes markdown wrappers)
- **Returns:** Clean HTML string

### `infer_files_from_request()`
- **Type:** `def infer_files_from_request(edit_description: str, source_files: Dict) -> List[str]`
- **Purpose:** Infers which files to edit based on edit description
- **Returns:** List of file paths

---

## Page Generation Functions

### `generate_login_page()`
- **Type:** `def generate_login_page() -> str`
- **Purpose:** Generates complete login page with API integration
- **Returns:** React/Next.js login page component

### `generate_signup_page()`
- **Type:** `def generate_signup_page() -> str`
- **Purpose:** Generates complete signup page with API integration
- **Returns:** React/Next.js signup page component

### `generate_navigation_with_auth()`
- **Type:** `def generate_navigation_with_auth() -> str`
- **Purpose:** Generates navigation component with authentication links
- **Returns:** React/Next.js navigation component

### `generate_env_file()`
- **Type:** `def generate_env_file(conn_string: str) -> str`
- **Purpose:** Generates .env file with database configuration
- **Returns:** .env file content

### `generate_new_page_content()`
- **Type:** `def generate_new_page_content(file_path: str) -> str`
- **Purpose:** Generates default content for new pages
- **Returns:** React component code

---










// Image Processing Functions









### `fetch_images_from_pexels()`
- **Type:** `async def fetch_images_from_pexels(query: str, per_page: int = 3) -> List[Dict]`
- **Purpose:** Fetches images from Pexels API based on search query
- **Returns:** List of image data objects

### `download_and_save_image()`
- **Type:** `async def download_and_save_image(url: str, path: str) -> bool`
- **Purpose:** Downloads image and saves to project files
- **Returns:** Boolean indicating success

### `inject_base64_images()`
- **Type:** `def inject_base64_images(html: str, files: Dict) -> str`
- **Purpose:** Injects base64 encoded images into HTML preview
- **Returns:** HTML with inline images

---

## WebSocket Functions

### `websocket_endpoint()`
- **Type:** `@app.websocket("/ws/build") async def websocket_endpoint(websocket: WebSocket)`
- **Purpose:** Handles real-time build progress via WebSocket
- **Features:** Sends file generation updates, progress percentage

---










// API Endpoints






### `@app.post("/api/save-project")`
- **Purpose:** Saves project to database and Cloudinary
- **Returns:** `{"success": bool, "id": str, "preview_url": str, "files_url": str}`

### `@app.get("/api/get-projects")`
- **Purpose:** Retrieves all projects for authenticated user
- **Returns:** `{"success": bool, "projects": List[SavedProject]}`

### `@app.delete("/api/delete-project/{project_id}")`
- **Purpose:** Deletes project from database and Cloudinary
- **Returns:** `{"success": bool, "message": str}`

### `@app.post("/api/edit-file")`
- **Purpose:** Intelligent AI-powered file editing with database integration
- **Returns:** `{"success": bool, "edits": List, "preview_html": str}`

### `@app.get("/api/credits")`
- **Purpose:** Gets user's available credits
- **Returns:** `{"dailyRemaining": int, "monthlyRemaining": int, "plan": str}`

### `@app.post("/api/credits/deduct")`
- **Purpose:** Deducts credits for AI operations
- **Returns:** `{"success": bool, "remaining": int}`

### `@app.post("/api/auth/signup")`
- **Purpose:** Registers new user with Neon database
- **Returns:** `{"success": bool, "user": dict, "access_token": str}`

### `@app.post("/api/auth/login")`
- **Purpose:** Authenticates existing user
- **Returns:** `{"success": bool, "user": dict, "access_token": str}`

### `@app.get("/api/auth/verify")`
- **Purpose:** Verifies JWT token validity
- **Returns:** `{"success": bool, "user": dict}`

### `@app.post("/api/generate-preview")`
- **Purpose:** Generates HTML preview from project files
- **Returns:** `{"success": bool, "preview_html": str}`

### `@app.post("/api/deploy-vercel")`
- **Purpose:** Deploys project to Vercel
- **Returns:** `{"success": bool, "deployment_url": str}`

---

## Utility Functions

### `reconstruct_preview()`
- **Type:** `def reconstruct_preview(updated_files: Dict[str, str]) -> str`
- **Purpose:** Reconstructs preview HTML from edited source files
- **Returns:** Preview HTML string

### `clean_json_response()`
- **Type:** `def clean_json_response(response: str) -> str`
- **Purpose:** Extracts JSON from AI response with markdown wrappers
- **Returns:** Clean JSON string

### `generate_project_name()`
- **Type:** `def generate_project_name(prompt: str, existing_names: List[str]) -> str`
- **Purpose:** Generates unique project name from prompt
- **Returns:** Unique project name string

### `get_file_language()`
- **Type:** `def get_file_language(filename: str) -> str`
- **Purpose:** Determines syntax highlighting language from file extension
- **Returns:** Language string for syntax highlighter

### `check_and_deduct_credits()`
- **Type:** `async def check_and_deduct_credits(user_id: str, credits: int) -> bool`
- **Purpose:** Checks and deducts credits for AI operations
- **Returns:** Boolean indicating if operation can proceed

### `load_credits()`
- **Type:** `async def load_credits(user_id: str) -> Dict`
- **Purpose:** Loads user's current credit balance
- **Returns:** Credit information dictionary

### `save_to_cloudinary()`
- **Type:** `async def save_to_cloudinary(content: str, folder: str, public_id: str) -> str`
- **Purpose:** Uploads content to Cloudinary
- **Returns:** Cloudinary URL

### `generate_thumbnail_from_html()`
- **Type:** `async def generate_thumbnail_from_html(html_content: str, project_id: str) -> Optional[str]`
- **Purpose:** Generates thumbnail screenshot using Playwright
- **Returns:** Thumbnail URL or None

### `get_storage_size()`
- **Type:** `def get_storage_size() -> int`
- **Purpose:** Calculates localStorage size used by projects
- **Returns:** Size in bytes

### `clear_old_projects()`
- **Type:** `def clear_old_projects() -> None`
- **Purpose:** Clears old projects to free localStorage space
- **Returns:** None

---

## Error Handlers

### `@app.exception_handler(HTTPException)`
- **Purpose:** Handles HTTP exceptions with proper JSON responses

### `@app.exception_handler(Exception)`
- **Purpose:** Global exception handler for uncaught errors

---

## Middleware

### `auth_middleware()`
- **Type:** `@app.middleware("http") async def auth_middleware(request: Request, call_next)`
- **Purpose:** Authenticates requests for protected endpoints
- **Features:** JWT token validation, public path whitelist

### `cors_middleware()`
- **Type:** `@app.middleware("http") async def cors_middleware(request: Request, call_next)`
- **Purpose:** Handles CORS headers for frontend requests

---

## Startup/Shutdown Events

### `startup_event()`
- **Type:** `@app.on_event("startup") async def startup_event()`
- **Purpose:** Initializes database connection pool on startup

### `shutdown_event()`
- **Type:** `@app.on_event("shutdown") async def shutdown_event()`
- **Purpose:** Closes database connections gracefully on shutdown