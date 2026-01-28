import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QComboBox, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QTextEdit, QLabel, QDialog, QFormLayout,
                             QDateEdit, QLineEdit, QListWidget, QFileDialog)
from PyQt6.QtCore import QDate
from PyQt6.QtWebEngineWidgets import QWebEngineView

# --- FUNKCJA KONWERTUJĄCA LICZBY NA SŁOWA ---
def kwota_slownie(kwota_float):
    try:
        zlote = int(kwota_float)
        grosze = int(round((kwota_float - zlote) * 100))
    except:
        return str(kwota_float)

    def rzedy(n):
        jednosci = ["", "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć"]
        nastki = ["dziesięć", "jedenaście", "dwanaście", "trzynaście", "czternaście", "piętnaście", "szesnaście", "siedemnaście", "osiemnaście", "dziewiętnaście"]
        dziesiatki = ["", "dziesięć", "dwadzieścia", "trzydzieści", "czterdzieści", "pięćdziesiąt", "sześćdziesiąt", "siedemdziesiąt", "osiemdziesiąt", "dziewięćdziesiąt"]
        setki = ["", "sto", "dwieście", "trzysta", "czterysta", "pięćset", "sześćset", "siedemset", "osiemset", "dziewięćset"]
        s = (n % 1000) // 100
        d = (n % 100) // 10
        j = n % 10
        txt = []
        if s > 0: txt.append(setki[s])
        if d == 1: txt.append(nastki[j])
        else:
            if d > 0: txt.append(dziesiatki[d])
            if j > 0: txt.append(jednosci[j])
        return " ".join(txt)

    def odmien(n, forma1, forma2, forma3):
        if n == 1: return forma1
        if n % 10 in [2, 3, 4] and n % 100 not in [12, 13, 14]: return forma2
        return forma3

    res = []
    tys = zlote // 1000
    if tys > 0:
        if tys == 1: res.append("tysiąc")
        else:
            res.append(rzedy(tys))
            res.append(odmien(tys, "tysiąc", "tysiące", "tysięcy"))
    zl_reszta = zlote % 1000
    if zl_reszta > 0 or zlote == 0:
        if zlote == 0: res.append("zero")
        else: res.append(rzedy(zl_reszta))
    res.append(odmien(zlote, "złoty", "złote", "złotych"))
    if grosze > 0:
        res.append(rzedy(grosze))
        res.append(odmien(grosze, "grosz", "grosze", "groszy"))
    else: res.append("zero groszy")
    return " ".join(res).strip()

class SettingsEditor(QDialog):
    def __init__(self, settings_dict):
        super().__init__()
        self.setWindowTitle("Dane Sprzedawcy")
        self.setMinimumWidth(500)
        self.settings = settings_dict
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edit_sprzedawca = QTextEdit(self.settings.get("sprzedawca_staly", ""))
        self.edit_sprzedawca.setMaximumHeight(80)
        self.edit_podstawa = QTextEdit(self.settings.get("podstawa_prawna", ""))
        self.edit_podstawa.setMaximumHeight(80)
        self.edit_bank = QTextEdit(self.settings.get("bank_nr_konta", ""))
        self.edit_bank.setMaximumHeight(60)
        self.edit_miejsce = QLineEdit(self.settings.get("miejsce_wystawienia", ""))
        form.addRow("Sprzedawca:", self.edit_sprzedawca)
        form.addRow("Podstawa prawna:", self.edit_podstawa)
        form.addRow("Bank/Konto:", self.edit_bank)
        form.addRow("Miejsce:", self.edit_miejsce)
        layout.addLayout(form)
        btn = QPushButton("Zapisz"); btn.clicked.connect(self.accept); layout.addWidget(btn)

    def get_values(self):
        return {
            "sprzedawca_staly": self.edit_sprzedawca.toPlainText(),
            "podstawa_prawna": self.edit_podstawa.toPlainText(),
            "bank_nr_konta": self.edit_bank.toPlainText(),
            "miejsce_wystawienia": self.edit_miejsce.text()
        }

