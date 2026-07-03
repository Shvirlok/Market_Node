import asyncio
import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from fastapi.responses import JSONResponse
from scraper import search_market_data
from llm_service import analyze_scraped_data, compare_projects

app = FastAPI(title="MarketNode API Backend", version="1.0.0")

# Enable CORS middleware to allow cross-origin requests for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/analyze")
async def analyze(
    project_name: str = Query(..., description="The name of the project to analyze")
) -> Dict[str, Any]:
 
    try:
        is_major_l1 = project_name.lower() in ['bitcoin', 'btc', 'ethereum', 'eth']
        
        if project_name.lower() in ['bitcoin', 'btc']:
            # Locked strictly to Bitcoin Core metrics with negative keywords
            query_l1 = f"{project_name} core metrics, macro ETF inflows 2026, post-halving block rewards -monero -xmr"
            search_queries = [query_l1]
        elif project_name.lower() in ['ethereum', 'eth']:
            query_l1 = f"{project_name} current inflation rate 2026, network emission curve, block rewards schedule, institutional inflows 2026"
            search_queries = [query_l1]
        else:
            # Standard DePIN search queries
            query_hype = f"{project_name} (crypto OR DePIN) (site:twitter.com OR site:reddit.com) recent discussions, community sentiment, FUD, leaks"
            query_finance = f"{project_name} tokenomics funding round Crunchbase Messari allocation valuation metrics"
            query_tech = f"{project_name} Blackbird node issues, hardware delays, network complaints, github speed"
            query_competitors = f"{project_name} vs Helium vs IoTeX market share, community drama, comparison"
            
            search_queries = [query_hype, query_finance, query_tech, query_competitors]
            
            is_microcap = project_name.lower() not in ["helium", "render", "chirp", "iotex", "solana"]
            if is_microcap:
                query_whale = f"{project_name} (crypto OR DePIN) site:dexscreener.com OR site:alphagaindaily.com liquidity lock, whale concentration, contract address, rugpull history"
                search_queries.append(query_whale)

        # Execute searches concurrently
        tasks = [search_market_data(q) for q in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten search results
        flat_results = []
        for r in results:
            if isinstance(r, list):
                flat_results.extend(r)
            elif isinstance(r, Exception):
                print(f"Parallel search exception occurred: {r}")

        if not flat_results:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "project": project_name,
                    "message": "Scraped data is empty or scraping failed across all topics"
                }
            )
        
        llm_result = await analyze_scraped_data(project_name, flat_results)
        return {
            "status": "success",
            "project": project_name,
            "analysis": llm_result.get("analysis", {}),
            "sources_manifest": llm_result.get("sources_manifest", {})
        }
    except Exception as exc:
        return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "project": project_name,
                    "message": f"Server error: {str(exc)}"
                }
        )

@app.get("/api/v1/battle")
async def battle(
    project_a: str = Query(..., description="First project to compare"),
    project_b: str = Query(..., description="Second project to compare")
) -> Dict[str, Any]:
    try:
        # Construct Project A queries
        is_a_btc = project_a.lower() in ['bitcoin', 'btc']
        is_a_l1 = project_a.lower() in ['bitcoin', 'btc', 'ethereum', 'eth']
        
        if is_a_btc:
            queries_a = [f"{project_a} core metrics, macro ETF inflows 2026, post-halving block rewards -monero -xmr"]
        elif is_a_l1:
            queries_a = [f"{project_a} current inflation rate 2026, network emission curve, block rewards schedule, institutional inflows 2026"]
        else:
            queries_a = [
                f"{project_a} (crypto OR DePIN) (site:twitter.com OR site:reddit.com) recent discussions, community sentiment, FUD, leaks",
                f"{project_a} tokenomics funding round Crunchbase Messari allocation valuation metrics",
                f"{project_a} Blackbird node issues, hardware delays, network complaints, github speed",
                f"{project_a} vs Helium vs IoTeX market share, community drama, comparison"
            ]
            is_a_micro = project_a.lower() not in ["helium", "render", "chirp", "iotex", "solana"]
            if is_a_micro:
                queries_a.append(f"{project_a} (crypto OR DePIN) site:dexscreener.com OR site:alphagaindaily.com liquidity lock, whale concentration, contract address, rugpull history")

        # Construct Project B queries
        is_b_btc = project_b.lower() in ['bitcoin', 'btc']
        is_b_l1 = project_b.lower() in ['bitcoin', 'btc', 'ethereum', 'eth']
        
        if is_b_btc:
            queries_b = [f"{project_b} core metrics, macro ETF inflows 2026, post-halving block rewards -monero -xmr"]
        elif is_b_l1:
            queries_b = [f"{project_b} current inflation rate 2026, network emission curve, block rewards schedule, institutional inflows 2026"]
        else:
            queries_b = [
                f"{project_b} (crypto OR DePIN) (site:twitter.com OR site:reddit.com) recent discussions, community sentiment, FUD, leaks",
                f"{project_b} tokenomics funding round Crunchbase Messari allocation valuation metrics",
                f"{project_b} Blackbird node issues, hardware delays, network complaints, github speed",
                f"{project_b} vs Helium vs IoTeX market share, community drama, comparison"
            ]
            is_b_micro = project_b.lower() not in ["helium", "render", "chirp", "iotex", "solana"]
            if is_b_micro:
                queries_b.append(f"{project_b} (crypto OR DePIN) site:dexscreener.com OR site:alphagaindaily.com liquidity lock, whale concentration, contract address, rugpull history")

        # Execute parallel searches
        tasks = [search_market_data(q) for q in queries_a + queries_b]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        split_idx = len(queries_a)
        flat_a = []
        for r in results[:split_idx]:
            if isinstance(r, list):
                flat_a.extend(r)
        
        flat_b = []
        for r in results[split_idx:]:
            if isinstance(r, list):
                flat_b.extend(r)
        
        llm_result = await compare_projects(project_a, flat_a, project_b, flat_b)
        
        return {
            "status": "success",
            "comparison": llm_result.get("comparison", {}),
            "sources_manifest": llm_result.get("sources_manifest", {})
        }
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Server error during competitor battle: {str(exc)}"
            }
        )

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
