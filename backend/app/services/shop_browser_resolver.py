from dataclasses import dataclass
import re

from fastapi import HTTPException, status

from app.core.config import get_settings

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - runtime dependency check
    PlaywrightError = Exception
    PlaywrightTimeoutError = Exception
    sync_playwright = None


@dataclass(slots=True)
class ResolvedShopIdentity:
    seller_username: str
    shop_name: str


def resolve_shop_identity(host: str, shop_slug: str) -> ResolvedShopIdentity:
    if sync_playwright is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Playwright is not installed on the backend runtime.",
        )

    settings = get_settings()
    target_url = f"https://{host}/str/{shop_slug}?_ul={settings.shop_browser_country_code}"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    "--lang=en-US",
                ],
            )
            context = browser.new_context(
                locale=settings.shop_browser_locale,
                timezone_id=settings.shop_browser_timezone_id,
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
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Sec-CH-UA-Platform": '"Windows"',
                },
            )
            context.add_cookies(
                [
                    {
                        "name": "dp1",
                        "value": f"bbl/{settings.shop_browser_country_code}67075a60^",
                        "domain": ".ebay.com",
                        "path": "/",
                    }
                ]
            )
            page = context.new_page()

            try:
                page.goto(
                    target_url,
                    wait_until="domcontentloaded",
                    timeout=int(settings.shop_browser_timeout_seconds * 1000),
                )
                page.wait_for_timeout(settings.shop_browser_wait_after_load_ms)

                html = page.content()
                requested_href = page.locator("a[href*='requested=']").first.get_attribute("href")
                if not requested_href:
                    requested_href = _extract_requested_href_from_html(html)

                seller_username = _extract_seller_username(requested_href or html)
                if not seller_username:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Could not resolve seller username from eBay store page.",
                    )

                shop_name = _extract_shop_name(page=page, html=html, fallback=shop_slug)
                return ResolvedShopIdentity(
                    seller_username=seller_username,
                    shop_name=shop_name,
                )
            finally:
                context.close()
                browser.close()
    except HTTPException:
        raise
    except (PlaywrightTimeoutError, PlaywrightError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to resolve seller username from eBay store page: {exc}",
        ) from exc


def _extract_requested_href_from_html(html: str) -> str | None:
    match = re.search(r'href="([^"]*requested=[^"]+)"', html, re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def _extract_seller_username(text: str) -> str | None:
    match = re.search(r"requested=([A-Za-z0-9_.-]+)", text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _extract_shop_name(page, html: str, fallback: str) -> str:
    heading = page.locator("h1").first.text_content()
    if heading and heading.strip():
        return heading.strip()

    link_heading = page.locator("h1 a").first.text_content()
    if link_heading and link_heading.strip():
        return link_heading.strip()

    match = re.search(r"<h1[^>]*>\s*(?:<a[^>]*>)?\s*([^<]+?)\s*(?:</a>)?\s*</h1>", html, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return fallback
