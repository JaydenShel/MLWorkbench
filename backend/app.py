from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.upload_router import router as upload_router

app = FastAPI(
    title="ML Directory API",
    description="A FastAPI application for machine learning dataset management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)


@app.get("/")
def read_root():
    return {
        "message": "ML Directory API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ml-directory-api"}
