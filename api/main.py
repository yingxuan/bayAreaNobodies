from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.database import engine, Base
from app.routers import auth, trending, articles, engagement, holdings, portfolio, stocks, coupons, digests, feeds, food, deals, deals_food, gossip, wealth, market, tech, risk
from app.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="湾区牛马日常 API",
    description="API for trending feeds, portfolio, and coupons",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://web:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(trending.router, prefix="/trending", tags=["trending"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(engagement.router, prefix="/engagement", tags=["engagement"])
app.include_router(holdings.router, prefix="/holdings", tags=["holdings"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
app.include_router(coupons.router, prefix="/coupons", tags=["coupons"])
app.include_router(digests.router, prefix="/digests", tags=["digests"])
app.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
app.include_router(food.router, prefix="/food", tags=["food"])
app.include_router(deals.router, prefix="/deals", tags=["deals"])
app.include_router(deals_food.router, prefix="/deals", tags=["deals"])
app.include_router(gossip.router, prefix="/gossip", tags=["gossip"])
app.include_router(wealth.router, prefix="/wealth", tags=["wealth"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(tech.router, prefix="/tech", tags=["tech"])
app.include_router(risk.router, prefix="/risk", tags=["risk"])


@app.get("/")
async def root():
    return {"message": "湾区牛马日常 API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

