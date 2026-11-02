# Recorder auf bestätigter Bridge 0.3.0 – lokale Vorbereitung

Stand 02.11.2026. Nur lokale Anpassung und Prüfung beauftragt. Keine Installation,
Aktivierung, Optionenänderung oder Neustarts auf HA in dieser Phase.

## Bestätigte Basis

Die bestehende App `local_braumeister_bridge` wurde mit dem geprüften unveränderten
Upstream-Paket 0.3.0 aus `796d3a9fe7eccca8af5fc21c98b56e8f5cd4bf21` aktualisiert.
Die funktionierenden Optionen sind laut manueller Prüfung erhalten, insbesondere
dns_port=0 und explizite Cloud-DNS-Resolver. Start und API-Health sind bestätigt.
Neue Gerätezeitstempel steigen, die Antwortquelle war `cloud`. Diese Nachweise
betreffen die reguläre Basis auf dem echten Gerät, keine Recorder-Hardwareprüfung.

Bei der HA-Anzeigeprüfung wurde statt der angenommenen Integration 2.0.11-beta
tatsächlich alter Code 2.0.3 festgestellt: manifest, sensor, coordinator und
web_auth wurden geprüft; bridge_client und device_protocol fehlten. Der alte
Cloud-Parser verwendete Zahlenfelder 7/8 für Pumpe/Heizung, während frische
Bridge-Daten `ph` enthielten. Nach gesondert freigegebenem HACS-Download von
2.0.11-beta und gemeldetem HA-Core-Neustart zeigt HA `data_source: bridge`,
bridge_age etwa 0,26 s, beide Aktoren aus und 20,5 °C passend zu MySpeidel.
Vollständige Dateiidentität der nun installierten Integration wurde danach nicht
erneut gehasht; Version, Nutzung der Bridge und korrekte Anzeige wurden belegt.

## Lokale Änderung

Neue lokale App-Version **0.3.1-diag.1**. Keine offizielle Upstream-Version.
Der frühere Recorder auf 7f06b29 basierte bereits auf demselben Bridge-App-Code;
kein 0.1.4-Rückport wird übernommen. Die unveränderte 0.3.0 wird als Referenz im
synthetischen Differentialtest mit Recorder aus/an und Fehlerfall verglichen.
Neue .dockerignore schließt Python-Cache aus dem Build-Kontext aus.
Der neue Container-Exporttest deckte außerdem eine bisher ungetestete Lücke auf:
SIGTERM beim Container-Stopp erzeugte keine session_end-Markierung. Ein expliziter
SIGTERM-Handler im Programmeinstieg löst jetzt den vorhandenen Cleanup aus.
Der Wiederholungstest verlangt Exitcode 0 und die tatsächliche Endmarkierung
im exportierten Datensatz. Das ändert die Beendigung, nicht die laufende
Weiterleitung. Erzwungener Abbruch oder Stromverlust bleibt als unsicherer
Dateischluss erkennbar und wird nicht als vollständig ausgegeben.

Produktionsänderung gegenüber 0.3.0: optionales Recorder-Modul, abgeschirmte
Beobachtungspunkte, Diagnose-Health nur bei aktiviertem/fehlgeschlagenem Recorder,
folgende zusätzliche Optionen und eigene Versionsangabe. DNS, Cloud-Weiterleitung,
Rezeptverarbeitung, Header- und Kompressionsverhalten von 0.3.0 bleiben erhalten.
Auch dessen begrenzte Unterstützung gestapelter Kompression wird nicht erweitert.
Kein Integrationscode und kein neues HTTP-Download-/Steuerungsinterface im Paket.

```
diagnostics_enabled: false
diagnostics_max_file_mb: 8
diagnostics_files: 4
```

Alte Optionen werden nicht überschrieben. Fehlen neue Optionen in options.json,
verwendet der Code diese Vorgaben. Deaktiviert: kein Writer, keine Auswertung der
Event-Callbacks, keine Löschung alter Aufzeichnungen. Aktiviert: session/correlation
IDs, UTC/monotone Zeit, rohe Cloud- und ausgehende Bodies als Base64/Latin-1,
vollständige Länge, Cloud/Fallback-Unterscheidung und explizite Ausfall-/Lückenmarker.
Anwendungskörper, kein TCP-Paketmitschnitt; keine Gerätausführungsbestätigung.

Warteschlange: maximal 64 Events und konservativ 16 MiB Schätzung einschließlich
Event in Bearbeitung. Vor Base64/JSON konservative Größenprüfung; ganze Events
verwerfen statt abschneiden. Ein nichtblockierender Lock verhindert Warten des
HTTP-Pfads auf den Writer. Zusätzlicher Serialisierungsspeicher ist begrenzt durch
ein angenommenes Event; vorhandene HTTP- und Dekompressionspuffer sind hiervon
nicht umfasst. Standard-Plattenbudget: höchstens vier Dateien zu 8 MiB. Unpassende
Altdateien blockieren Aufnahme, statt alte Beweise zu löschen oder das Budget zu
vergrößern. Rotation kann den Anfang eines Austauschs verdrängen; Lücken und
Sequenzen prüfen. Kein fsync-/Stromausfall-Dauerhaftigkeitsversprechen.
Graceful-Close begrenzt; fehlende Endmarkierung bedeutet unbestätigten Dateischluss.

