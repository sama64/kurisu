from personal_google_auth import PersonalGoogleAuth

if __name__ == "__main__":
    credentials_path = "credentials.json"
    token_save_path = "token.json"
    
    # open browser once for authorization
    PersonalGoogleAuth.generate_persistent_token(
        credentials_path=credentials_path,
        token_save_path=token_save_path
    )