from typing import Any


def mask_email(email: str) -> str:
    """
    Mask an email address.

    Example:
    thabo@example.com -> t***@example.com
    """
    if not email or "@" not in email:
        return "MASKED"

    local_part, domain = email.split("@", 1)

    if len(local_part) <= 1:
        return f"*@{domain}"

    return f"{local_part[0]}***@{domain}"


def mask_full_name(full_name: str) -> str:
    """
    Partially mask a full name.

    Example:
    Thabo Mokoena -> Thabo M.
    """
    if not full_name:
        return "MASKED"

    parts = full_name.strip().split()

    if len(parts) == 1:
        return parts[0]

    first_name = parts[0]
    surname_initial = parts[-1][0].upper()

    return f"{first_name} {surname_initial}."


def mask_customer_record_by_role(record: Any, role: str) -> Any:
    """
    Mask customer data based on user role.

    support_agent:
        - sees partially masked name and email

    admin:
        - sees full data

    auditor:
        - sees customer identity fully masked
    """
    if not isinstance(record, dict):
        return record

    role = role.strip().lower()

    masked_record = record.copy()

    if role == "admin":
        return masked_record

    if role == "support_agent":
        if "full_name" in masked_record:
            masked_record["full_name"] = mask_full_name(masked_record["full_name"])

        if "email" in masked_record:
            masked_record["email"] = mask_email(masked_record["email"])

        return masked_record

    if role == "auditor":
        if "full_name" in masked_record:
            masked_record["full_name"] = "MASKED"

        if "email" in masked_record:
            masked_record["email"] = "MASKED"

        return masked_record

    # Unknown roles get safest output.
    if "full_name" in masked_record:
        masked_record["full_name"] = "MASKED"

    if "email" in masked_record:
        masked_record["email"] = "MASKED"

    return masked_record
