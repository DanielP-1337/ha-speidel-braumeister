# Bridge 0.3.0: lokaler Update-Plan, 2. November 2026

Status: Vorbereitung zur Deployment-Freigabe. Keine HA-Änderung ausgeführt.
Der 0.1.4-Diagnose-Rückport ist pausiert. Dieses Paket enthält keinen Recorder.

## Versionen und Empfehlung

- Upstream-GitHub-Release `v3.0.0`, veröffentlicht 31.10.2026, ist das
  Integrationsrelease am Commit `d619f74ad9d4e77ab586c17e95e70fed31541fad`.
  Sein App-Verzeichnis enthält Bridge **0.2.0**, nicht 0.3.0.
- Bridge **0.3.0** steht seit `796d3a9fe7eccca8af5fc21c98b56e8f5cd4bf21`
  im öffentlichen Upstream-App-Verzeichnis mit Changelog und Versionsangabe.
  Kein separates GitHub-Release/Tag für Bridge 0.3.0 wurde gefunden.
  Dies ist ein über das Repository angebotener App-Stand, kein eigener
  GitHub-Release. Die Version allein fixiert den Quellstand nicht.
- Upstream-main bei Prüfung: `7a2f6fd724f03c48da7ae406609edbf9d788d382`.
  PR #15 ist über `fc8538aea6b206ce5ee3f1137146cb80bd1d0ab1` gemergt.
  Die RTC-Änderungen betreffen Integration und Tests; das Bridge-Verzeichnis
  ist gegenüber dem empfohlenen Commit unverändert (Git-Tree
  `5376d31ac5f85dc7cd34ff2b13d4ce4efdfe2ba3`). Ein Merge ist kein neues Release.
- Fork-Integrations-Prerelease `2.0.11-beta` verweist auf
  `214d557499116af25348f5f5cd0176e8ed472ee4` und enthält Bridge **0.1.4**.
  Fork-Branch `feat/local-bridge-adguard` enthält ebenfalls 0.1.4.
  Fork-main `2bcfc86bd686118f88fdde1cf70ca1ee95644cda` hat kein Bridge-Verzeichnis.
- Lokales `0.1.5-diag.1` ist ausschließlich die pausierte Diagnose-Arbeit;
  nicht veröffentlicht, nicht installiert und nicht Teil dieses Updates.

Empfehlung: unveränderte Upstream-Bridge **0.3.0**, gepinnt auf **796d3a9**,
als kontrolliertes Basisupdate in der bestehenden lokalen App. Sie unterstützt
die vorhandene externe DNS-Umschreibung und explizite Cloud-Resolver. Die ältere
Bridge 0.2.0 aus dem Integrationsrelease enthält diese Cloud-DNS-Isolation nicht
und ist deshalb für diesen Aufbau kein geeigneter Ersatz. Die Integration
**2.0.11-beta bleibt unverändert**. Diese Empfehlung behauptet keine vollständige
Protokollgleichheit zur angepassten 0.1.4; die folgenden Unterschiede gehören
ausdrücklich zur Freigabeentscheidung.

## Vergleich mit dem gesicherten Image 0.1.4

Image-Layer in Manifest-Reihenfolge ausgewertet, Whiteouts und opake Verzeichnisse
vor den Ergänzungen desselben Layers berücksichtigt; Layer-Digests geprüft.
Die resultierende `/app/bridge.py` ist bytegleich zur separaten Quellsicherung:
SHA256 `17a76ef3f9ae3ebe0ec76d1b89a330dc4ecb78ee2a5c8bdbd140dbaf516ce435`.
Keine HA-Daten, SSL-Dateien oder produktiven Optionen ins Repository übernommen.

| Bereich | Gesicherte 0.1.4 → Upstream 0.3.0 |
|---|---|
| DNS-Vorgaben | `dns_port: 0` → `53`; Cloudflare-Liste → `[]` (Host-Resolver). Bestehende explizite Werte müssen erhalten bleiben. |
| Cloud-DNS | Öffentliche Zieladressen weiterhin erzwungen. Zusätzlich Host-Resolver erlaubt, wenn Liste leer. Mit erhaltener Liste bleibt explizite Auflösung aktiv. |
| Weiterleitung | Methode, URL, Body, keine Redirects, HTTP-Status und lokale Ersatzantwort bleiben grundsätzlich gleich; unten genannte Unterschiede beachten. |
| Rezepte | Neu: Speicherung eingehender Rezeptlisten in `/data/recipes.json`, Wiederherstellung beim Start, Schreiben nur bei Rezeptänderung. Kein Rezeptbefehl wird dadurch erzeugt. |
| Antwortheader | 0.1.4 übernimmt Nicht-Hop-by-hop-Header (bei Dekodierung bereinigt). 0.3.0 übernimmt nur `Content-Type`; z.B. ETag, Retry-After und eigene Cloud-Header entfallen. |
| Kompression | Beide unterstützen gzip/x-gzip und zlib/raw-deflate. 0.1.4 dekodiert gestapelte Codierungen; 0.3.0 behandelt `gzip, deflate` als Fehler und antwortet lokal. |
| Request-Encoding | 0.1.4 entfernt vorhandene Accept-Encoding-Schreibweisen vor `identity`; 0.3.0 setzt `identity` ohne diese explizite Bereinigung. Tatsächliche Legacy-Geräteheader sind noch nicht frisch belegt. |
| Passthrough | 0.3.0 fordert `identity` an, wenn kein Accept-Encoding vorliegt. Aktuell ist Passthrough leer. |
| Logs | Zusätzliche Protokollierung empfangener Cloud-Kommandos bei INFO sowie Dauer/Antwortanfang bei DEBUG; gewöhnliche Logs privat behandeln. |
| Status-API | `/api/status` und Quellenkennzeichnung bleiben verfügbar. Rezeptdaten können nach Neustart vorhanden sein, ohne frischen Geräteverkehr zu belegen. |

