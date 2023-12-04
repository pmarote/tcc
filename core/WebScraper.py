# pmscrap.py - classe para WebScraper do contencioso do TIT

import os
import requests


class WebScraper:
    def __init__(self, cweb_dir):
        self.cweb_dir = cweb_dir
        self.tit_url = ("https://www.fazenda.sp.gov.br/epat/extratoprocesso/"
                        + "ExtratoDetalhe.aspx?num_aiim=")
        self.url_from = ''
        self.file_to = ''
        self.html_content = ''

    def get_first_and_latest_file(self, filetype):
        files = os.listdir(self.cweb_dir)
        filtered_files = [file for file in files if file.endswith(filetype)]
        paths = [os.path.join(self.cweb_dir, file) for file in filtered_files]
        paths.sort()
        return paths[0], paths[-1]

    def get_first_aiim_nr(self):
        first_file = self.get_first_and_latest_file('.html')[0]
        first_aiim_nr = int(os.path.basename(first_file).replace('.html', ''))
        return first_aiim_nr

    def get_next_aiim_nr(self):
        latest_file = self.get_first_and_latest_file('.html')[1]
        last_aiim_nr = int(os.path.basename(latest_file).replace('.html', ''))
        return last_aiim_nr + 1

    def fetch_url(self, url_from):
        self.url_from = url_from
        try:
            response = requests.get(self.url_from)
            if response.status_code == 200:
                self.html_content = response.text
                print(f"Leitura de {self.url_from} com sucesso.")
                return True
            else:
                print(f"##Erro## {response.status_code} de leitura de {self.url_from}.")
                return None
        except Exception as e:
            print(f"##Erro##: {e}")
            return None

    def save_url_to(self, nro_aiim):
        self.file_to = os.path.join(self.cweb_dir, nro_aiim + ".html")
        try:
            self.save_html_file(self.html_content, self.file_to, nro_aiim)
            print(f"Html {self.file_to} salvo com sucesso.")
            return str(int(nro_aiim) + 1)
        except Exception as e:
            print(f"Erro ao salvar Html {self.file_to}: {e}")
            return None

    # Function to save content to an HTML file
    def save_html_file(self, content, file_name, nro_aiim):
        html_content = self.process_html(content, nro_aiim)
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(html_content)

    # Function para fazer algumas alterações no html content para visualizar mais fácil em arquivo
    def process_html(self, html, nro_aiim):
        # Tirar o Ansi que está descrito em HEAD
        html = html.replace('; charset=iso-8859-1', ';')
        # Ainda não sei o porquê, mas veio com um \r a mais...
        # html = html.replace('\r\n\r', '\r\n')
        # html = html.replace('\r\r\n', '\r\n')
        # Fixing links, removing absolute links to save
        html = html.replace('/epat/ExtratoProcesso/images/', 'images/')
        pos_ini = 0
        search_string = "https://www.fazenda.sp.gov.br/vdtit/consultarvotos.aspx?cdvoto="
        while html.find(search_string, pos_ini) != -1:
            pos_vote_ini = html.find(search_string, pos_ini) + 63
            pos_vote_end = html.find('"', pos_vote_ini) - 1
            vote = html[pos_vote_ini:pos_vote_end + 1]
            self.download_and_save_pdf(vote, nro_aiim)
            # Fixing PDF link
            html = html.replace("https://www.fazenda.sp.gov.br/vdtit/"
                                + f"consultarvotos.aspx?cdvoto={vote}",
                                f"{nro_aiim}voto{vote}.pdf")
            pos_ini = pos_vote_end + 5 - 70 + 18
        return html

    def download_and_save_pdf(self, vote, nro_aiim):
        pdf_url = f"https://www.fazenda.sp.gov.br/vdtit/consultarvotos.aspx?cdvoto={vote}"
        response = requests.get(pdf_url)

        if response.status_code == 200:
            pdf_file_name = os.path.join(self.cweb_dir, nro_aiim + 'voto' + vote + '.pdf')
            with open(pdf_file_name, "wb") as f:
                f.write(response.content)
        else:
            print(f"Error downloading and saving PDF {vote}...")

    def baixa_aiim(self, nro_aiim):
        res1 = self.fetch_url(self.tit_url + nro_aiim)
        # se a leitura da url acima foi com sucesso, o método pmscrap.fetch_url retorn True
        if (res1):
            # self.save_url_to retorna None em caso de erro ou o número do próximo AIIM se tudo ok
            return self.save_url_to(nro_aiim)
        else:
            return None
