# Changer le port par défaut de Streamlit
if __name__ == "__main__":
    import os
    os.system("streamlit run .\main.py --server.port 8509  --server.headless true")