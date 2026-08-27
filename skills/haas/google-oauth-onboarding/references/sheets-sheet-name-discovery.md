# Google Sheets API — Sheet Name Discovery Pattern

## The Problem

Sheet names in Google Sheets can contain special characters (spaces, quotes, accents) and users rename them. Hardcoding a sheet name like `"Mirna's Team"` will fail if the user renamed it to `"HaaS Teams"`.

## The Pattern: Always Discover First

Before accessing ANY range, hit the spreadsheet metadata endpoint:

```python
import json, urllib.request

spreadsheet_id = "1tcQd0H-LBKLJ-SJJqoctBKt1UNwW_pHQ_CTNQcvFfgk"
url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"

req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer" + " " + access_token)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

for sheet in data['sheets']:
    title = sheet['properties']['title']
    sheet_id = sheet['properties']['sheetId']
    print(f"Sheet: {title!r} (ID: {sheet_id})")
```

## A1 Notation for Special Characters

Sheet names with spaces, quotes, or special characters need to be wrapped in single quotes in A1 notation:

```
Correct: 'Mirna\'s Team'!A1:G10
Correct: HaaS Teams!A1:G10       (no special chars beyond space)
Wrong:   Mirna's Team!A1:G10      (single quote breaks parsing)
```

URL-encode the entire range string (the API handles the wrapping):

```python
import urllib.parse
sheet_name = "HaaS Teams"
encoded = urllib.parse.quote(sheet_name, safe='')
range_str = f"{encoded}!A1:G15"
```

## Pitfall: Ranges vs Values endpoints

- `/values/{range}` — simple reads/writes, auto-detects majorDimension
- `/values:batchGet` — multiple ranges in one call
- `/values:batchUpdate` — write multiple ranges

For discovery + first read, prefer two separate calls (metadata + values) over trying to guess the sheet name.

## Mirna Session Example (01/07/2026)

Tried `Mirna's Team` → 400 error. Discovered it was `Haas Team` → then user renamed to `HaaS Teams`. The discovery pattern would have avoided 3 failed attempts.