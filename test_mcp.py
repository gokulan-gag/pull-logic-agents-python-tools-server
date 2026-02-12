import asyncio
import httpx

import json

async def test_mcp():
    async with httpx.AsyncClient() as client:
        # Streamable HTTP requires specific headers
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "x-company-id": "f80d6409-cb1d-4af1-8e1c-1b90f657b9bd"  # TYM company ID
        }
        # Test list_tools
        resp = await client.post(
            "http://localhost:8000/mcp/", 
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            },
            headers=headers
        )
        print(f"List Tools Status: {resp.status_code}")
        # print(f"List Tools Response: {resp.text}")

        # Test call_tool
        async with client.stream("POST", "http://localhost:8000/mcp/", json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_demand_forecast",
                "arguments": {
                    "request": {
                        "forecast_date": "2026-12-07",
                        "region": "All"
                    }
                }
            },
            "id": 2
        }, headers=headers, timeout=30.0) as resp:
            print(f"Call Tool Status: {resp.status_code}")
            
            json_data = None
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    json_data = line.replace("data:", "").strip()
                    break # We just need the first data event for this test

            if not json_data:
                raise ValueError("No JSON data found in MCP response")

            result = json.loads(json_data)
            print("Parsed Result:", result)

            if "result" in result and "content" in result["result"]:
                content = result["result"]["content"]
                print("Content:", content)

if __name__ == "__main__":
    asyncio.run(test_mcp())
