# Recorder 0.3.1-diag.1 – lokale Prüfung am 02.11.2026

Basis für Installation: unveränderte Bridge-App 0.3.0 aus
796d3a9fe7eccca8af5fc21c98b56e8f5cd4bf21. Der getestete Recorder wurde nicht auf
HA übertragen, installiert oder aktiviert. Integration 2.0.11-beta bleibt dort
unverändert. Deren Nutzung frischer Bridge-Daten und korrekte Anzeigen wurden
zuvor vom Eigentümer bestätigt; diese Hardwareprüfung gilt nur der regulären Basis.

## Änderungen

Der bereits auditierte Recorder von 7f06b29 passt zum selben 0.3.0-App-Code.
Separater Worktree/Branch bewahrt den pausierten 0.1.4-Rückport unverändert.
Neue lokale Version 0.3.1-diag.1, alte Optionsvorgaben erhalten, neue Diagnose-
Vorgaben false/8 MiB/4 Dateien. Kein Integrationscode im Update-Paket.
Neue .dockerignore schließt Python-Cache aus. Vergleichsfixture ist ausschließlich
öffentlicher Upstream-Code, SHA256 der LF-Datei:
50f7d628a155fca16345ae4036d039a8f481f7fa8e03d150ec7a0bc1284ccd27.

Zusätzlich notwendige Korrektur: SIGTERM beim echten Container-Stopp löst nun
den vorhandenen Cleanup aus. Vorher fehlte session_end im Export; der neue Test
scheiterte daran reproduzierbar. Keine Änderung der laufenden HTTP-Weiterleitung.

## Aktuelle Tests

Nach der SIGTERM-Korrektur: **254 passed, 1 skipped, 261 subtests passed**,
61.01 s, Windows/AMD64-Python-Umgebung. Ruff über das Repository und
git diff --check bestanden. POSIX-Rechtetest unter Windows übersprungen;
Verzeichnis-/Dateirechte und historische Archive zusätzlich im ARM64-Container
geprüft. Frühere 208/224/248-Teststände werden nicht als neue Ergebnisse gezählt.
Der vollständige Lauf prüft den lokalen Analysebaum; er ist kein Nachweis über
alle Dateien der tatsächlich installierten HA-Integration.

Neue Differentialtests vergleichen unveränderte 0.3.0, Recorder aus und an:
binäre Bodies, HTTP 200/207/503, identity/gzip/x-gzip/deflate/raw-deflate,
gestapelte/ungültige/nicht unterstützte Kompression, Requestweiterleitung und
Antwortheader. AST-Gleichheit für DNS-Resolver, DNS-Protokoll, Geräte-/Rezept-
verarbeitung, Statuslogging, Passthrough und Status-API. Alte Defaults bleiben
gleich; bestehende Optionen überlagern neue Vorgaben. Deaktivierter Recorder
verändert vorhandene Aufzeichnungen und andere persistente Dateien nicht.

Bestehende Regressionen decken Fehler bei Import, Eventvorbereitung, Status,
UUID/Annotation, Schreiben, vollem Datenträger und gesperrtem Writer ab;
Queue-/Größenbegrenzung vor Kodierung, Rotation/Altdateien, kurze Schreibvorgänge,
unvollständige HTTP-Bodies, Abbruch und begrenzter Recorder-Close bleiben geprüft.

## Build und Containerprüfung

Docker ausschließlich mit Kontext desktop-linux, Engine linux/amd64 29.7.2.
Buildziel linux/arm64; ausgeführt als aarch64 unter Emulation, Python 3.14.10,
aiohttp 3.13.5. Kein Raspberry-Pi-/Supervisor-Test des Recorders.

```
docker --context desktop-linux build --load --platform linux/arm64 --build-arg BUILD_FROM=ghcr.io/home-assistant/aarch64-base:3.24 --tag braumeister-diagnostics:0.3.1-diag.1-20261102 braumeister_bridge
python tests/container_smoke.py --image braumeister-diagnostics:0.3.1-diag.1-20261102 --platform linux/arm64
```

Basisdigest:
sha256:4925dc4a4e3c23a3a27e6936929ad33afb4d255027944a6054edff7e179f47b7

Finale Testimage-ID:
sha256:773b6010566dea3dfd9cd3c5851225133d8594a7b7a32e12a8d989c990f53639