Stacked-Encoding-Fallback und Header-Reduktion sind bestätigte Eigenschaften des
unveränderten Upstream-Codes, nicht stillschweigend repariert. Falls die reale
Cloud diesen Sonderfall nutzt oder die Baseline unerwartete Fallbacks zeigt:
abbrechen/rückrollen und eine separate Kompatibilitätskorrektur prüfen.

## Installation nach gesonderter Freigabe

Bestätigte Ziel-App: `local_braumeister_bridge`, Quelle `local`, `build: true`,
Host-Netzwerk; HA meldet `aarch64` / `raspberrypi5-64`.
Bestätigter Quellordner im Terminal: `/addons/braumeister_bridge`.
Bestätigter SMB-Pfad: `\\homeassistant.local\addons\braumeister_bridge`.

1. Braumeister bleibt aus, kein aktiver Sud. Backup und Quellarchiv lokal behalten.
   Bestehende aktive Optionen erneut mit der bereits gelieferten Liste vergleichen.
   Insbesondere **dns_port=0**, **cloud_dns=[1.1.1.1,1.0.0.1]**,
   forward_to_cloud=true, cloud_host=api2.myspeidel.com, http_port=80,
   api_port=8642, leere bridge_ip/upstream_dns/passthrough_url und log_level=info.
   Nicht auf Standardwerte zurücksetzen. Keine Diagnoseoption hinzufügen.
2. Paket `Braumeister-Bridge-0.3.0-796d3a9-tested.zip` lokal entpacken und
   SHA256 anhand SHA256SUMS.txt prüfen. Es enthält nur das App-Verzeichnis.
   Nach Freigabe dessen Dateien in den bestätigten SMB-Quellordner kopieren,
   ohne einen zweiten verschachtelten `braumeister_bridge`-Ordner anzulegen.
   Keine Integration kopieren, keine App deinstallieren, keine Datenordner löschen.
   Der pausierte Diagnosecode darf nicht in diesen Quellordner gelangen.
3. Im HA-App-Store über das Menü nach Updates suchen/Store neu laden.
   Auf der bestehenden lokalen Bridge-App muss nun installierte Version 0.1.4
   und verfügbare Version 0.3.0 erscheinen. Falls nicht: anhalten und Ansicht prüfen.
   Kein geratenes CLI-Updatekommando verwenden.
4. Auf genau dieser bestehenden App **Aktualisieren** ausführen. Kein Wechsel auf
   eine zweite Repository-App (anderer Slug). Supervisor baut wegen fehlendem
   `image:` und `build: true` lokal aus Dockerfile und build.yaml für aarch64;
   `BUILD_FROM=ghcr.io/home-assistant/aarch64-base:3.24` wird ausgewählt.
   Diese Dateien sind unverändert Upstream. Der lokale Docker-Test ersetzt nicht
   den Build durch den installierten Supervisor. Image-Bezeichnung und genaue
   Builddauer auf HA werden erst dabei bestätigt. Eine Bridge-Unterbrechung ist
   nötig; HA-Core-Neustart und DNS-Umstellung sind nicht vorgesehen.
5. Update der gleichen App behält Optionen und das persistente `/data`.
   Nach dem Update aktive Optionen vollständig vergleichen, Version/Startlogs
   und rein lokale `/api/health` prüfen. Keine fehlenden Daten aus Rezeptcache
   als frische Kommunikation interpretieren. Bei Schemafehler oder geänderten
   DNS-Werten nicht den Braumeister einschalten.

Der App-Code lädt zuerst Vorgaben und überlagert sie mit vorhandenen Optionen.
Alle bisherigen Optionsnamen werden vom 0.3.0-Schema akzeptiert, auch dns_port=0.
Es gibt kein Migrationsskript, das absichtlich alte Werte ersetzen sollte.
Der zusätzliche lokale Test prüft diese Überlagerung. Die tatsächliche
Supervisor-Migration bleibt bis zum HA-Update unbestätigt; deshalb Kontrolle
unmittelbar davor und danach, keine pauschale Übernahme neuer Vorgaben.

## Basisprüfung nach Installation, vor Diagnosearbeit

