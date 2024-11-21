from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import pysolr

app = FastAPI()

# Solr connection URL
solr_url = 'http://localhost:8983/solr/search_core'
solr = pysolr.Solr(solr_url)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Solr Search</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f7fa;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: #fff;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    border-radius: 8px;
                }
                h1 {
                    text-align: center;
                    color: #333;
                }
                form {
                    display: flex;
                    flex-direction: column;
                }
                input[type="text"] {
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                    font-size: 16px;
                }
                input[type="submit"] {
                    padding: 10px;
                    background-color: #007bff;
                    color: #fff;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                }
                input[type="submit"]:hover {
                    background-color: #0056b3;
                }
                .results {
                    margin-top: 20px;
                }
                .result-item {
                    padding: 15px;
                    margin-bottom: 10px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .highlight {
                    background-color: yellow;
                    font-weight: bold;
                }
                a {
                    display: inline-block;
                    text-align: center;
                    padding: 10px;
                    margin-top: 20px;
                    background-color: #28a745;
                    color: #fff;
                    text-decoration: none;
                    border-radius: 5px;
                }
                a:hover {
                    background-color: #218838;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Search Engine</h1>
                <form action="/search" method="get">
                    <input type="text" name="query" placeholder="Search..." required/>
                    <input type="submit" value="Search"/>
                </form>
            </div>
        </body>
    </html>
    """

@app.get("/search", response_class=HTMLResponse)
async def search(
    query: str = Query(..., min_length=3, max_length=50),
    page: int = Query(1, ge=1)
):
    results_per_page = 10
    start = (page - 1) * results_per_page

    query_params = {
        "q": f"title:{query} content:{query}",
        "hl": "true",  # Enable highlighting
        "hl.fl": "title,content",  # Highlight fields
        "start": start,
        "rows": results_per_page,
        "fl": "id,title,content,score",  # Include 'id'
    }

    # Perform search
    results = solr.search(**query_params)
    highlighting = results.highlighting

    results_html = f"""
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Search Results</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f8f9fa;
                    color: #333;
                }}
                .container {{
                    max-width: 800px;
                    margin: 2rem auto;
                    padding: 1rem;
                    background: #fff;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                h2 {{
                    text-align: center;
                    color: #007bff;
                }}
                .results {{
                    margin-top: 1.5rem;
                }}
                .result-item {{
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border-bottom: 1px solid #ddd;
                }}
                .result-item:last-child {{
                    border-bottom: none;
                }}
                .result-item strong {{
                    color: #007bff;
                    font-size: 1.2rem;
                }}
                a {{
                    color: #007bff;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .pagination {{
                    text-align: center;
                    margin-top: 1rem;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Search Results for: <strong>{query}</strong></h2>
                <div class="results">
    """

    # Process results
    if results.docs:
        for doc in results.docs:
            doc_id = doc.get("id", None)
            if not doc_id:
                continue  # Skip documents without 'id'

            # Extract fields, handling arrays
            title_list = doc.get("title", ["No Title"])
            content_list = doc.get("content", ["No Content"])
            score = doc.get("score", "No Score")

            # Default display
            title = " ".join(title_list)
            content = " ".join(content_list)

            # Apply highlighting if available
            doc_highlight = highlighting.get(doc_id, {})
            if "title" in doc_highlight:
                title = " ".join(doc_highlight["title"])
            if "content" in doc_highlight:
                content = " ".join(doc_highlight["content"])

            results_html += f"""
            <div class="result-item">
                <strong>{title}</strong>: {content}
                <br><small>Relevance Score: {score}</small>
            </div>
            """
    else:
        results_html += "<p>No results found.</p>"

    # Pagination
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if len(results.docs) == results_per_page else None

    results_html += "</div>"
    results_html += '<div class="pagination">'
    if prev_page:
        results_html += f'<a href="/search?query={query}&page={prev_page}">Previous Page</a> '
    if next_page:
        results_html += f'<a href="/search?query={query}&page={next_page}">Next Page</a>'
    results_html += "</div>"

    results_html += """
            </div>
        </body>
    </html>
    """
    return results_html








# curl "http://localhost:8983/solr/search_core/update?commit=true" -d @data/data.json -H "Content-Type: application/json"
# curl "http://localhost:8983/solr/search_core/select?q=Python"
# curl "http://localhost:8983/solr/search_core/update?commit=true" -d '<delete><query>*:*</query></delete>'