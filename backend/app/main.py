from fastapi import FastAPI
import uvicorn
from app.core.database import engine, Base
from app.routers import estudiantes, anios, asignaturas, periodos, asistencias, calificaciones, profesores, auth, usuarios
# Crea las tablas en MySQL automáticamente si no existen
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Control Escolar", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(estudiantes.router)
app.include_router(profesores.router)
app.include_router(anios.router)
app.include_router(asignaturas.router)
app.include_router(periodos.router)
app.include_router(asistencias.router)
app.include_router(calificaciones.router)

@app.get("/")
def read_root():
    return {"mensaje": "API de Control Escolar funcionando al 100% y conectada a HeidiSQL"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)