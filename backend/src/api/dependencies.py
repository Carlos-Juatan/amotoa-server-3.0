from fastapi import Header

def get_active_account(x_active_account: str = Header(default="car-j-home")) -> str:
    """
    Dependency that extracts the active account ID from the 'X-Active-Account' header.
    Defaults to 'car-j-home' if the header is missing or unrecognized.
    """
    valid_accounts = ["car-j-works", "car-j-home"]
    if x_active_account not in valid_accounts:
        return "car-j-home"
    return x_active_account
