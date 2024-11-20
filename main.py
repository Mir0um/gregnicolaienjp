import streamlit as st
import pandas as pd
import ftplib
import json
import csv
import sqlite3
from io import StringIO, BytesIO
from datetime import datetime
import socket
import pandas_profiling
from streamlit_pandas_profiling import st_profile_report
from ydata_profiling import ProfileReport
import openpyxl

# Configuration de la page
st.set_page_config(page_title="Data_convertisseur",
                    page_icon="http://89.86.5.13/img/logo.png",
                    layout="wide",
                    initial_sidebar_state="collapsed",
                    menu_items={
                            'Get Help': 'https://www.extremelycoolapp.com/help',
                            'Report a bug': "https://www.extremelycoolapp.com/bug",
                            'About': "# This is a header. This is an *extremely* cool app!"
                        }
                   )
# Titre principal
col1, col2 = st.columns([1,12])

with col1:
    st.image("http://89.86.5.13/img/logo.png", width=120)
with col2:
    st.header("Convertisseur de fichiers")

# Créer des onglets pour l'importation et l'exportation
tabs = st.tabs(["Importation", "Exportation", "Configuration", "Analyse de données"])

# Onglet Importation
tabs[0].header("Importation des Fichiers")
with tabs[0]:
    uploaded_file = st.file_uploader("Chargez un fichier (CSV, JSON, SQL, ou Excel)", type=["csv", "json", "sql", "xlsx", "xlsm", "xlsb", "odf"])

    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1]

        try:
            if file_type == "csv":
                # Détection automatique du séparateur
                decoders = encodings = [
                                        'ascii',        # Encodage ASCII standard
                                        'utf-8',        # Encodage Unicode standard
                                        'utf-16',       # Encodage Unicode sur 2 ou 4 octets
                                        'utf-32',       # Encodage Unicode sur 4 octets
                                        'latin-1',      # Encodage ISO-8859-1 pour les langues d'Europe occidentale
                                        'cp1252',       # Encodage Windows pour les langues d'Europe occidentale
                                        'iso-8859-15',  # Variante de l'ISO-8859-1 avec le symbole de l'euro
                                        'mac-roman',    # Encodage utilisé sur les anciens systèmes Mac
                                        'big5',         # Encodage pour le chinois traditionnel
                                        'gb2312',       # Encodage pour le chinois simplifié
                                        'shift_jis',    # Encodage pour le japonais
                                        'euc-jp',       # Encodage pour le japonais
                                        'euc-kr',       # Encodage pour le coréen
                                        'koi8-r',       # Encodage pour le russe
                                        'cp866',        # Encodage DOS pour le russe
                                        'cp850',        # Encodage DOS pour l'Europe occidentale
                                        'cp437',        # Encodage DOS original
                                        'utf-7',        # Encodage Unicode obsolète
                                        'utf-8-sig',    # UTF-8 avec marque d'ordre d'octet (BOM)
                                        'utf-16-be',    # UTF-16 big-endian
                                        'utf-16-le',    # UTF-16 little-endian
                                        'utf-32-be',    # UTF-32 big-endian
                                        'utf-32-le',    # UTF-32 little-endian
                                    ]

                for decoder in decoders:
                    try:
                        content = uploaded_file.read().decode(decoder, errors="ignore")
                        break
                    except UnicodeDecodeError:
                        continue
                try:
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(content[:1024])
                    sep = dialect.delimiter
                    st.success(f"Séparateur détecté automatiquement : '{sep}'")
                except Exception:
                    sep = st.text_input("Séparateur non détecté, entrez-le manuellement (par ex. ',' ou ';') :", value=",")
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=sep)
            elif file_type == "json":
                data = json.load(uploaded_file)
                df = pd.json_normalize(data)
            elif file_type in ["xlsx", "xlsm", "xlsb", "odf"]:
                df = pd.read_excel(uploaded_file)
            elif file_type == "sql":
                conn = sqlite3.connect(uploaded_file)
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
                table_name = st.selectbox("Sélectionnez une table :", tables['name'])
                df = pd.read_sql(f"SELECT * FROM {table_name};", conn)
                conn.close()
            else:
                st.error("Type de fichier non pris en charge.")
                df = None

            if df is not None:
                # Afficher un aperçu des données
                st.write("Aperçu des données :")
                st.dataframe(df)

        except Exception as e:
            st.error(f"Erreur lors du traitement : {e}")
    else:
        st.info("Veuillez charger un fichier pour commencer.")

