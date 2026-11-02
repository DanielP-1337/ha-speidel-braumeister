# Lokale Prüfung des regulären Bridge-Updates, 02.11.2026

App-Basis: unverändert `796d3a9fe7eccca8af5fc21c98b56e8f5cd4bf21`, Version 0.3.0.
Die neuen Dateien dieses Folgecommits sind ausschließlich Tests und Dokumentation.
Kein Diagnose-Recorder, keine Änderungen an Bridge-Produktionscode oder Integration.

## Aktuelle Ergebnisse

- `pytest -q tests/test_bridge.py tests/test_cloud_dns.py`: **25 passed**, 3.00 s.
- `pytest -q tests/test_bridge_options_migration.py`: **1 passed**, 0.11 s.
- Ruff für App-Code, Bridge-/DNS-Tests und die neuen Tests: bestanden.
- `git diff --check`: bestanden; App-Verzeichnis gegenüber Basis ohne Git-Diff.
- Insgesamt **26 gezielte Tests**, kein erneut ausgeführter vollständiger
  Integrationstestlauf. Frühere Zahlen 208/261 bzw. 224/1/261 gehören anderen
  Prüfständen und werden hier nicht als neue Resultate verwendet.

Build:
```
docker --context desktop-linux build --platform linux/arm64 --build-arg BUILD_FROM=ghcr.io/home-assistant/aarch64-base:3.24 --tag braumeister-base:0.3.0-796d3a9-20261102 braumeister_bridge
```

Docker Engine: linux/amd64, 29.7.2. Buildziel linux/arm64; Testlauf meldet aarch64,
also ARM64 unter Emulation. Kein Raspberry-Pi-/Supervisor-Hardwaretest.
Der erste Docker-Zugriff innerhalb der Sandbox scheiterte an der Named-Pipe-
Berechtigung; außerhalb der Sandbox funktionierte der explizite Kontext.

Basisdigest:
`sha256:4925dc4a4e3c23a3a27e6936929ad33afb4d255027944a6054edff7e179f47b7`.
Testimage-ID:
`sha256:34df733538be24dd79a0bd5a39b427a3573685f776dc1e7d834008a5dba17b0e`.
Im getesteten Image enthaltene bridge.py:
`59b8151dd3128ac831a11d885c53491a5f84ad15a17c990d89646a34b43b4371`.
Das Auslieferungs-ZIP mit Suffix `-tested` übernimmt genau diese Checkout-Bytes
(Windows-CRLF); gegen Git-Blobs mit normalisierten Zeilenenden geprüft.

Buildwarnung `InvalidDefaultArgInFrom`: Dockerfile hat absichtlich kein Default
für BUILD_FROM; das benötigte Argument wurde korrekt gesetzt. Build erfolgreich.
Das Upstream-Build ist nicht vollständig reproduzierbar gepinnt: Basis-Tag und
APK-Pakete sind beweglich. Supervisor baut später selbst auf dem Pi; dessen
Image-Digest kann abweichen und ist nach Installation zu protokollieren.

Container-Smoke-Test (`tests/container_smoke_base.py`):

- Genau 11 synthetische HTTP-Austausche über ein verifiziert internes Netz.
- Keine Host-Portfreigaben, Bind-Mounts, Docker-Socket oder produktiven Optionen.
  Ausschließlich eigene beschriftete Container, internes Netz und Testvolume.
- Start des echten `/app/bridge.py` mit synthetischer Konfiguration.
- Plain/Binär, gzip, zlib-deflate, raw-deflate, leerer Body, Cloud-503,
  ungültiges gzip, gestapelte Codierung und abgebrochene Cloud-Verbindung.
- Status/Bodies geprüft; Cloud-503 bleibt Cloud-Antwort, Transport-/Decodefehler
  führen zur vorhandenen lokalen Antwort. Quellenkennzeichnung über Status-API
  für frische synthetische Nachrichten geprüft.
- Dokumentierte Unterschiede bestätigt: fremde Antwortheader entfallen;
  gestapeltes gzip/deflate führt zu lokalem Fallback.
- Rezeptliste bleibt nach Container-Neustart im eigenen Testvolume erhalten.
  Recorder-Dateien und Diagnose-Health-Felder sind nicht vorhanden.
- Erstlauf: HTTP-Tests bestanden, Restart-Prüfung nach fixer 1 s traf einen
  noch nicht offenen Port. Testharness korrigiert: begrenztes Warten auf lokale
  Bereitschaft. Wiederholung vollständig erfolgreich; App-Code unverändert.
- Alle eigenen Testcontainer, das Testvolume und das Testnetz in beiden Läufen
  gezielt entfernt; kein Prune, keine fremden Ressourcen verändert.
- Testimage bleibt lokal als Prüfartefakt, gesichertes Image 0.1.4 nicht geladen,
  gestartet oder überschrieben.

## Erhaltene pausierte Arbeit

Worktree `protocol-analysis`, Branch `codex/bridge-014-diagnostics`, weiterhin mit
seinen uncommitteten Änderungen; frühere Commits c12a91f, 8f42422, 7f06b29 erhalten.
Zusätzliche Kopie des getrackten Diffs unter
`bridge-014-preparation-20261102/paused-tracked-work.patch` neben dem Worktree.
Ungetrackte neue Tests bleiben ebenfalls im Worktree erhalten.
Die bereits laufenden Rückporttests endeten mit **248 passed, 1 skipped,
261 subtests**; dies ist kein Ergebnis des regulären 0.3.0-Pakets.
Der hängende ältere Sandbox-Testlauf wurde anhand seiner Prozess-IDs beendet.
Das lokale Rückport-Image ist erhalten, aber nicht zur Installation freigegeben.

## Grenzen

Kein neuer Live-Datenfluss bestätigt, kein MySpeidel-Zugriff, keine Gerätebefehle,
kein Deployment und keine Wiederherstellung ausgeführt. Optionsübernahme im
App-Code geprüft, tatsächlicher Supervisor-Updateablauf noch nicht ausgeführt.
Backup-Inhalte lesbar und gehasht; Rückrollfähigkeit durch Wiederherstellung
weiterhin ungetestet. Aktuelle GitHub-Main-/Release-Metadaten wurden gelesen;
keine Veröffentlichung, kein Push und kein PR erstellt.
