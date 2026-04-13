import re

from app.core.config import get_settings

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - runtime dependency check
    PlaywrightError = Exception
    PlaywrightTimeoutError = Exception
    sync_playwright = None


class ShopListingSalesService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_sales_summary(self, item_url: str) -> str | None:
        if sync_playwright is None:
            return None

        target_url = item_url if "_ul=" in item_url else f"{item_url}{'&' if '?' in item_url else '?'}_ul=US"

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    executable_path=playwright.chromium.executable_path,
                    args=["--lang=en-US"],
                )
                context = browser.new_context(
                    locale=self.settings.shop_browser_locale,
                    timezone_id=self.settings.shop_browser_timezone_id,
                    geolocation={
                        "latitude": 40.7128,
                        "longitude": -74.0060,
                        "accuracy": 100,
                    },
                    permissions=["geolocation"],
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1440, "height": 2200},
                    extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                )
                context.add_cookies(
                    [
                        {
                            "name": "dp1",
                            "value": f"bbl/{self.settings.shop_browser_country_code}67075a60^",
                            "domain": ".ebay.com",
                            "path": "/",
                        }
                    ]
                )
                page = context.new_page()
                page.goto(
                    target_url,
                    wait_until="domcontentloaded",
                    timeout=int(self.settings.shop_browser_timeout_seconds * 1000),
                )
                page.wait_for_timeout(self.settings.shop_browser_wait_after_load_ms)
                html = page.content()
                context.close()
                browser.close()
        except (PlaywrightTimeoutError, PlaywrightError):
            return None

        for pattern in [r"([0-9][0-9,]*)\s+sold", r"([0-9][0-9,]*)\s+已售", r"last one sold"]:
            match = re.search(pattern, html, re.IGNORECASE)
            if not match:
                continue
            text = match.group(0).strip()
            if text:
                return text[0].upper() + text[1:]

        return None
