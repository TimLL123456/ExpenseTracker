# Google OAuth
<details>
    <summary>Google OAuth Response</summary>

```json
{
    "is_logged_in":true,
    "iss":"https://accounts.google.com",
    "azp":"3452142141242-1231j3h1kjh13h18u2h3121ujh2381hj.apps.googleusercontent.com",
    "aud":"3452142141242-1231j3h1kjh13h18u2h3121ujh2381hj.apps.googleusercontent.com",
    "sub":"1283791827391827398173918",
    "email":"test@gmail.com",
    "email_verified":true,
    "at_hash":"d979a8sd79a8s7da9adasda2312SNEA",
    "nonce":"ajlT5A879798a789798uoRznZeFy",
    "name":"Alex __",
    "picture":"https://lh3.googleusercontent.com/a/,ACgasdasdas6P_8p0uimK0PjasdasdajD-afPPA512414124m=s96-c",
    "given_name":"Alex",
    "family_name":"__",
    "iat":1754406862,
    "exp":1754410462,
}
```
</details>

1. `is_logged_in`: true
    * Indicates whether the user is successfully authenticated. A value of `true` means the OAuth flow completed, and the user is logged in.

2. `sub`: 38291739812739182731
    * The **subject**, a unique identifier for the user within Google’s system. This is a stable, non-reusable ID for the user, ideal for identifying users in your app (e.g., as a key for their expense data).