import json
import boto3
import sqlite3
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from botocore.exceptions import ClientError, NoCredentialsError
import bcrypt

# --- Configuration & Security ---
SECRET_KEY = "super-secret-minnu-key-for-development"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CommandRequest(BaseModel):
    text: str

class ActionResponse(BaseModel):
    intent: str
    confidence: float
    action: str
    response_text: str

# --- App Initialization ---
app = FastAPI(
    title="Minnu Assistant API", 
    description="Backend for Minnu Voice & Gesture Assistant"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AWS boto3 SageMaker Runtime client
try:
    sagemaker_runtime = boto3.client('sagemaker-runtime')
except Exception as e:
    sagemaker_runtime = None
    print(f"Warning: Failed to initialize SageMaker Runtime client: {e}")

SAGEMAKER_ENDPOINT_NAME = "minnu-intent-classifier-endpoint"

# --- Authentication Dependency ---
def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        raise credentials_exception
    return dict(user)

# --- Routes ---

@app.post("/signup", response_model=Token)
def signup(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (user.username, user.email))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username or email already registered")
        
    hashed_password = get_password_hash(user.password)
    cursor.execute("INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)", 
                  (user.username, user.email, hashed_password))
    db.commit()
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(user: UserLogin, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    db_user = cursor.fetchone()
    
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": db_user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "account_created": "Today" # Placeholder
    }

@app.post("/process_command", response_model=ActionResponse)
async def process_command(request: CommandRequest, current_user: dict = Depends(get_current_user)):
    """
    Protected route: Only logged in users can execute commands.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Command text cannot be empty.")
    
    payload = json.dumps({"inputs": request.text})
    
    try:
        if sagemaker_runtime is None:
            return ActionResponse(
                intent="local_mock_intent",
                confidence=0.99,
                action="mock_action",
                response_text=f"Received: '{request.text}'. Executed by: {current_user['username']} (Offline Mode)"
            )

        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME,
            ContentType='application/json',
            Body=payload
        )
        
        response_body = response['Body'].read().decode('utf-8')
        sagemaker_result = json.loads(response_body)
        
        intent = sagemaker_result.get("intent", "unknown")
        confidence = sagemaker_result.get("score", 0.0)
        
        action_mapping = {
            "turn_on_lights": "trigger_lights",
            "play_music": "start_music_playback",
            "system_status": "show_status"
        }
        
        action = action_mapping.get(intent, "no_action")
        response_text = f"User {current_user['username']}, processing intent '{intent}' with confidence {confidence:.2f}"
        
        return ActionResponse(
            intent=intent,
            confidence=confidence,
            action=action,
            response_text=response_text
        )
        
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        raise HTTPException(status_code=500, detail=f"AWS ClientError: {error_code}")
    except Exception as e:
        return ActionResponse(
            intent="mock_intent",
            confidence=0.99,
            action="mock_action",
            response_text=f"Mocked response. (Error: {str(e)})"
        )

# Serve the static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
