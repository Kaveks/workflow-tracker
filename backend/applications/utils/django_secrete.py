import secrets
import string


def generate_django_secret_key(length: int = 64) -> str:
    chars = string.ascii_letters + string.digits + string.punctuation

    # Remove characters that can break env files or shells
    chars = chars.replace('"', "").replace("'", "").replace("\\", "").replace("`", "")

    return "".join(secrets.choice(chars) for _ in range(length))


def print_secret_key():
    key = generate_django_secret_key()

    print("\n" + "." * 60)
    print(" DJANGO SECRET KEY GENERATOR")
    print("." * 30)
    print("\nCopy your SECRET_KEY below:\n")
    print(key)
    print("\n" + "." * 60)
    print("  Keep this secret. Do NOT commit it to GitHub.")
    #print("." * 60 + "\n")


if __name__ == "__main__":
    print_secret_key()