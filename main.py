from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from typing import Optional
import requests
import pandas as pd
from datetime import datetime

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.swiggy.com/",
    "Cookie": "WZRK_G=086b3c59fe63480daf8e7108511ed31f; __SW=a_SkBHYZHnm2Ro6_oOQWd3ktyDzEhMqG; _device_id=5881468d-f17e-551c-fb2d-e9010f2c2e53; _gcl_au=1.1.1963417137.1753103661; _ga_7JY7T788PK=GS2.1.s1757746805^$o1^$g1^$t1757746822^$j43^$l0^$h0; fontsLoaded=1; deviceId=s%3A5881468d-f17e-551c-fb2d-e9010f2c2e53.VxZHYeExnINfigR8PsrYW%2FE8mgnwx3WrxzHANp8ZCyc; versionCode=1200; platform=web; subplatform=dweb; statusBarHeight=0; bottomOffset=0; genieTrackOn=false; isNative=false; openIMHP=false; webBottomBarHeight=0; _fbp=fb.1.1758266058545.984279149937980703; tid=s%3A938dae07-2799-487d-bbe7-0d3c926f02d1.vkxPwSEhjqz8iBowIWKKzLTznj2ugkDcabw4i7kqdXA; userLocation=%7B%22lat%22%3A19.10549861498898%2C%22lng%22%3A72.88718238354151%2C%22address%22%3A%22Sag%20Baug%2C%20Marol%2C%20Andheri%20East%2C%20Mumbai%2C%20Maharashtra%2C%20India%22%2C%22id%22%3A%22%22%2C%22annotation%22%3A%22Sag%20Baug%2C%20Marol%2C%20Andheri%20East%2C%20Mumbai%2C%20Maharashtra%2C%20India%22%2C%22name%22%3A%22%22%7D; _ga_VEG1HFE5VZ=GS2.1.s1759993813^$o2^$g1^$t1759993949^$j60^$l0^$h0; _ga_0XZC5MS97H=GS2.1.s1759993813^$o2^$g1^$t1759993949^$j60^$l0^$h0; _ga_8N8XRG907L=GS2.1.s1759993812^$o2^$g1^$t1759993974^$j35^$l0^$h0; _guest_tid=f9cc2116-e348-4550-9a82-cafbfb28e4ff; _sid=ncf93b59-439a-48c4-9a7d-ccf27f3fb8a0; _gid=GA1.2.425038350.1760089171; aws-waf-token=0c5756e0-bb6f-43ff-a1d0-da2a78f63a37:BQoAr0hDR8wzAAAA:HcinXYQa2J+tI8qjdoMegrDdG8oPnv0eF30WRMoPemtUVkjY1CuG8xdSLHXqfGxvw+bPZcISJxhjPBMP/O9px22xVkD3Rm752qSIO86F5yvgeVrAZ2UcshdvNqLEwItPqUaZBTDuHBJzE2EmFkBa8xZoMmzG8HZhQ1/A8HOdx0z6OTe+Es+pfdPHbsIPl6c1BpYvQAf5ZAz0McwipsoVc7GDWp++Nc3Y5caXMPT6OvBUoCy4Zd4l; _gat_0=1; _ga=GA1.1.153191328.1753103661; _ga_YE38MFJRBZ=GS2.1.s1760089170^$o12^$g1^$t1760089381^$j59^$l0^$h0; _ga_34JYJ0BCRN=GS2.1.s1760089171^$o12^$g1^$t1760089381^$j59^$l0^$h0; _device_id=5881468d-f17e-551c-fb2d-e9010f2c2e53",
}


def scrape_and_generate_excel(resids):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"SwiggyMenu_{timestamp}.xlsx"

    with pd.ExcelWriter(filename) as writer:
        items = []
        for res_id in resids:
            url = f"https://www.swiggy.com/dapi/menu/pl?page-type=REGULAR_MENU&complete-menu=true&lat=19.07480&lng=72.88560&restaurantId={res_id}&catalog_qa=undefined&submitAction=ENTER"
            response = requests.get(url, headers=HEADERS)
            try:
                data = response.json()
                menu_data = data["data"]["cards"][4]["groupedCard"]["cardGroupMap"]["REGULAR"]["cards"]
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