Erst nach erfolgreicher Start-/Optionsprüfung und gemeinsamer Abstimmung den
Braumeister einschalten. Keine Heiz-/Pumpenaktion, Rezepteingabe oder Cloud-Replays.
Zunächst 60 Sekunden passiv beobachten, vorhandene Pollingintervalle unverändert.
Keine Recorder-Aufnahme in dieser Phase.

- Frische, fortschreitende Empfangszeitstempel in lokalem `/api/status` nachweisen.
  Vorhandener Cache und `last_response_source: cloud` allein reichen nicht.
- Für neue Nachrichten `last_response_source: cloud` und keine wiederholten
  Forwarding-/DNS-/Dekodierfehler nachweisen; Cloud-HTTP-Fehler und lokale
  Ersatzantwort sind zu unterscheiden. Keine zusätzlichen aktiven Cloud-Probes.
- HA-Zustände und Aktualisierung manuell prüfen. Die Integration bleibt 2.0.11-beta.
- Nutzer meldet sich selbst in Chrome bei MySpeidel an und prüft Status/Frische.
  Keine Browser-Automation und keine Übergabe von Sitzungen oder Zugangsdaten.
- Ergebnisse mit Uhrzeit protokollieren. Erst bei erfolgreicher Basisprüfung
  den vorhandenen Diagnose-Patch an genau diesen Stand anpassen und neu freigeben.

## Rückweg (gesichert, Wiederherstellung weiterhin ungetestet)

Backup `Braumeister-0.1.4-vor-Diagnose`, ID `af37faa1`, 02.11.2026 10:13 Berlin.
Lokale Kopie:
`<LOCAL_BACKUP_DIR>/braumeister_0_1_4_vor_diagnose.tar`
SHA256 `0b1a5406227e6e0554010e02b0631e892b3d2c46ce3d9e98dac634726b9ccb46`.
Enthält Bridge-Image `local/aarch64-addon-braumeister_bridge:0.1.4`, ARM64,
App-Metadaten und damaliges `/data/options.json`. Der vollständige Download
enthält zusätzlich HA-Daten und SSL und ist entschlüsselt: lokal behalten.

Quellsicherung:
`<LOCAL_BACKUP_DIR>/bridge-0.1.4.tar.gz`
SHA256 `bdca0c1f4e423e874333209b431f80e1071503fab7533b1d03621c0fe296106d`.

Bei Startfehler, ungewollter Optionsänderung, fehlendem frischen Empfang oder
unerwarteter lokaler Ersatzantwort: keinen weiteren Geräteversuch durchführen.
Wenn sicher, Braumeister ausschalten; nur Bridge stoppen. Gesicherten
0.1.4-Quellordner über denselben SMB-Pfad wiederherstellen (vorher aktuellen
Quellstand separat behalten). Store neu laden, damit 0.3.0 nicht erneut angeboten
wird. Im vorhandenen Backup **ausschließlich Braumeister Bridge (0.1.4)** für
Wiederherstellung auswählen, HA-Einstellungen/Verlauf und SSL abgewählt lassen.
Falls das HA-Backup nicht mehr lokal vorhanden ist, die lokale TAR-Kopie über die
Backup-Oberfläche importieren. Wiederherstellung des App-Backups stellt dessen
gesichertes Image und Optionen/Daten wieder her; nicht allein alte Quellen
kopieren und behaupten, damit sei der laufende Container zurückgesetzt.
Danach Version 0.1.4, Optionen, Start und vereinbarte passive Datenflussprüfung
kontrollieren. Quellrestaurierung verhindert ein versehentliches späteres
Neubauen aus 0.3.0. DNS-Setup und Integration bleiben unverändert.

## Export und offene Grenzen

Kein Recorder in diesem Paket, daher kein neuer Diagnoseexport.
Das vorhandene Backup bestätigt bereits die Sicherung des App-/data und Images.
Ein späterer Recorder würde `/data/diagnostics` nutzen. Ein nur lokales App-Backup
ist dafür vorgesehen; vollständige neue Recorder-Dateien, Rotation und
Abschlussmarkierung müssen erst in jener Phase mit synthetischem Export und
anschließender HA-Kontrolle überprüft werden. Dies ist noch kein solcher Nachweis.
Bei späteren Diagnosen automatische externe Backups berücksichtigen: zusätzliche
App-Daten könnten darin enthalten sein; private Export-/Aufbewahrungspolitik
vor Aktivierung abstimmen.

Quellen (am 02.11.2026 gelesen):
- https://github.com/omphteliba/ha-speidel-braumeister/releases/tag/v3.0.0
- https://github.com/omphteliba/ha-speidel-braumeister/commit/796d3a9fe7eccca8af5fc21c98b56e8f5cd4bf21
- https://github.com/omphteliba/ha-speidel-braumeister/compare/01ac674f4cb35fa04e05708de52b944aebeeadc7...7a2f6fd724f03c48da7ae406609edbf9d788d382
- https://github.com/DanielP-1337/ha-speidel-braumeister/releases/tag/2.0.11-beta
- https://contributors.home-assistant.io/apps/how-apps-work/
- https://contributors.home-assistant.io/apps/supervisor-api/store/
