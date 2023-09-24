# Scribd Audiobook Downloader

Updated: Allows downloading ebooks and audio book with embed artwork

## Requirements

These libs below must be installed!!!

```
pip install playwright requests mutagen PyPDF2
playwright install
```

## Usage

1. Run the script:

```
python3 main.py
```

or

```
py audioBook.py
```

2. Then a browser will be opened, continue your sign in.
   `Note that` after signing in, a session will be created for that account so you do not have to sign in again in the next time you use this.
   Consequently, if you want to sign in using a new account, please `delete` the file named `"session.json"`

3. After that, it will ask you to enter the link of the audiobook or ebook, proceed to do so.

4. Now, just wait for the file to download!
   `P/s`: The files name is based on how they are named on Scribd, therefore if you want to rename them, be my guest