Tatsächlich im Image geprüfte App-Dateien (genau diese Checkout-Bytes im ZIP):
- bridge.py: 4f3515a3cc1153b60a8f57eb5980cb2290db7bb58b134d64b4cd3d357c512f64
- bridge_diagnostics.py: 04cbfb194971e2fac0796ae6be4e926cc4e71f4ead53bec71607b3878962642b

BUILD_FROM wurde korrekt gesetzt; Warnung InvalidDefaultArgInFrom betrifft das
fehlende Dockerfile-Default, kein Buildfehler. Erster Build blieb beim damaligen
Buildx-Treiber im Cache; erneuter expliziter --load-Build machte das Testimage
lokal verfügbar. Keine globalen Docker-Einstellungen geändert, kein Push.
Basis-Tag und APK-Pakete sind beweglich; ein späterer Supervisor-Build kann einen
anderen Digest haben. Der auf HA dann verwendete Digest ist gesondert zu erfassen.

Finaler synthetischer Smoke-Test:
- Originalbasis, Recorder aus, an und fehlerhafter Speicherpfad auf verifiziert
  internem Netz; keine veröffentlichten Ports, Host-Binds oder Docker-Socket.
- 36 HTTP-Austausche, identische Status/Header/Bodies in allen vier Varianten.
- 9 korrelierte Aufzeichnungspaare, Base64/Länge/Latin-1 konsistent, gzip vor/nach
  Dekodierung erfasst, Geheimnisheader/Querywerte nicht in Events enthalten.
- Leere Bodies, Cloud-503, ungültiges gzip, Verbindungsabbruch und 2-MiB-Übergröße.
  Explizite Lücken statt stiller Trunkierung; Cloud/Fallback unterschieden.
- Synthetischer defekter Writer meldet 69 Fehler, ohne HTTP-Ergebnisse zu ändern.
- 40 Mock-Cloud-Requests: aiohttp wiederholt synthetisches idempotentes PUT beim
  Verbindungsabbruch einmal, 8 Drop-Requests bei vier Varianten. Kein zusätzlicher
  Recorder-Poll, kein Geräte-Replay; alle Zieladressen rein synthetisch.
- POSIX 0700/0600, Altdateirechte, 3-Dateien-Rotation mit je maximal 16384 Bytes,
  Eviction-/Gap-/Endmarker im separaten synthetischen Rotationsverzeichnis.
- Docker-Stopp des tatsächlichen App-Prozesses: Exitcode 0, kein OOM und
  session_end tatsächlich in der privaten persistenten Aufnahme vorhanden.
- Danach Netz-isolierter Exportcontainer mit ausschließlich eigenem Read-only-
  Testvolume. /data-TAR enthält **alle 6 Dateien hashgleich**, einschließlich
  aktiver/rotierter Captures, Optionen und unveränderter synthetischer Altdatei.
- Alle selbst erstellten Testcontainer, Netze und Volumes gezielt entfernt;
  Testimage bleibt lokales Prüfartefakt. Keine Prunes oder fremden Änderungen.

Zwischenläufe: zunächst fehlende session_end auf SIGTERM, korrigiert wie oben.
Ein Lauf scheiterte an kurzer Startbereitschaft; das Harness wartet jetzt maximal
45 s je App mit kurzen lokalen Health-Requests und liefert zusätzliche Fehlerlogs.
Der finale Lauf bestand; kein Fehler der Weiterleitung wurde dadurch kaschiert.

## Offene Grenzen und nächster Schritt

Kein Recorder-Hardwaretest, kein echter Supervisor-Export der neuen Capture-Dateien,
kein Browser-/Cloud-/Gerätezugriff in dieser Vorbereitung. Der synthetische
TAR-Roundtrip beweist nicht allein den späteren Supervisor-Backup-Ablauf.
Kein Stromausfall-/fsync-Versprechen; Rotationsanfang und Dateischluss können bei
Abbruch unvollständig sein. Bodies und Pfade bleiben private Rohdaten.

Vor Deployment: frische lokale Sicherung der jetzt bestätigten Bridge 0.3.0
einschließlich Optionen/Daten/Image, private Export-/Backup-Ziele abstimmen,
automatische Bridge-Updates kontrolliert ausschalten und explizite Freigabe des
konkreten Recorder-Pakets einholen. Erst deaktiviert installieren und prüfen;
Aktivierung/Restart/B00 nach eigener Abstimmung. Rückweg auf 0.3.0 vorbereiten;
Wiederherstellung bleibt bis zum tatsächlichen Test ungetestet.
