import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
from datetime import datetime
import re
import os

ARTICLES = [
    {"title": "Magic: The Gathering", "url": "https://es.wikipedia.org/wiki/Magic:_The_Gathering"},
    {"title": "Richard Garfield", "url": "https://es.wikipedia.org/wiki/Richard_Garfield"},
    {"title": "Multiverso (Magic: The Gathering)", "url": "https://es.wikipedia.org/wiki/Multiverso_(Magic:_The_Gathering)"},
    {"title": "Wizards of the Coast", "url": "https://es.wikipedia.org/wiki/Wizards_of_the_Coast"},
    {"title": "Anexo:Expansiones de Magic: The Gathering", "url": "https://es.wikipedia.org/wiki/Anexo:Expansiones_de_Magic:_The_Gathering"},
    {"title": "Campeonato mundial de Magic: el encuentro", "url": "https://es.wikipedia.org/wiki/Campeonato_mundial_de_Magic:_el_encuentro"},
    {"title": "Magic: The Gathering Arena", "url": "https://es.wikipedia.org/wiki/Magic:_The_Gathering_Arena"},
    {"title": "Magic: The Gathering – Duels of the Planeswalkers", "url": "https://es.wikipedia.org/wiki/Magic:_The_Gathering_%E2%80%93_Duels_of_the_Planeswalkers"},
    {"title": "Booster draft", "url": "https://es.wikipedia.org/wiki/Booster_draft"},
    {"title": "Unhinged (Magic)", "url": "https://es.wikipedia.org/wiki/Unhinged_(Magic)"},
]

def clean_text(text):
    # Eliminar referencias tipo [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    # Eliminar espacios múltiples y saltos de línea excesivos
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def scrape_article(title, url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; tarea-universitaria/1.0)'}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Obtener solo el contenido principal
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            print(f"No se encontró contenido en {url}")
            return []

        # Eliminar elementos no textuales
        for tag in content_div.find_all(['table', 'figure', 'img', 'sup', 'style', 'script']):
            tag.decompose()

        # Extraer párrafos
        paragraphs = content_div.find_all('p')
        raw_text = '\n'.join(p.get_text() for p in paragraphs)
        cleaned = clean_text(raw_text)

        if not cleaned:
            print(f"Texto vacío para {url}")
            return []

        # Fragmentar en chunks de ~800 caracteres
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=50)
        chunks = splitter.split_text(cleaned)

        results = []
        for i, chunk in enumerate(chunks):
            results.append({
                "text": chunk,
                "metadata": {
                    "title": title,
                    "url": url,
                    "line_number": i + 1,
                    "char_count": len(chunk),
                    "processed_at": datetime.now().isoformat()
                }
            })

        print(f"OK: {title} — {len(chunks)} chunks")
        return results

    except Exception as e:
        print(f"Error en {url}: {e}")
        return []

def main():
    os.makedirs('../Processed', exist_ok=True)
    all_chunks = []

    for article in ARTICLES:
        chunks = scrape_article(article['title'], article['url'])
        if not chunks:
            continue

        # Guardar archivo individual
        filename = article['title'].replace(' ', '_').replace(':', '').replace('/', '_')
        filepath = f"../Processed/{filename}.jsonl"
        with open(filepath, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')

        all_chunks.extend(chunks)

    # Guardar compilado
    with open('../Processed/Compilado.jsonl', 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Archivos guardados en /Processed")

if __name__ == "__main__":
    main()