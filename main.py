import feedparser
import ssl
from datetime import datetime
import pytz
import requests
import calendar

# --- 設定項目 ---
JOURNALS = {
    "Veterinary Quarterly": "https://www.tandfonline.com/action/showFeed?jc=tveq20&type=rss",
    "Journal of Veterinary Internal Medicine": "https://onlinelibrary.wiley.com/feed/19391676/most-recent",
    "Jorunal of Small Animal Practice": "https://onlinelibrary.wiley.com/feed/17485827/most-recent",
    # ↓↓↓ ここのURLを修正しました ↓↓↓
    "Journal of Feline Medicine and Surgery": "https://journals.sagepub.com/action/showFeed?jc=jfm&type=rss",
    "American Journal of Veterinary Research": "https://avmajournals.avma.org/rss/journal/ajvr",
    "Journal of Veterinary Medical Science": "https://www.jstage.jst.go.jp/AF05S010NewRssDld?btnaction=JT0041&sryCd=jvms&rssLang=en",
    "Open Veterinary Journal": "https://www.openveterinaryjournal.com/feed/",
    "Frontiers in Veterinary Science": "https://www.frontiersin.org/journals/veterinary-science/rss",
    "MDPI Animals": "https://www.mdpi.com/rss/journal/animals"
}
ARTICLE_LIMIT = 10
REQUEST_TIMEOUT = 30

# --- ここから下のプログラムは変更不要です ---

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def format_authors(authors):
    if not authors: return "著者情報なし"
    author_names = [author.get('name', '') for author in authors]
    if len(author_names) > 3: return ', '.join(author_names[:3]) + ', et al.'
    return ', '.join(author_names)

def parse_date(entry):
    date_struct = entry.get('published_parsed') or entry.get('updated_parsed')
    if date_struct:
        timestamp = calendar.timegm(date_struct)
        return datetime.fromtimestamp(timestamp, tz=pytz.utc)
    return None

def generate_html():
    html_body = ""
    for name, url in JOURNALS.items():
        journal_html = f"<h2><i class='fas fa-paw'></i> {name}</h2>\n<div class='article-list'>\n"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

        except requests.exceptions.RequestException as e:
            journal_html += f"<div class='article-card error'>フィード取得中にタイムアウトまたはネットワークエラーが発生しました。</div>"
            html_body += journal_html + "</div>\n"
            continue
        except Exception as e:
            journal_html += f"<div class='article-card error'>予期せぬエラーが発生しました: {e}</div>"
            html_body += journal_html + "</div>\n"
            continue

        if not feed.entries:
            journal_html += "<div class='article-card no-update'>新しい論文はありませんでした。</div>"
        else:
            for entry in feed.entries[:ARTICLE_LIMIT]:
                title = entry.get('title', 'タイトルなし')
                link = entry.get('link', '#')
                
                published_date_obj = parse_date(entry)
                published_date_str = published_date_obj.astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M') if published_date_obj else "日付不明"
                authors_str = format_authors(entry.get('authors'))

                journal_html += f"""
                <div class="article-card">
                    <h3><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
                    <div class="metadata">
                        <span class="date"><i class="fas fa-calendar-alt"></i> {published_date_str} JST</span>
                        <span class="authors"><i class="fas fa-user-edit"></i> {authors_str}</span>
                    </div>
                </div>
                """
        
        journal_html += "</div>\n"
        html_body += journal_html

    jst = pytz.timezone('Asia/Tokyo')
    last_updated_str = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')
    
    final_html = f"""
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>最新の獣医学論文 🐾</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        :root {{ --bg-color: #f0f8ff; --card-bg-color: #ffffff; --header-color: #4682b4; --text-color: #333333; --link-color: #1e90ff; --meta-color: #5f9ea0; --border-color: #e0ffff; --shadow-color: rgba(0, 0, 0, 0.08); }}
        body {{ font-family: 'Helvetica Neue', 'Arial', 'Hiragino Sans', 'Meiryo', sans-serif; line-height: 1.7; margin: 0; padding: 20px; background-color: var(--bg-color); color: var(--text-color); }}
        .container {{ max-width: 900px; margin: auto; background: var(--card-bg-color); padding: 20px 30px; border-radius: 12px; box-shadow: 0 4px 12px var(--shadow-color); }}
        h1 {{ color: var(--header-color); border-bottom: 3px solid var(--border-color); padding-bottom: 15px; text-align: center; font-size: 2em; }}
        h2 {{ color: var(--header-color); margin-top: 40px; border-left: 6px solid var(--link-color); padding-left: 12px; font-size: 1.5em; }}
        .article-list {{ display: grid; gap: 15px; }}
        .article-card {{ background: #fafffe; border: 1px solid var(--border-color); padding: 20px; border-radius: 8px; transition: transform 0.2s, box-shadow 0.2s; }}
        .article-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 15px var(--shadow-color); }}
        .article-card h3 {{ margin-top: 0; margin-bottom: 12px; font-size: 1.1em; }}
        .article-card h3 a {{ color: var(--link-color); text-decoration: none; font-weight: 600; }}
        .article-card h3 a:hover {{ text-decoration: underline; }}
        .metadata {{ display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 0.9em; color: var(--meta-color); }}
        .metadata span i {{ margin-right: 6px; }}
        .no-update, .error {{ text-align: center; color: #888; padding: 20px; }}
        .update-time {{ text-align: right; color: #777; font-size: 0.85em; margin-top: 30px; }}
        .fas {{ color: var(--meta-color); }}
    </style></head><body><div class="container">
    <h1><i class="fas fa-book-medical"></i> 最新の獣医学論文</h1>{html_body}
    <p class="update-time">最終更新: {last_updated_str}</p>
    </div></body></html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("新しいデザインのindex.htmlを生成しました。")

if __name__ == "__main__":
    generate_html()