class TenantEditor(QDialog):
    def __init__(self, najemcy_dict):
        super().__init__()
        self.setWindowTitle("Baza Najemców")
        self.setMinimumWidth(600)
        self.najemcy = najemcy_dict
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.addItems(sorted(self.najemcy.keys()))
        self.list_widget.currentRowChanged.connect(self.load_details)
        layout.addWidget(self.list_widget)
        form_w = QWidget(); flay = QFormLayout(form_w)
        self.e_nazwa = QLineEdit(); self.e_adres = QLineEdit(); self.e_miasto = QLineEdit()
        self.e_cena = QLineEdit(); self.e_nr_r = QLineEdit()
        flay.addRow("Nazwa:", self.e_nazwa); flay.addRow("Adres:", self.e_adres)
        flay.addRow("Kod/Miasto:", self.e_miasto); flay.addRow("Cena (zł):", self.e_cena)
        flay.addRow("Numer R:", self.e_nr_r)
        btn_s = QPushButton("Zapisz / Aktualizuj"); btn_s.clicked.connect(self.save_tenant); flay.addRow(btn_s)
        btn_d = QPushButton("Usuń"); btn_d.clicked.connect(self.delete_tenant); flay.addRow(btn_d)
        btn_close = QPushButton("Zamknij"); btn_close.clicked.connect(self.accept); flay.addRow(btn_close)
        layout.addWidget(form_w)

    def load_details(self, row):
        if row < 0: return
        name = self.list_widget.item(row).text()
        d = self.najemcy[name]
        self.e_nazwa.setText(name); self.e_adres.setText(d['adres'])
        self.e_miasto.setText(d['miasto']); self.e_cena.setText(d['cena_zl'])
        self.e_nr_r.setText(d['numer_R'])

    def save_tenant(self):
        name = self.e_nazwa.text().strip()
        if not name: return
        self.najemcy[name] = {"adres": self.e_adres.text(), "miasto": self.e_miasto.text(), "cena_zl": self.e_cena.text(), "numer_R": self.e_nr_r.text()}
        self.list_widget.clear(); self.list_widget.addItems(sorted(self.najemcy.keys()))

    def delete_tenant(self):
        curr = self.list_widget.currentItem()
        if curr:
            del self.najemcy[curr.text()]; self.list_widget.clear(); self.list_widget.addItems(sorted(self.najemcy.keys()))

class InvoiceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generator Faktur")
        self.setGeometry(50, 50, 1100, 900)
        self.config_file = "ustawienia.json"
        self.load_data()
        self.init_ui()

    def load_data(self):
        def_s = {"sprzedawca_staly": "Testowy\nul. Testowa 1\n00-001 Warszawa", "podstawa_prawna": "SPRZEDAWCA ZWOLNIONY PODMIOTOWO Z PODATKU OD TOWARÓW I USŁUG [dostawa towarów lub świadczenie usług zwolnionych na podstawie art. 113 ust. 1 (albo ust. 9) ustawy z dnia 11 marca 2004r. O podatku od towarów i usług (Dz. U. z 2011r. Nr 177, poz. 1054, z późn. zm.)]", "bank_nr_konta": "TestowyBank\nNr: 00 0000 0000 0000 0000 0000 0000", "miejsce_wystawienia": "Warszawa"}
        self.najemcy = {"Przykład": {"adres": "ul. Testowa 1", "miasto": "00-001 Warszawa", "cena_zl": "1000", "numer_R": "1"}}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    self.ustawienia = d.get("settings", def_s); self.najemcy = d.get("najemcy", self.najemcy)
            except: self.ustawienia = def_s
        else: self.ustawienia = def_s

    def save_all_data(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump({"settings": self.ustawienia, "najemcy": self.najemcy}, f, ensure_ascii=False, indent=4)

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central); layout = QVBoxLayout(central)
        tbar = QHBoxLayout()
        self.combo = QComboBox(); self.combo.addItems(sorted(self.najemcy.keys())); self.combo.currentIndexChanged.connect(self.update_preview)
        self.date_edit = QDateEdit(QDate.currentDate()); self.date_edit.setCalendarPopup(True); self.date_edit.dateChanged.connect(self.update_preview)
        tbar.addWidget(QLabel("Najemca:")); tbar.addWidget(self.combo)
        tbar.addWidget(QLabel("Data:")); tbar.addWidget(self.date_edit)
        btn_b = QPushButton("➕ Najemcy"); btn_b.clicked.connect(self.open_tenants)
        btn_s = QPushButton("⚙️ Sprzedawca"); btn_s.clicked.connect(self.open_settings)
        btn_p = QPushButton("💾 PDF"); btn_p.clicked.connect(self.save_pdf); btn_p.setStyleSheet("background: #dcedc8; font-weight: bold;")
        tbar.addWidget(btn_b); tbar.addWidget(btn_s); tbar.addWidget(btn_p)
        layout.addLayout(tbar)
        self.browser = QWebEngineView(); layout.addWidget(self.browser)
        self.update_preview()

    def open_settings(self):
        dialog = SettingsEditor(self.ustawienia)
        if dialog.exec(): self.ustawienia = dialog.get_values(); self.save_all_data(); self.update_preview()

    def open_tenants(self):
        curr = self.combo.currentText()
        dialog = TenantEditor(self.najemcy.copy())
        if dialog.exec():
            self.najemcy = dialog.najemcy # AKTUALIZACJA BAZY
            self.save_all_data()
            self.combo.blockSignals(True)
            self.combo.clear()
            self.combo.addItems(sorted(self.najemcy.keys()))
            idx = self.combo.findText(curr); self.combo.setCurrentIndex(idx if idx >= 0 else 0)
            self.combo.blockSignals(False)
            self.update_preview()

    def save_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Zapisz PDF", f"Faktura_{self.combo.currentText()}.pdf", "PDF (*.pdf)")
        if path: self.browser.page().printToPdf(path)

    def get_html_part(self, name, d, typ, qdate):
        s_h = self.ustawienia['sprzedawca_staly'].replace('\n', '<br>')
        b_h = self.ustawienia['bank_nr_konta'].replace('\n', '<br>')
        rom = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
        dzien = qdate.toString("dd.MM.yyyy")
        zl = d['cena_zl']; sl = kwota_slownie(float(zl or 0))
        cid = "section_oryginal" if typ == "oryginał" else "section_kopia"
        edit = 'contenteditable="true"' if typ == "oryginał" else 'contenteditable="false"'
        return f"""
        <div class="invoice-part" id="{cid}">
            <div class="header">
                <div class="left" {edit}><span class="label">SPRZEDAWCA</span><br>{s_h}</div>
                <div class="right" {edit}>{self.ustawienia['miejsce_wystawienia']}, {dzien}<br><strong>Faktura Nr {qdate.toString('MM')}/R{d['numer_R']}/{qdate.toString('yy')} ({typ})</strong><br><br><span class="label">NABYWCA</span><br><strong>{name}</strong><br>{d['adres']}<br>{d['miasto']}</div>
            </div>
            <table class="items">
                <thead><tr><th rowspan="2">Lp.</th><th rowspan="2">Nazwa usługi</th><th rowspan="2">Ilość</th><th colspan="2">Cena</th><th colspan="2">Wartość</th></tr><tr><th>zł</th><th>gr</th><th>zł</th><th>gr</th></tr></thead>
                <tbody {edit}><tr><td>1</td><td class="nazwa">Czynsz za m-c {rom[qdate.month()-1]}.{qdate.year()}</td><td class="ilosc">1</td><td class="cena_zl">{zl}</td><td class="cena_gr">0</td><td class="wartosc_zl">{zl}</td><td class="wartosc_gr">0</td></tr><tr><td>2</td><td class="nazwa"></td><td class="ilosc"></td><td class="cena_zl"></td><td class="cena_gr"></td><td class="wartosc_zl"></td><td class="wartosc_gr"></td></tr></tbody>
            </table>
            <div class="summary" {edit}>Razem: <span class="razem_val">{zl} | 0</span><br><strong>Do zapłaty: <span class="do_zaplaty_val">{zl},0</span> zł</strong><br><small>słownie: <span class="slownie_val">{sl}</span></small></div>
            <div class="legal" {edit}>{self.ustawienia['podstawa_prawna']}</div>
            <div class="footer"><div class="pay-info" {edit}>Zapłata: przelew<br>Termin: {dzien}<br>{b_h}</div><div class="sig"><div class="sig-line"></div>podpis wystawcy</div></div>
        </div>
        """

    def update_preview(self):
        name = self.combo.currentText()
        if not name or name not in self.najemcy: return
        d = self.najemcy[name]; qd = self.date_edit.date()
        js = r"""
        <script>
        function kwotaSlownie(total) {
            let zl = Math.floor(total), gr = Math.round((total - zl) * 100);
            function rzedy(n) {
                let j=["","jeden","dwa","trzy","cztery","pięć","sześć","siedem","osiem","dziewięć"], nt=["dziesięć","jedenaście","dwanaście","trzynaście","czternaście","piętnasta","szesnaście","siedemnaście","osiemnaście","dziewiętnaście"], d=["","dziesięć","dwadzieścia","trzydzieści","czterdzieści","pięćdziesiąt","sześćdziesiąt","siedemdziesiąt","osiemdziesiąt","dziewięćdziesiąt"], s=["","sto","dwieście","trzysta","czterysta","pięćset","sześćset","siedemset","osiemset","dziewięćset"];
                let sz=Math.floor((n%1000)/100), dz=Math.floor((n%100)/10), jz=n%10, t=[];
                if(sz>0) t.push(s[sz]); if(dz==1) t.push(nt[jz]); else { if(dz>0) t.push(d[dz]); if(jz>0) t.push(j[jz]); }
                return t.join(" ");
            }
            function odm(n,f1,f2,f3) { if(n==1) return f1; if(n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20)) return f2; return f3; }
            let res = []; let tys = Math.floor(zl/1000);
            if(tys>0) { if(tys==1) res.push("tysiąc"); else { res.push(rzedy(tys)); res.push(odm(tys,"tysiąc","tysiące","tysięcy")); } }
            if(zl%1000>0 || zl==0) { if(zl==0) res.push("zero"); else res.push(rzedy(zl%1000)); }
            res.push(odm(zl,"złoty","złote","złotych"));
            if(gr>0) { res.push(rzedy(gr)); res.push(odm(gr,"grosz","grosze","groszy")); } else res.push("zero groszy");
            return res.join(" ").replace(/\s+/g, ' ').trim();
        }
        document.addEventListener('input', function(e) {
            let o=document.getElementById('section_oryginal'), k=document.getElementById('section_kopia');
            let sum=0; o.querySelectorAll('tbody tr').forEach(r => {
                let n=r.querySelector('.nazwa').innerText.trim();
                if(n=="") { ["ilosc","cena_zl","cena_gr","wartosc_zl","wartosc_gr"].forEach(c=>r.querySelector('.'+c).innerText=""); return; }
                let il=parseFloat(r.querySelector('.ilosc').innerText)||0, zl=parseInt(r.querySelector('.cena_zl').innerText)||0, gr=parseInt(r.querySelector('.cena_gr').innerText)||0;
                let v=il*(zl+(gr/100)), vz=Math.floor(Math.round(v*100)/100), vg=Math.round((v-vz)*100);
                r.querySelector('.wartosc_zl').innerText=vz; r.querySelector('.wartosc_gr').innerText=vg; sum+=v;
            });
            let sz=Math.floor(Math.round(sum*100)/100), sg=Math.round((sum-sz)*100);
            o.querySelector('.razem_val').innerText=sz+" | "+sg; o.querySelector('.do_zaplaty_val').innerText=sz+","+sg; o.querySelector('.slownie_val').innerText=kwotaSlownie(sum);
            k.querySelector('.left').innerHTML=o.querySelector('.left').innerHTML; k.querySelector('.right').innerHTML=o.querySelector('.right').innerHTML.replace('(oryginał)','(kopia)'); k.querySelector('tbody').innerHTML=o.querySelector('tbody').innerHTML; k.querySelector('.summary').innerHTML=o.querySelector('.summary').innerHTML; k.querySelector('.legal').innerHTML=o.querySelector('.legal').innerHTML; k.querySelector('.pay-info').innerHTML=o.querySelector('.pay-info').innerHTML;
        });
        </script>
        """
        css = "<style>@page{size:A4;margin:0;}body{font-family:serif;padding:10mm;background:#eee;}.paper{background:white;width:210mm;margin:auto;padding:15mm;}.invoice-part{border-bottom:1px dashed #000;padding-bottom:20px;margin-bottom:20px;}.header{display:flex;justify-content:space-between;font-size:12px;}.items{width:100%;border-collapse:collapse;margin:15px 0;font-size:11px;}.items th,.items td{border:1px solid #000;padding:4px;text-align:center;}.summary{text-align:right;font-size:12px;}.legal{font-size:9px;margin:10px 0;}.footer{display:flex;justify-content:space-between;margin-top:20px;}.sig{width:180px;text-align:center;border-top:1px solid #000;font-size:10px;}[contenteditable='true']:focus{background:#fffde7;}</style>"
        h = f"<html><head>{css}{js}</head><body><div class='paper'>" + self.get_html_part(name, d, "oryginał", qd) + self.get_html_part(name, d, "kopia", qd) + "</div></body></html>"
        self.browser.setHtml(h)

if __name__ == "__main__":
    a = QApplication(sys.argv); w = InvoiceApp(); w.show(); sys.exit(a.exec())