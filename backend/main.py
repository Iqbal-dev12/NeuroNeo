from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

import models, schemas, auth
from database import engine, get_db

# Hackathon imports for pain detection
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.database.db import Base as PainBase, engine as pain_engine, check_db_connection, MYSQL_DB
from app.routes.pain_routes import router as pain_router
from app.services.prediction_service import initialise_model
from app.utils.image_utils import UPLOAD_DIR, DEMO_SAMPLES_DIR

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and init model
    print(f"Connecting to database: {MYSQL_DB}...")
    try:
        models.Base.metadata.create_all(bind=engine)
        PainBase.metadata.create_all(bind=engine)
        print("Database tables verified/created.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    
    print("Initializing AI model...")
    try:
        initialise_model()
    except Exception as e:
        print(f"Model initialization failed: {e}")
        
    yield
    # Shutdown logic if needed

app = FastAPI(lifespan=lifespan)

# Add CORS middleware to allow React app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for static files (heatmaps, predicted images)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Mount demo_samples directory for direct sample playback
DEMO_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/demo_samples", StaticFiles(directory=str(DEMO_SAMPLES_DIR)), name="demo_samples")

# Include Pain Detection routes
app.include_router(pain_router, prefix="/api/pain")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/api/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/api/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = auth.get_password_hash(user.password)
        new_user = models.User(name=user.name, email=user.email, hashed_password=hashed_password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print("ERROR IN SIGNUP:", error_msg)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
        )
    if not auth.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
