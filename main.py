from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from typing import Optional
import requests
import pandas as pd
from datetime import datetime

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def scrape_and_generate_excel(resids):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"SwiggyMenu_{timestamp}.xlsx"

    with pd.ExcelWriter(filename) as writer:
        items = []
        for res_id in resids:
            url = f"https://www.swiggy.com/mapi/menu/pl?page-type=REGULAR_MENU&complete-menu=true&lat=19.07480&lng=72.88560&restaurantId={res_id}&catalog_qa=undefined&submitAction=ENTER"
            response = requests.get(url, headers=HEADERS)
            try:
                data = response.json()
                menu_data = data["data"]["cards"][5]["groupedCard"]["cardGroupMap"]["REGULAR"]["cards"]
                info_card = data["data"]["cards"][2]["card"]["card"]["info"]
                locality = f"{info_card.get('locality')}-{info_card.get('name')}"
            except (KeyError, IndexError):
                continue

            
            for card in menu_data:
                categories = card.get("card", {}).get("card", {}).get("categories", [])
                if len(categories) > 0:
                    for category in categories:
                        for itemCard in category.get("itemCards", []):
                            info = itemCard.get("card", {}).get("info", {})
                            price = round((info.get("price") or info.get("defaultPrice") or 0) / 100, 2)
                            finalPrice = round(info.get("finalPrice", 0) / 100, 2)
                            flashSale = "ON" if finalPrice and finalPrice < price else "OFF"
                            inStock = info.get("inStock", None)

                            imageId = info.get("imageId")
                            imageUrl = f"https://media-assets.swiggy.com/swiggy/image/upload/{imageId}" if imageId else None

                            items.append({
                                "res_id": info_card.get("id"),
                                "category": info.get("category", ""),
                                "sub-category": category.get("title", ""),
                                "name": info.get("name", ""),
                                "price": price,
                                "finalPrice": finalPrice,
                                "flashSale": flashSale,
                                "inStock": inStock,
                                "image": imageUrl,
                            })

                else:
                    categories = card.get("card", {}).get("card", {}).get("itemCards", [])
                    for itemCard in categories:
                        info = itemCard.get("card", {}).get("info", {})
                        price = round(
                            (info.get("price") or info.get("defaultPrice") or 0) / 100,
                            2,
                        )
                        finalPrice = round(info.get("finalPrice", 0) / 100, 2)
                        flashSale = "ON" if finalPrice and finalPrice < price else "OFF"
                        inStock = info.get("inStock", None)

                        imageId = info.get("imageId")
                        imageUrl = (
                            f"https://media-assets.swiggy.com/swiggy/image/upload/{imageId}"
                            if imageId
                            else None
                        )

                        items.append(
                            {
                                "res_id": info_card.get("id"),
                                "category": info.get("category", ""),
                                "sub-category": "",
                                "name": info.get("name", ""),
                                "price": price,
                                "finalPrice": finalPrice,
                                "flashSale": flashSale,
                                "inStock": inStock,
                                "image": imageUrl,
                            }
                        )

                   
        df = pd.DataFrame(items)
        df.to_excel(writer, sheet_name="All In One", index=False)

    return filename


@app.get("/swiggy/download")
def download_excel(res_id: Optional[str] = Query(...)):
    res_ids = res_id.split(",")
    file_path = scrape_and_generate_excel(res_ids)
    return FileResponse(
        file_path,
        filename=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
