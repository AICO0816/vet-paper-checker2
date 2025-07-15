import feedparser
import ssl
from datetime import datetime, date
import pytz

# --- 設定項目 ---

# 1. 論文サイトのリスト
JOURNALS = {
    "Veterinary Quarterly": "https://www.tandfonline.com/action/showFeed?jc=tveq20&type=rss",
    "Journal of Veterinary Internal Medicine": "https://onlinelibrary.wiley.com/feed/19391676/most-recent",
    "Veterinary and Comparative Oncology": "https://onlinelibrary.wiley.com/feed/17485827/most-recent",
    "Journal of Feline Medicine and Surgery": "http://feeds.feedburner.com/Jfm-TheJournalOfFelineMedicineAndSurgery",
    "American Journal of Veterinary Research": "https://avmajournals.avma.org/rss/journal/ajvr",
    "Journal of Veterinary Medical Science": "https://www.jstage.jst.go.jp/browse/jvms/_rss/-char/en",
    "Open Veterinary Journal": "https://www.openveterinaryjournal.com/feed/",
    "Frontiers in Veterinary Science": "https://www.frontiersin.org/journals/veterinary-science/rss",
    "MDPI Animals": "https://www.mdpi.com/rss/journal/animals"
}

# 2. 各サイトの表示件数の上限
ARTICLE_LIMIT = 10

# --- ここから下のプログラムは変更不要です ---

# SSL証明書の検証を無効にする (環境によるエラー回避)
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def format_authors(authors):
    """著者リストを整形する関数"""
    if not authors:
        return "著者情報なし"
    # 著者が多数の場合、3人まで表示して「et al.」を付ける
    author_names = [author.get('name', '') for author in authors]
    if len(author_names) > 3:
        return ', '.join(author_names[:3]) + ', et al.'
    return ', '.join(author_names)

def parse_date(entry):
    """日付をパースする関数"""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime.fromtimestamp(feedparser._parse_date_to_utc(entry.published_parsed))
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime.fromtimestamp(feedparser._parse_date_to_utc(entry.updated_parsed))
    return None

def generate_html():
    """RSSフィードから記事を取得し、HTMLファイルを生成する"""
    
    # 今日の日付をUTCで取得
    today_utc = datetime.now(pytz.utc).date()
    
    # HTMLのヘッダーとスタイルシート部分
    html_body = ""
    for name, url in JOURNALS.items():
        journal_html = f"<h2><i class='fas fa-paw'></i> {name}</h2>\n<div class='article-list'>\n"
        
        todays_articles = []
        try:
            feed = feedparser.parse(url)
            if feed.status == 200:
                for entry in feed.entries:
                    article_date = parse_date(entry)
                    if article_date and article_date.date() == today_utc:
                        todays_articles.append(entry)
            else:
                journal_html += "<div class='article-card error'>フィードを取得できませんでした。</div>"
                continue

        except Exception as e:
            journal_html += f"<div class='article-card error'>エラーが発生しました: {e}</div>"
            continue

        if not todays_articles:
            journal_html += "<div class='article-card no-update'>本日更新された論文はありませんでした。</div>"
        else:
            for entry in todays_articles[:ARTICLE_LIMIT]:
                title = entry.get('title', 'タイトルなし')
                link = entry.get('link', '#')
                
                # 日付と著者の情報を取得・整形
                published_date_obj = parse_date(entry)
                published_date_str = published_date_obj.strftime('%Y-%m-%d') if published_date_obj else "日付不明"
                authors_str = format_authors(entry.get('authors'))

                journal_html += f"""
                <div class="article-card">
                    <h3><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
                    <div class="metadata">
                        <span class="date"><i class="fas fa-calendar-alt"></i> {published_date_str}</span>
                        <span class="authors"><i class="fas fa-user-edit"></i> {authors_str}</span>
                    </div>
                </div>
                """
        
        journal_html += "</div>\n"
        html_body += journal_html

    # 最終更新日時
    jst = pytz.timezone('Asia/Tokyo')
    last_updated_str = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')
    
    # 全体のHTMLを組み立てる
    final_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>本日の新着獣医学論文 🐾</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        <style>
            :root {{
                --bg-color: #f0f8ff; /* AliceBlue */
                --card-bg-color: #ffffff;
                --header-color: #4682b4; /* SteelBlue */
                --text-color: #333333;
                --link-color: #1e90ff; /* DodgerBlue */
                --meta-color: #5f9ea0; /* CadetBlue */
                --border-color: #e0ffff; /* LightCyan */
                --shadow-color: rgba(0, 0, 0, 0.08);
            }}
            body {{
                font-family: 'Helvetica Neue', 'Arial', 'Hiragino Sans', 'Meiryo', sans-serif;
                line-height: 1.7;
                margin: 0;
                padding: 20px;
                background-color: var(--bg-color);
                color: var(--text-color);
            }}
            .container {{
                max-width: 900px;
                margin: auto;
                background: var(--card-bg-color);
                padding: 20px 30px;
                border-radius: 12px;
                box-shadow: 0 4px 12px var(--shadow-color);
            }}
            h1 {{
                color: var(--header-color);
                border-bottom: 3px solid var(--border-color);
                padding-bottom: 15px;
                text-align: center;
                font-size: 2em;
            }}
            h2 {{
                color: var(--header-color);
                margin-top: 40px;
                border-left: 6px solid var(--link-color);
                padding-left: 12px;
                font-size: 1.5em;
            }}
            .article-list {{
                display: grid;
                gap: 15px;
            }}
            .article-card {{
                background: #fafffe;
                border: 1px solid var(--border-color);
                padding: 20px;
                border-radius: 8px;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .article-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 15px var(--shadow-color);
            }}
            .article-card h3 {{
                margin-top: 0;
                margin-bottom: 12px;
                font-size: 1.1em;
            }}
            .article-card h3 a {{
                color: var(--link-color);
                text-decoration: none;
                font-weight: 600;
            }}
            .article-card h3 a:hover {{
                text-decoration: underline;
            }}
            .metadata {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px 20px;
                font-size: 0.9em;
                color: var(--meta-color);
            }}
            .metadata span i {{
                margin-right: 6px;
            }}
            .no-update, .error {{
                text-align: center;
                color: #888;
                padding: 20px;
            }}
            .update-time {{
                text-align: right;
                color: #777;
                font-size: 0.85em;
                margin-top: 30px;
            }}
            .fas {{
                color: var(--meta-color);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fas fa-book-medical"></i> 本日の新着獣医学論文</h1>
            {html_body}
            <p class="update-time">最終更新: {last_updated_str}</p>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("新しいデザインのindex.htmlを生成しました。")

if __name__ == "__main__":
    generate_html()
