from flask import Flask, request, send_file, render_template, after_this_request
from cryptography.fernet import Fernet
import os
import threading
import time

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Funkcja do czyszczenia starych plików
def clean_old_files():
    while True:
        for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    file_age = time.time() - os.path.getmtime(file_path)
                    if file_age > 300:  # 300 sekund = 5 minut
                        os.remove(file_path)
        time.sleep(60)  # Sprawdza co minutę

# Uruchomienie czyszczenia w osobnym wątku
threading.Thread(target=clean_old_files, daemon=True).start()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            # Pobieranie klucza i trybu działania
            key = request.form["key"].encode()
            mode = request.form["mode"]
            file = request.files["file"]

            # Zapis pliku wejściowego
            input_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(input_path)

            # Przetwarzanie pliku
            fernet = Fernet(key)
            with open(input_path, "rb") as f:
                data = f.read()
            
            output_data = fernet.encrypt(data) if mode == "encrypt" else fernet.decrypt(data)
            output_filename = f"processed_{file.filename}.enc" if mode == "encrypt" else f"processed_{file.filename}"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            with open(output_path, "wb") as f:
                f.write(output_data)

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(output_path)
                except Exception as e:
                    app.logger.error(f"Error removing file: {e}")
                return response

            return send_file(output_path, as_attachment=True)

        except Exception as e:
            return f"Error: {e}"

    return render_template("index.html")

if __name__ == "__main__":
    app.run(port=80)