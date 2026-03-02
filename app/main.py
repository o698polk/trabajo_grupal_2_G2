from fastapi import FastAPI, Depends, Request, Form, HTTPException, status, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import models, auth, crud, scraping
from .models import engine, get_db
from datetime import timedelta
import os
from jose import JWTError, jwt
from .config import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Initialize admin user
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    crud.create_admin_user(db)

# Middlewares or Dependency to get user from JWT in cookies
def get_current_user_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        # print("DEBUG: No access_token found in cookies")
        return None
    
    payload = auth.decode_access_token(token)
    if not payload:
        print("DEBUG: Token invalid or expired")
        return None
    
    username: str = payload.get("sub")
    if username is None:
        print("DEBUG: No 'sub' in token payload")
        return None
    
    user = crud.get_user_by_username(db, username=username)
    if not user:
        print(f"DEBUG: User '{username}' not found in DB")
    return user

@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: models.User = Depends(get_current_user_cookie)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=username)
    if not user or not auth.verify_password(password, user.hashed_password):
      
        return RedirectResponse(url="/login?error=invalid", status_code=status.HTTP_302_FOUND)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
   
    redirect_resp = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
   
    redirect_resp.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False 
    )
    print(f"DEBUG: Login successful for '{username}', cookie set.")
    return redirect_resp

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: models.User = Depends(get_current_user_cookie), db: Session = Depends(get_db)):
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    products = crud.get_all_products(db)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user, "products": products})

@app.get("/api/search")
def search(query: str, current_user: models.User = Depends(get_current_user_cookie), db: Session = Depends(get_db)):
    if not current_user or current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")
    
    results = scraping.scrape_mercadolibre(query)
    
   
    if results:
      
        for res in results:
            db_product = models.ProductResult(
                query=query,
                name=res["name"],
                price=res["price"],
                link=res["link"]
            )
            db.add(db_product)
        db.commit()
        
    
    return  results

@app.get("/api/download/{filename}")
async def download_csv(filename: str, current_user: models.User = Depends(get_current_user_cookie)):
    if not current_user or current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Not authorized")
    
    file_path = os.path.join("csv_archivos", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(path=file_path, filename=filename, media_type='text/csv')
