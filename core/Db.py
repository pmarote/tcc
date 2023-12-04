# pmdb.py - classe para Gerenciamento dos Banco de Dados

import os
import sqlite3
from bs4 import BeautifulSoup


class Db:
    def __init__(self, var_dir):
        self.var_dir = var_dir
        self.db_name = 'tcc.db'
        if not os.path.exists(os.path.join(self.var_dir, self.db_name)):
            print(f"Banco de dados {os.path.join(self.var_dir, self.db_name)}"
                  + " inexistente... Criando...")
            self.db_connect()
            self.exec('''
CREATE TABLE aiim
    (numero INT PRIMARY KEY, nro_comp TEXT, drt TEXT, autuado TEXT,
     advogado TEXT, assunto TEXT, fase_proc TEXT);
''')
            self.exec('''
CREATE TABLE aiim_mov
    (numero INT, item INT, data TEXT, descri TEXT, PRIMARY KEY (numero, item));
''')
            self.exec('''
CREATE TABLE aiim_decis
    (numero INT, item INT, data TEXT, recurso TEXT, pdf_link TEXT,
        PRIMARY KEY (numero, item));
''')
        else:
            print("abrindo banco de dados "
                  + f"{os.path.join(self.var_dir, self.db_name)}")
            self.db_connect()

    def db_connect(self):
        self.conn = sqlite3.connect(os.path.join(self.var_dir, self.db_name))
        self.cursor = self.conn.cursor()

    def exec(self, sql):
        self.cursor.execute(sql)
        return self.conn.commit()

    def sql_to_list(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def html_to_db(self, html_file):
        with open(html_file, 'r', encoding='utf-8') as file:
            html = file.read()
        soup = BeautifulSoup(html, 'html.parser')
        if not ('COORDENADORIA DA ADMINISTRAÇÃO TRIBUTÁRIA' in html
                and 'TRIBUNAL DE IMPOSTOS E TAXAS' in html):
            print(f"Não processei {html_file} porque não me pareceu"
                  + " ser um arquivo .html de AIIM válido")
            return None
        dad_aiim = []
        dad_aiim_item = {'data': [], 'descri': []}
        dad_aiim_arqs = {'data': [], 'recurso': [], 'pdf_link': []}
        dad_aiim.append(int(os.path.basename(html_file[:-5])))
        if 'Dados do AIIM não encontrados' in html:
            dad_aiim.append("Dados AIIM não encontrados")
            return dad_aiim, dad_aiim_item
        if 'aiim informado não consta na base do sistema TIT' in html:
            dad_aiim.append("Erro... AIIM não consta na base do Tit")
            return dad_aiim, dad_aiim_item
        dad_aiim.append(self.html_to_db_aux(soup, "ConteudoPagina_lblAIIM"))
        dad_aiim.append(self.html_to_db_aux(soup, "ConteudoPagina_lblDRT"))
        dad_aiim.append(self.html_to_db_aux(soup,
                                            "ConteudoPagina_lblNomeAutuado"))
        dad_aiim.append(self.html_to_db_aux(soup,
                                            "ConteudoPagina_lblNomeAdvogado"))

        element = soup.find('div', {'id': 'ConteudoPagina_pnlAssunto'})
        if element:
            for br in element.find_all('br'):
                br.replace_with('##BR##')
            text = element.get_text(strip=True)
            text = text.replace('  ', '').replace('\n', '')\
                .replace('##BR##', '<br>').strip()
        else:
            text = ''
        dad_aiim.append(text)  # assunto, quando existir

        text = ''
        tables = soup.find_all('table')
        for table in tables:
            # Testa se o primeiro <td> no primeiro <tr>
            # contém 'Fase(s) Processual(is):'
            first_row = table.find('tr')
            if first_row and first_row.find('td').get_text(strip=True) == 'Fase(s) Processual(is):':
                # Wenn ja, finden Sie das zweite <td> in der zweiten <tr>
                second_row = first_row.find_next_sibling('tr')
                if second_row:
                    second_td = second_row.find_all('td')[1]
                    # Tudo isso para buscar a fase processual
                    text = second_td.get_text(strip=True)
                    break
        dad_aiim.append(text)  # fase processual, quando existir
        self.cursor.execute("INSERT OR REPLACE INTO aiim VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (dad_aiim[0], dad_aiim[1], dad_aiim[2], dad_aiim[3], dad_aiim[4], dad_aiim[5], dad_aiim[6]))

        events_div = soup.find(id='ConteudoPagina_pnlEventos')
        rows = events_div.find_all('tr')
        for item, row in enumerate(rows):
            cols = row.find_all('td')
            dad_aiim_item['data'].append(self.dtaBarra2AAAA_MM_DD(cols[0].text.strip()))
            dad_aiim_item['descri'].append(cols[1].text.strip())
            self.cursor.execute("INSERT OR REPLACE INTO aiim_mov VALUES (?, ?, ?, ?)",
                                (dad_aiim[0], item, dad_aiim_item['data'][item], dad_aiim_item['descri'][item]))

        arquivos_div = soup.find(id='ConteudoPagina_pnlArquivos')
        if arquivos_div is not None:
            rows = arquivos_div.find_all('tr')
            for item, row in enumerate(rows):
                cols = row.find_all('td')
                dad_aiim_arqs['data'].append(self.dtaBarra2AAAA_MM_DD(cols[0].text.strip()))
                dad_aiim_arqs['recurso'].append(cols[1].text.strip())
                dad_aiim_arqs['pdf_link'].append(cols[2].find('a')['href'])
                self.cursor.execute("INSERT OR REPLACE INTO aiim_decis VALUES (?, ?, ?, ?, ?)",
                                    (dad_aiim[0], item, dad_aiim_arqs['data'][item],
                                     dad_aiim_arqs['recurso'][item],
                                     dad_aiim_arqs['pdf_link'][item]))
        return dad_aiim, dad_aiim_item, dad_aiim_arqs

    def html_to_db_aux(self, soup, id):
        element = soup.find(id=id)
        return element.text.strip() if element else ''

    def dtaBarra2AAAA_MM_DD(self, date_str):
        day, month, year = date_str.split('/')
        return f'{year}-{month}-{day}'

    def close(self):
        self.conn.close()