## Persistenz und privater Export

Fester Pfad **/data/diagnostics im Bridge-Container**, POSIX 0700/0600.
Nicht mit dem SMB-Quellordner /addons oder addon_configs verwechseln.
Die vorhandene lokale App-Sicherung belegt grundsätzlich /data im Backup;
der neue synthetische Test prüft zusätzlich aktive und rotierte Recorder-Dateien,
Gap-/Endmarker, unveränderte vorhandene synthetische Daten und Hashgleichheit
aller Dateien beim /data-TAR-Roundtrip nach sauberem App-Stopp.

Das ist kein ausgeführter Supervisor-Backup-Test mit installiertem Recorder.
Der reale lokale App-Backup-Export muss nach gesonderter Installation zunächst
mit einer begrenzten Aufnahme auf HA geprüft werden. Vorgehen: Aufnahme beenden,
Bridge kontrolliert stoppen, nur die Bridge lokal sichern, privat herunterladen,
Dateimenge/Hashes/JSONL-Sequenzen und session_end prüfen. Ein Backup während
aktiver Rotation kann Dateien aus unterschiedlichen Momenten enthalten. Ein
Neustart mit weiter aktivierter Aufnahme erzeugt eine weitere Sitzung; deren
Abgrenzung dokumentieren. Details des Stop-/Backup-/Wiederanlaufablaufs anhand
der vorhandenen UI bestätigen, bevor Live-Aufzeichnung beginnt.

Die früher erstellte Sicherung enthält zusätzlich HA/SSL; nicht öffentlich teilen.
Spätere Exporte ausschließlich Bridge und Speicherort **Dieses System** auswählen.
Automatische Backups an weitere Ziele können Recorder-Daten mitnehmen. Vor
Aktivierung deren Bridge-Auswahl/Aufbewahrung prüfen und private Behandlung mit
dem Eigentümer abstimmen. Keine Dateien nach www, kein neuer HTTP-Endpunkt,
keine Zugangsdaten oder Browser-Sitzungen übernehmen.

## Voraussetzungen einer späteren Installation

1. Neue lokale Sicherung der **jetzt bestätigten Bridge 0.3.0 und Integration
   2.0.11-beta** samt aktuellem /data/Optionen erstellen und privat exportieren.
   Die vorhandene 0.1.4-Sicherung ist historischer Rückweg und darf nicht als
   Sicherung der inzwischen bestätigten 0.3.0 ausgegeben werden.
2. Quellstand und aktive Optionen erneut lesen, Hash mit Basis vergleichen.
   App-Quellordner /addons/braumeister_bridge und Slug local_braumeister_bridge
   sind aus der bisherigen Installation belegt. Im letzten Screenshot waren
   automatische Bridge-Updates eingeschaltet: **vor Quellenübertragung nach
   Freigabe ausschalten**, damit schon das Kopieren der neuen Versionsdatei kein
   unbeabsichtigtes Update auslöst. In dieser lokalen Phase nichts übertragen.
3. Eigentümer gibt konkretes Recorder-Deployment und Bridge-Unterbrechung frei;
   kein aktiver Sud. Erst danach ausschließlich das App-Paket übertragen und
   die bestehende lokale App über ihren Supervisor-Updateweg aktualisieren.
   Integration, HACS-Auswahl, DNS und sonstige Komponenten unverändert lassen.
4. Erster Lauf **diagnostics_enabled=false**. Version, Health, alte Optionen,
   erhaltene Daten, frische Bridge-/Cloud-Nachrichten und HA-Anzeige prüfen.
   Recorder-Aktivierung und notwendiger Bridge-Neustart gesondert abstimmen.
5. B00: zunächst **60 Sekunden passiv**, ohne Portal-/Gerätebedienung,
   unveränderte Pollingintervalle. Nutzer bedient Chrome selbst. Keine automatischen
   Heizungs-/Pumpenbefehle, Rezepteingriffe, Replays oder Fuzzing. Erst nach
   Auswertung spätere einzelne Bedienaktionen gemeinsam abstimmen.

## Rückweg und erhaltene Arbeit

Für ein späteres Recorder-Deployment ist der unmittelbare Rückweg die dann neu
gesicherte Bridge 0.3.0: Quellen zurückspielen und ausschließlich App-Backup samt
Image/Optionen/Daten wiederherstellen. Integration 2.0.11-beta beibehalten.
Die Wiederherstellung bleibt ungetestet, solange kein solcher Test erfolgt ist.
Keine komplette HA-/SSL-Wiederherstellung vorsehen. Diagnose aus stoppt künftige
Aufnahme, ersetzt aber keine Quell-/Image-Rückkehr. Alte Exporte privat erhalten.

0.1.4-Quell-/Image-Sicherung und Integrationssicherung 2.0.3 sind erhalten.
Der pausierte Worktree protocol-analysis / codex/bridge-014-diagnostics einschließlich
uncommitteter Änderungen und neuer Tests bleibt unangetastet. Frühe Commits
c12a91f, 8f42422, 7f06b29 bleiben erhalten. Diese Vorbereitung liegt separat in
bridge-030-recorder / codex/bridge-030-recorder. Kein Push/Release/PR.
