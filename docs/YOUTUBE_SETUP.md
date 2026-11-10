# 📺 YouTube-Integration & Google Device-Login

Dieses Setup verwendet das offizielle Kodi YouTube-Add-on (v7.4.4), das speziell für den Google TV Streamer angepasst wurde.

---

## 1. Google-Konto verbinden (Ohne Sicherheitswarnung)

Google hat vor kurzem den unüberprüften Zugriff auf persönliche Daten bei Drittanbieter-Apps gesperrt. Standardmäßige YouTube-Add-ons scheitern daher beim zweiten Login-Code mit der Fehlermeldung:  
> *„Hat versucht auf vertrauliche Daten zuzugreifen – zu deinem Schutz haben wir blockiert.“*

In diesem Setup wurde das Anmeldeverfahren (`yt_login.py`) so gepatcht, dass es sich als nativer Google TV Client (`tv`-Scope) identifiziert:
1. Navigiere in der linken Seitenleiste zu **YouTube & SmartTube** -> Untermenüpunkt **„🔑 YouTube Konto verbinden (Sign-In)“** (oder über Add-ons -> YouTube -> Anmelden).
2. Auf dem Fernseher erscheint ein **8-stelliger Geräte-Code** (z. B. `ABCD-EFGH`).
3. Öffne auf deinem Smartphone oder PC die Seite:  
   👉 **[google.com/device](https://google.com/device)**
4. Gib den angezeigten Code ein und bestätige die Berechtigung für deinen Google-Account.
5. Der Login ist sofort abgeschlossen – **kein zweiter Code, keine Sicherheitswarnung!**

---

## 2. Startseiten-Widgets

Sobald dein Konto verbunden ist, stehen dir folgende Reihen auf der Startseite zur Verfügung:
* **⭐ Meine YouTube Vorschläge:** Lädt deine persönlichen Empfehlungen (`FEwhat_to_watch`), genau wie in der YouTube-App auf deinem Handy.
* **🔥 YouTube Trends:** Aktuelle Trends aus Deutschland.
* **🔔 Meine Abonnements:** Neueste Videos aus deinen abonnierten Kanälen.
* **🕒 Wiedergabeverlauf:** Kürzlich gesehene Videos.

---

## 3. Native SmartTube App

In der linken Seitenleiste findest du den Haupteintrag **„YouTube & SmartTube“**.
* Ein Klick auf diesen Eintrag startet direkt die eigenständige Android-App **SmartTube**.
* SmartTube ist werbefrei, unterstützt SponsorBlock und spielt Videos bis zu 4K 60fps HDR flüssig ab.
