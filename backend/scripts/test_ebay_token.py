from app.services.ebay_client import get_access_token


def main() -> None:
    token = get_access_token(debug=True)
    print(f"Access Token Prefix: {token[:18]}...")


if __name__ == "__main__":
    main()
