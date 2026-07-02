from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
from backend.app.db.database import get_db
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class UserRegister(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        text("SELECT * FROM users WHERE username = :u"), {"u": username}
    )
    user = result.mappings().first()
    if not user:
        raise credentials_exception
    return dict(user)


@router.post("/register", status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        text("SELECT id FROM users WHERE username = :u"), {"u": data.username}
    )
    if existing.first():
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(data.password)
    await db.execute(
        text("INSERT INTO users (username, password_hash) VALUES (:u, :p)"),
        {"u": data.username, "p": hashed}
    )
    await db.commit()
    return {"message": f"User '{data.username}' registered successfully"}


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT * FROM users WHERE username = :u"), {"u": form_data.username}
    )
    user = result.mappings().first()
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"], "id": current_user["id"]}