# Onglet Configuration FTPS
tabs[2].header("Configuration")
with tabs[2]:
    st.write("== Config SFTPS.==")
    ftp_host = st.text_input("FTP Host")
    ftp_port = st.number_input("FTP Port", min_value=1, max_value=65535, value=21)
    ftp_user = st.text_input("FTP Username")
    ftp_password = st.text_input("FTP Password", type="password")
    ftp_directory = st.text_input("FTP Directory", value="/")
    st.write("== Config serveur SQL .==")
    SQL_host = st.text_input("SQL Host")
    SQL_port = st.number_input("SQL Port", min_value=1, max_value=65535, value=3306 )
    SQL_user = st.text_input("SQL Username")
    SQL_password = st.text_input("SQL Password", type="password")
    SQL_bdd = st.text_input("SQL Database name.", value="/")

# Onglet Exportation
tabs[1].header("Exportation des Fichiers")
with tabs[1]:
    if 'df' in locals() and df is not None:
        # Sélection du format de conversion
        export_format = st.selectbox("Choisissez un format de conversion :", ["CSV", "JSON", "SQL", "Excel"])

        if export_format:
            if export_format == "CSV":
                # Choix du séparateur pour l'exportation
                export_sep = st.text_input("Choisissez un séparateur pour l'exportation (par ex. ',' ou ';') :",
                                           value=",")
                buffer = StringIO()
                df.to_csv(buffer, index=False, sep=export_sep)
                file_data = buffer.getvalue().encode('utf-8')
                filename = "converted_file.csv"
            elif export_format == "JSON":
                buffer = StringIO()
                df.to_json(buffer, orient="records", indent=2)
                file_data = buffer.getvalue().encode('utf-8')
                filename = "converted_file.json"
            elif export_format == "Excel":
                buffer = BytesIO()
                df.to_excel(buffer, index=False, engine='openpyxl')
                file_data = buffer.getvalue()
                filename = "converted_file.xlsx"
            elif export_format == "SQL":
                conn = sqlite3.connect("converted_file.db")
                table_name = st.text_input("Nom de la table pour l'export :", "exported_table")
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                conn.close()
                with open("converted_file.db", "rb") as f:
                    file_data = f.read()
                filename = "converted_file.db"

            # Section de téléchargements basiques
            st.header("Téléchargement basique")
            mime_type = 'text/csv' if export_format == "CSV" else 'application/json' if export_format == "JSON" else 'application/x-sqlite3' if export_format == "SQL" else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            st.download_button(label=f"Télécharger le fichier {filename}", data=file_data, file_name=filename, mime=mime_type)

            # Section d'exportation en FTPS
            st.header("Exportation via FTPS")
            if ftp_host and ftp_user and ftp_password:
                if st.button("Exporter via FTPS"):
                    print("[LOG] Connexion au serveur FTP...")
                    try:
                        with ftplib.FTP_TLS() as ftp:
                            ftp.connect(host=ftp_host, port=ftp_port)
                            ftp.login(user=ftp_user, passwd=ftp_password)
                            ftp.prot_p()  # Activer le mode de protection
                            ftp.cwd(ftp_directory)
                            ftp.storbinary(f'STOR {filename}', BytesIO(file_data))
                            st.success(f"Fichier sauvegardé sur le serveur FTP : {ftp_directory}/{filename}")
                            print(f"[LOG] Fichier uploadé avec succès sur le serveur FTP : {ftp_directory}/{filename}")
                    except Exception as e:
                        st.error(f"Erreur lors de l'upload FTP : {e}")
                        print(f"[LOG] Erreur lors de l'upload FTP : {e}")
            else:
                st.warning("Veuillez configurer les identifiants FTP dans l'onglet 'Configuration FTPS' pour utiliser l'exportation FTPS.")
    else:
        st.info("Veuillez importer des données dans l'onglet 'Importation' pour commencer l'exportation.")

# Onglet Analyse de données avec Pandas Profiling
tabs[3].header("Analyse des Données")
with tabs[3]:
    if 'df' in locals() and df is not None:
        if st.button("Générer le rapport de profilage"):
            profile = ProfileReport(df)
            st_profile_report(profile, navbar=True)

            # Ajouter un bouton pour télécharger le rapport de profilage au format HTML
            html_report = profile.to_html()
            st.download_button(label="Télécharger le rapport de profilage en HTML", data=html_report, file_name="profiling_report.html", mime="text/html")
    else:
        st.info("Veuillez importer des données dans l'onglet 'Importation' pour générer un rapport de profilage.")
