#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import fcntl
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import *
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    if os.path.exists("/usr/bin/Xwayland") or os.path.exists("/usr/bin/X"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["QT_X11_NO_MITSHM"] = "1"
_lock_file = None
class ModernCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percent = 0
        self.setFixedSize(200, 200)
    def setPercent(self, val):
        self.percent = max(0, min(100, val))
        self.update()
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy, radius, pen_width = 100, 100, 90, 16
       
        # Arka plan dairesi
        p.setPen(QPen(QColor(255, 255, 255, 60) if self.window().theme == "Dark" else QColor(0, 0, 0, 60), pen_width))
        p.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 0, 360 * 16)
       
        if self.percent > 0:
            grad = QConicalGradient(cx, cy, 90)
            pct = self.percent
            y1, y2 = (QColor(255, 255, 0), QColor(255, 255, 100)) if self.window().theme == "Dark" else (QColor(255, 200, 0), QColor(255, 220, 50))
           
            # Orijinal renk geçiş algoritmaların
            if pct <= 25:
                t = pct / 25
                color = QColor(int(y1.red()*(1-t)+y2.red()*t), int(y1.green()*(1-t)+y2.green()*t), int(y1.blue()*(1-t)+y2.blue()*t))
            elif pct <= 50:
                t = (pct - 25) / 25
                color = QColor(int(180*(1-t)+128*t), int(240*(1-t)+255*t), 0)
            elif pct <= 75:
                t = (pct - 50) / 25
                color = QColor(0, int(128*(1-t)+200*t), 0)
            else:
                t = (pct - 75) / 25
                color = QColor(int(255*(1-t)+200*t), int(0*(1-t)+50*t), 0)
               
            grad.setColorAt(0, color); grad.setColorAt(1, color)
            p.setPen(QPen(grad, pen_width, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 90 * 16, int(-pct * 3.6 * 16))
           
        p.setFont(QFont("Arial", 36, QFont.Bold))
        p.setPen(QColor("#ffffff") if self.window().theme == "Dark" else QColor("#000000"))
        p.drawText(self.rect(), Qt.AlignCenter, f"{int(self.percent)}%")
class NumericKeypad(QDialog):
    def __init__(self, parent=None, current_value=0, max_value=99, title="Giriş"):
        super().__init__(parent)
        self.setWindowTitle(title); self.setFixedSize(260, 360); self.setModal(True)
        self.max_value = max_value
        self.value = None
        self.temp_value = 0 if current_value > 0 else None
       
        layout = QVBoxLayout(self)
        self.display = QLabel("--" if self.temp_value is None else f"{self.temp_value:02d}")
        self.display.setFont(QFont("Arial", 36, QFont.Bold)); self.display.setAlignment(Qt.AlignCenter)
        self.display.setStyleSheet("background:#2c3e50; color:#ecf0f1; border-radius:15px; padding:15px; border: 2px solid #34495e;")
        layout.addWidget(self.display)
       
        grid = QGridLayout()
        buttons = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'Sil', '0', 'Onayla']
        for i, text in enumerate(buttons):
            btn = QPushButton(text); btn.setFixedSize(60, 60)
            if text == 'Onayla':
                btn.setStyleSheet("background:#27ae60; color:white; font-weight:bold;")
                btn.clicked.connect(self.try_accept)
            elif text == 'Sil':
                btn.setStyleSheet("background:#e74c3c; color:white;")
                btn.clicked.connect(self.delete)
            else:
                btn.setStyleSheet("background:#34495e; color:#ecf0f1;")
                btn.clicked.connect(lambda checked, t=text: self.append_number(t))
            grid.addWidget(btn, i // 3, i % 3)
        layout.addLayout(grid)
    def append_number(self, num):
        if self.temp_value is None: self.temp_value = 0
        new_val = self.temp_value * 10 + int(num)
        if new_val <= self.max_value:
            self.temp_value = new_val
            self.display.setText(f"{self.temp_value:02d}")
    def delete(self):
        if self.temp_value is not None and self.temp_value > 0:
            self.temp_value //= 10
            self.display.setText(f"{self.temp_value:02d}" if self.temp_value > 0 else "--")
            if self.temp_value == 0: self.temp_value = None
        else:
            self.temp_value = None; self.display.setText("--")
    def try_accept(self):
        if self.temp_value is None:
            QMessageBox.warning(self, "Hata", "( -- ) Olamaz .Rakam Giriniz !")
            return
        self.value = self.temp_value; self.accept()
    def get_value(self):
        return self.value if self.value is not None else -1
class TurnOff_v3(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("NikBulamadim", "TurnOff_v3")
        self.theme = self.settings.value("theme", "Dark", str)
        self.mode = self.settings.value("mode", "target_time", str)
       
        self.total = self.remain = 0
        self.is_paused = False
        self.action = "poweroff"
        self.hour = self.minute = 0
       
        self.setWindowTitle("TurnOff_v3"); self.setFixedSize(400, 650)
        icon_path = "/usr/share/pixmaps/turnoff_v3.png"
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "turnoff_v3.png")
        self.setWindowIcon(QIcon(icon_path))
       
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick)
        self.ui(); self.style()
    def ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20); v.setSpacing(10)
       
        top = QHBoxLayout()
        self.mode_label = QLabel("Sistem Saati" if self.mode == "target_time" else "Geri Sayım")
        self.mode_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.settings_btn = QPushButton("⚙"); self.settings_btn.setFixedSize(40, 40)
        top.addWidget(self.mode_label); top.addStretch(); top.addWidget(self.settings_btn)
        v.addLayout(top)
        self.menu = QMenu(self)
        m_menu = self.menu.addMenu("Giriş Modu")
        self.act_t = QAction("Sistem Saati", self, checkable=True)
        self.act_t.triggered.connect(lambda: self.set_mode("target_time"))
        self.act_d = QAction("Geri Sayım", self, checkable=True)
        self.act_d.triggered.connect(lambda: self.set_mode("duration"))
        m_menu.addActions([self.act_t, self.act_d])
       
        t_menu = self.menu.addMenu("Tema")
        self.act_l = QAction("Light Tema", self, checkable=True)
        self.act_l.triggered.connect(lambda: self.set_theme("Light"))
        self.act_dk = QAction("Dark Tema", self, checkable=True)
        self.act_dk.triggered.connect(lambda: self.set_theme("Dark"))
        t_menu.addActions([self.act_l, self.act_dk])
       
        self.act_t.setChecked(self.mode == "target_time"); self.act_d.setChecked(self.mode == "duration")
        self.act_l.setChecked(self.theme == "Light"); self.act_dk.setChecked(self.theme == "Dark")
        self.settings_btn.setMenu(self.menu)
        time_box = QHBoxLayout()
        self.hour_btn = QPushButton("--"); self.minute_btn = QPushButton("--")
        for b in (self.hour_btn, self.minute_btn):
            b.setFixedSize(70, 70); b.setFont(QFont("Arial", 40, QFont.Bold))
        self.hour_btn.clicked.connect(self.open_hour_keypad)
        self.minute_btn.clicked.connect(self.open_minute_keypad)
        self.colon = QLabel(":"); self.colon.setFont(QFont("Arial", 40, QFont.Bold))
        time_box.addStretch(); time_box.addWidget(self.hour_btn); time_box.addWidget(self.colon); time_box.addWidget(self.minute_btn); time_box.addStretch()
        v.addLayout(time_box)
        self.circle = ModernCircle(self); v.addWidget(self.circle, alignment=Qt.AlignCenter)
        self.time_lbl = QLabel("00:00:00"); self.time_lbl.setFont(QFont("Arial", 36, QFont.Bold)); self.time_lbl.setAlignment(Qt.AlignCenter)
        v.addWidget(self.time_lbl)
        grid = QGridLayout(); grid.setSpacing(12)
        self.btn_start = QPushButton("Kapat"); self.btn_stop = QPushButton("Beklet")
        self.btn_cancel = QPushButton("İptal"); self.btn_restart = QPushButton("Yeniden Başlat")
        for b in (self.btn_start, self.btn_stop, self.btn_cancel, self.btn_restart):
            b.setFixedSize(140, 70); b.setFont(QFont("Arial", 13, QFont.Bold))
       
        self.btn_start.clicked.connect(lambda: self.start("poweroff")); self.btn_stop.clicked.connect(self.toggle_pause)
        self.btn_cancel.clicked.connect(self.cancel); self.btn_restart.clicked.connect(lambda: self.start("reboot"))
       
        grid.addWidget(self.btn_start, 0, 0); grid.addWidget(self.btn_stop, 0, 1)
        grid.addWidget(self.btn_cancel, 1, 0); grid.addWidget(self.btn_restart, 1, 1)
        v.addLayout(grid)
       
        self.status = QLabel("Hazır"); self.status.setAlignment(Qt.AlignCenter); v.addWidget(self.status)
        self.apply_style()
    def set_mode(self, mode):
        self.mode = mode; self.act_t.setChecked(mode == "target_time"); self.act_d.setChecked(mode == "duration")
        self.mode_label.setText("Sistem Saati" if mode == "target_time" else "Geri Sayım")
        self.hour = self.minute = 0; self.hour_btn.setText("--"); self.minute_btn.setText("--")
        self.settings.setValue("mode", mode); self.update_pause_btn_state()
    def set_theme(self, theme):
        self.theme = theme; self.act_l.setChecked(theme == "Light"); self.act_dk.setChecked(theme == "Dark")
        self.style(); self.circle.update(); self.apply_style()
        if self.total == 0: self.time_lbl.setStyleSheet(f"color: {'#ffffff' if theme == 'Dark' else '#000000'};")
        self.settings.setValue("theme", theme)
    def style(self):
        dark = self.theme == "Dark"
        self.setStyleSheet(f"background: {'#0d1117' if dark else '#f9f9f9'}; color: {'#f0f0f0' if dark else '#222'};")
       
        s_btn_qss = "QPushButton { background: transparent; border: 2px solid #888; border-radius: 20px; } QPushButton:hover { border-color: #3498db; background: rgba(52, 152, 219, 40); }"
        self.settings_btn.setStyleSheet(s_btn_qss)
       
        self.btn_start.setStyleSheet("QPushButton { background:#27ae60; color:white; border-radius:16px; font-weight:bold; } QPushButton:hover { background:#2ecc71; }")
        self.btn_cancel.setStyleSheet("QPushButton { background:#e74c3c; color:white; border-radius:16px; font-weight:bold; } QPushButton:hover { background:#ff5e4d; }")
        self.btn_restart.setStyleSheet("QPushButton { background:#3498db; color:white; border-radius:16px; font-weight:bold; } QPushButton:hover { background:#4aa3df; }")
        self.update_pause_btn_state()
    def apply_style(self):
        dark = self.theme == "Dark"
        bg, txt = ("#2c3e50", "#ecf0f1") if dark else ("#ecf0f1", "#2c3e50")
        btn_s = f"QPushButton {{ background-color: {bg}; color: {txt}; border: 3px solid #34495e; border-radius: 20px; font-size: 40px; font-weight: bold; }} QPushButton:hover {{ background-color: #3498db; color: white; }}"
        self.hour_btn.setStyleSheet(btn_s); self.minute_btn.setStyleSheet(btn_s); self.colon.setStyleSheet(f"color: {txt};")
    def update_pause_btn_state(self):
        if self.mode == "target_time":
            self.btn_stop.setEnabled(False); self.btn_stop.setText("Beklet")
            self.btn_stop.setStyleSheet("background:#95a5a6; color:#bdc3c7; border-radius:16px;")
        else:
            self.btn_stop.setEnabled(True)
            c = "#e67e22" if self.is_paused else "#f39c12"
            self.btn_stop.setText("Devam Et" if self.is_paused else "Beklet")
            self.btn_stop.setStyleSheet(f"QPushButton {{ background:{c}; color:white; border-radius:16px; font-weight:bold; }} QPushButton:hover {{ background:#ff9f43; }}")
    def open_hour_keypad(self):
        k = NumericKeypad(self, self.hour, 23 if self.mode == "target_time" else 99, "Saat Gir")
        if k.exec_():
            val = k.get_value()
            if val != -1: self.hour = val; self.hour_btn.setText(f"{self.hour:02d}")
    def open_minute_keypad(self):
        k = NumericKeypad(self, self.minute, 59, "Dakika Gir")
        if k.exec_():
            val = k.get_value()
            if val != -1: self.minute = val; self.minute_btn.setText(f"{self.minute:02d}")
    def start(self, action="poweroff"):
        if self.total > 0: return
        h_t, m_t = self.hour_btn.text(), self.minute_btn.text()
        if h_t == "--" and m_t == "--":
            QMessageBox.warning(self, "Hata", "( -- : -- ) Geçersiz Giriş ! Rakam Yazınız !"); return
       
        now = datetime.now()
        if self.mode == "duration":
            t = self.hour * 3600 + self.minute * 60
            if t == 0: QMessageBox.warning(self, "Hata", "Süre 0 (Sıfır) Olamaz !"); return
            st_txt = f"{self.hour:02d}:{self.minute:02d} süreyle geri sayım başladı"
        else:
            if h_t == "--" or m_t == "--":
                QMessageBox.warning(self, "Hata", "Eksik Giriş yaptınız (--) Alan Var.\nSistem Saati modunda saat ve dakika zorunludur."); return
            tgt = datetime(now.year, now.month, now.day, self.hour, self.minute)
            if tgt <= now: tgt += timedelta(days=1)
            t = int((tgt - now).total_seconds())
            st_txt = f"{tgt.strftime('%d.%m.%Y %H:%M')}'da kapanacak"
        self.total = self.remain = t; self.action = action; self.is_paused = False
        self.hour_btn.setEnabled(False); self.minute_btn.setEnabled(False); self.timer.start(1000)
        self.status.setText(st_txt + (" (yeniden başlatma)" if action == "reboot" else " (Kapatma)"))
        self.update_ui(); self.update_pause_btn_state()
    def toggle_pause(self):
        if self.mode == "target_time" or self.total <= 0: return
        self.is_paused = not self.is_paused
        if self.is_paused: self.timer.stop(); self.status.setText("Durduruldu")
        else: self.timer.start(1000); self.status.setText("Geri sayım devam ediyor...")
        self.update_pause_btn_state()
    def cancel(self):
        self.timer.stop(); self.total = self.remain = 0; self.is_paused = False
        self.hour_btn.setEnabled(True); self.minute_btn.setEnabled(True)
        self.hour_btn.setText("--"); self.minute_btn.setText("--"); self.circle.setPercent(0)
        self.time_lbl.setText("00:00:00"); self.status.setText("İptal edildi")
        self.time_lbl.setStyleSheet(f"color: {'#ffffff' if self.theme == 'Dark' else '#000000'};")
        self.update_pause_btn_state()
        self.hour = self.minute = 0
    def tick(self):
        if self.remain > 0: self.remain -= 1; self.update_ui()
        else: self.timer.stop(); os.system(f"systemctl {self.action}")
    def update_ui(self):
        if self.total == 0: return
        h, m, s = self.remain // 3600, (self.remain % 3600) // 60, self.remain % 60
        self.time_lbl.setText(f"{h:02d}:{m:02d}:{s:02d}")
        pct = (self.total - self.remain) / self.total * 100
        self.circle.setPercent(pct)
        # Renk geçiş efekti
        y1, y2 = (QColor(255, 255, 0), QColor(255, 255, 100)) if self.theme == "Dark" else (QColor(255, 200, 0), QColor(255, 220, 50))
        if pct <= 25:
            t = pct / 25
            c = QColor(int(y1.red()*(1-t)+y2.red()*t), int(y1.green()*(1-t)+y2.green()*t), int(y1.blue()*(1-t)+y2.blue()*t))
        elif pct <= 50:
            t = (pct - 25) / 25
            c = QColor(int(180*(1-t)+128*t), int(240*(1-t)+255*t), 0)
        elif pct <= 75:
            t = (pct - 50) / 25
            c = QColor(0, int(128*(1-t)+200*t), 0)
        else:
            t = (pct - 75) / 25
            c = QColor(int(255*(1-t)+200*t), int(0*(1-t)+50*t), 0)
        self.time_lbl.setStyleSheet(f"color: rgb({c.red()},{c.green()},{c.blue()});")
    def closeEvent(self, event):
        if self.total > 0:
            QMessageBox.warning(self, "Dikkat!", "Geri sayım devam ediyor! Önce İptal edin.")
            event.ignore()
        else: event.accept()
def single_instance_lock():
    global _lock_file
    lock_path = os.path.join(os.getenv('XDG_RUNTIME_DIR', '/tmp'), 'turnoff_v3.lock')
    try:
        _lock_file = open(lock_path, 'w')
        fcntl.lockf(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except: return False
if __name__ == "__main__":
    if not single_instance_lock(): sys.exit(0)
    app = QApplication(sys.argv)
    app.setApplicationName("TurnOff_v3")
    win = TurnOff_v3(); win.show()
    sys.exit(app.exec_())
