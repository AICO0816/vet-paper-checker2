import feedparser
import ssl
from datetime import datetime
import pytz

# SSL証明書の検証を無効にする (環境によるエラー回避)
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# 巡回したい学術誌のRSSフィード
JOURNALS = {
    "Veterinary Quarterly": "https://www.tandfonline.com/action/showFeed?jc=tveq20&type=rss",
    "Journal of Veterinary Internal Medicine (JVIM)": "https://onlinelibrary.wiley.com/feed/19391676/most-recent",
    "Journals of Small Animal Practice": "https://onlinelibrary.wiley.com/feed/17485827/most-recent",
    "Journal of Feline Medicine and Surgery (JFMS)": "https://journals.sagepub.com/action/showFeed?type=etoc&feed=rss&jc=jfm",
    "American Journal of Veterinary Research (AJVR)": "https://avmajournals.avma.org/view/journals/ajvr/ajvr-overview.xml",
    "Journal of Veterinary Medical Science (JVMS)": "https://www.jstage.jst.go.jp/AF05S010NewRssDld?btnaction=JT0041&sryCd=jvms&rssLang=en"
}

ARTICLE_COUNT = 5 # 取得したい記事の数

def fetch_and_generate_html():
    """RSSフィードから記事を取得し、HTMLファイルを生成する"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>最新獣医学論文リスト</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; margin: 20px; background-color: #f9f9f9; color: #333; }
            .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 40px; border-left: 5px solid #3498db; padding-left: 10px; }
            ul { list-style-type: none; padding-left: 0; }
            li { background: #ecf0f1; margin-bottom: 10px; padding: 15px; border-radius: 5px; }
            a { color: #2980b9; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
            .update-time { text-align: right; color: #7f8c8d; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>最新獣医学論文リスト</h1>
    """

    for name, url in JOURNALS.items():
        html_content += f"<h2>{name}</h2>\n<ul>\n"
        try:
            feed = feedparser.parse(url)
            if feed.status == 200 and feed.entries:
                for entry in feed.entries[:ARTICLE_COUNT]:
                    title = entry.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    link = entry.link
                    html_content += f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></li>\n'
            else:
                html_content += "<li>記事を取得できませんでした。</li>\n"
        except Exception as e:
            html_content += f"<li>エラーが発生しました: {e}</li>\n"
        html_content += "</ul>\n"

    # 更新日時を追加
    jst = pytz.timezone('Asia/Tokyo')
    last_updated = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')
    html_content += f'<p class="update-time">最終更新: {last_updated}</p>'

    html_content += """
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("index.htmlを生成しました。")

if __name__ == "__main__":
    fetch_and_generate_html()
